from __future__ import annotations

import logging
import threading
from typing import Any

from app.core.config import settings


logger = logging.getLogger(__name__)


def _ensure_cuda_execution_provider(manager: Any) -> None:
    """Register the CUDA execution provider before the catalog is ever touched.

    Root cause (verified on this project's own GPU, foundry-local-sdk-winml
    1.2.4): ``FoundryLocalManager.initialize()`` does not register any
    execution provider by itself. ``Catalog._update_models`` caches the
    result of its first ``get_model_list`` call for 6 hours, and that first
    result only includes variants compatible with EPs registered *at that
    moment*. If CUDA isn't registered yet, every alias resolves to CPU-only
    variants for the rest of the process -- even for a model whose CUDA
    variant is already downloaded and cached on disk. Registering CUDA here,
    strictly before ``manager.catalog`` is accessed anywhere, is what makes
    the catalog show (and default-select) the cuda-gpu variant.

    This project targets CUDA specifically, so a missing/failed CUDA EP is a
    hard failure here rather than a silent CPU fallback: CPU-only phi-4-mini
    inference has been measured at 84+ seconds to the first streamed token,
    which is not viable for this assistant.
    """
    eps = manager.discover_eps()
    cuda_ep = next((ep for ep in eps if ep.name == "CUDAExecutionProvider"), None)

    if cuda_ep is None:
        raise RuntimeError(
            "CUDAExecutionProvider Foundry Local tarafından keşfedilemedi. "
            "NVIDIA sürücüsünü ve Foundry Local kurulumunu kontrol edin."
        )

    if cuda_ep.is_registered:
        logger.info("CUDA Execution Provider already registered.")
        return

    logger.info("Registering CUDA Execution Provider...")
    result = manager.download_and_register_eps(["CUDAExecutionProvider"])

    if not result.success or "CUDAExecutionProvider" not in result.registered_eps:
        raise RuntimeError(
            "CUDA Execution Provider kaydı başarısız oldu: "
            f"status={result.status!r} failed_eps={result.failed_eps!r}"
        )

    eps_after = manager.discover_eps()
    cuda_after = next(
        (ep for ep in eps_after if ep.name == "CUDAExecutionProvider"), None
    )
    if cuda_after is None or not cuda_after.is_registered:
        raise RuntimeError(
            "CUDA Execution Provider kaydı tamamlandı bildirildi ancak "
            "discover_eps() hâlâ registered=False gösteriyor."
        )

    logger.info("CUDA Execution Provider registration completed.")


def _is_gpu_variant(variant: Any) -> bool:
    runtime = getattr(getattr(variant, "info", None), "runtime", None)
    device_type = getattr(runtime, "device_type", None)
    return str(device_type).upper() == "GPU"


def _select_cached_variant_if_available(model: Any) -> None:
    """Pick the best already-cached variant for ``model``, preferring GPU.

    Priority: cached GPU variant > currently-selected variant (if it's
    cached) > any other cached variant > leave the normal SDK
    download()/load() path untouched.

    Two distinct problems this fixes, both observed on this project's real
    device against foundry-local-sdk-winml 1.2.4:

    1. Stale/wrong selection (original bug): ``Model._add_variant`` prefers a
       cached variant over an uncached one when variants are added one at a
       time, but ``Model._refresh_variants`` -- used when
       ``Catalog.get_model()`` goes through a catalog refresh -- replaces the
       whole variant list without re-running that preference check. The
       previously selected variant can end up being one whose files were
       never downloaded, and ``model.load()`` then fails fast with "Model
       path does not exist" instead of loading the variant that is really on
       disk.

    2. CPU-over-GPU default (this revision): once CUDA is registered as an
       execution provider (see ``_ensure_cuda_execution_provider``), a
       model's variant list can contain *both* a cached CPU variant and a
       cached GPU variant. The SDK's own default selection (``Model.__init__``:
       "the first variant Core lists is the default") is not GPU-aware, and
       was observed picking the cached CPU variant in production even though
       a cached CUDA variant existed. A cached GPU variant must win in that
       case rather than being left unused because "the current selection is
       already cached" (which is what a naive early-return would do).

    This only ever inspects ``model.variants`` and ``model.id``/each
    variant's live ``is_cached`` state, so it is alias-agnostic: it applies
    the same way to any chat model or the embedding model, with no
    per-model-name or per-variant-id-substring branching.

    Note on IPC cost: each variant's ``is_cached`` is a live daemon call
    (``ModelVariant.is_cached`` -> ``get_cached_model_ids``). To correctly
    prefer a cached GPU variant even when the current selection is *already*
    cached, this function can no longer short-circuit on ``model.is_cached``
    alone the way the original version did -- it must inspect every
    variant's cache status once. Each variant is still only ever queried
    once (never re-queried, including for whichever variant is currently
    selected), and this whole function only runs once per alias per process
    (``FoundryProvider.get_loaded_model`` caches the result), so the extra
    calls are a handful of IPC round-trips one time, not a per-request cost.
    """
    variants = getattr(model, "variants", None)
    if not variants:
        # Single-variant wrapper (e.g. Catalog.get_model_variant) or a model
        # object that doesn't expose variants -- nothing to select between.
        return

    selected_id = getattr(model, "id", None)

    # Single pass: read each variant's is_cached exactly once and remember
    # it, instead of re-querying the same variant later.
    cache_status: list[tuple[Any, bool]] = [
        (variant, bool(getattr(variant, "is_cached", False))) for variant in variants
    ]

    cached_gpu = next(
        (variant for variant, cached in cache_status if cached and _is_gpu_variant(variant)),
        None,
    )
    selected_variant, selected_is_cached = next(
        (
            (variant, cached)
            for variant, cached in cache_status
            if getattr(variant, "id", None) == selected_id
        ),
        (None, False),
    )

    if cached_gpu is not None:
        if selected_variant is cached_gpu:
            # Already selected -- nothing to do.
            return
        target = cached_gpu
        select_reason = "gpu"
    elif selected_is_cached:
        # No cached GPU variant exists; the current selection is already
        # cached, so respect it instead of second-guessing a selection that
        # works.
        return
    else:
        cached_variants = [variant for variant, cached in cache_status if cached]
        if not cached_variants:
            # Truly nothing cached for this alias yet -- this is a normal
            # "needs downloading" case, not the stale-selection bug. Leave
            # model.download()/model.load() to run their usual path
            # untouched.
            return
        target = cached_variants[0]
        select_reason = "fallback"

    try:
        model.select_variant(target)
    except Exception as exc:
        raise RuntimeError(
            f"'{getattr(model, 'alias', '?')}' icin cache'li varyant "
            f"(id={getattr(target, 'id', '?')}) secilemedi: {exc}"
        ) from exc

    if select_reason == "gpu":
        logger.info("Selecting cached GPU variant: %s", getattr(target, "id", "?"))


class FoundryProvider:
    """Lazy singleton wrapper around Microsoft Foundry Local SDK.

    Models are loaded once and reused across requests. `model.download()` is only
    attempted when AUTO_DOWNLOAD_MODELS=true and the model is not cached.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._manager: Any | None = None
        self._models: dict[str, Any] = {}

    def _get_manager(self) -> Any:
        with self._lock:
            if self._manager is not None:
                return self._manager

            try:
                from foundry_local_sdk import Configuration, FoundryLocalManager
            except ImportError as exc:
                raise RuntimeError(
                    "Microsoft Foundry Local SDK kurulu değil. "
                    "Windows için 'pip install foundry-local-sdk-winml', "
                    "diğer platformlar için 'pip install foundry-local-sdk' kullanın."
                ) from exc

            FoundryLocalManager.initialize(
                Configuration(
                    app_name=settings.app_name,
                    model_cache_dir=str(settings.foundry_model_cache_dir),
                )
            )
            manager = FoundryLocalManager.instance

            # Must happen before any manager.catalog access anywhere (see
            # _ensure_cuda_execution_provider's docstring). Runs exactly once
            # per process: this whole method only reaches here the first
            # time it's called (the early-return above short-circuits every
            # call after), and the surrounding `self._lock` already
            # serializes concurrent callers, so two threads can't race into
            # registering CUDA twice.
            _ensure_cuda_execution_provider(manager)

            self._manager = manager
            return self._manager

    def get_loaded_model(self, alias: str) -> Any:
        with self._lock:
            existing = self._models.get(alias)
            if existing is not None:
                return existing

            manager = self._get_manager()
            model = manager.catalog.get_model(alias)
            _select_cached_variant_if_available(model)

            resolved_runtime = getattr(getattr(model, "info", None), "runtime", None)
            logger.info(
                "'%s' resolved to variant %s (device=%s)",
                alias,
                getattr(model, "id", "?"),
                getattr(resolved_runtime, "device_type", "?"),
            )

            is_cached = bool(getattr(model, "is_cached", False))
            if not is_cached:
                if not settings.auto_download_models:
                    raise RuntimeError(
                        f"'{alias}' modeli cihazda önbelleğe alınmamış. "
                        "İnternete bağlıyken scripts/prepare_models.py çalıştırın "
                        "veya AUTO_DOWNLOAD_MODELS=true kullanın."
                    )
                model.download()

            if not bool(getattr(model, "is_loaded", False)):
                model.load()

            self._models[alias] = model
            return model

    def unload_model(self, alias: str) -> bool:
        """Best-effort unload of a single cached model, leaving every other
        alias untouched.

        Used for GPU model swapping between the chat and embedding models
        (RAG query lifecycle), so the two never have to be GPU-resident at
        the same time. Returns True if ``alias`` is confirmed not resident
        afterwards (either it wasn't loaded to begin with, or the unload
        just succeeded), False if an unload was attempted and failed. A
        caller about to load a *different* model onto the same GPU must
        treat False as "do not proceed" -- loading a second model while
        this one is still resident is exactly the CUDA OOM / native-process-
        crash scenario this method exists to prevent. The failure itself is
        logged and swallowed rather than raised here: raising is the
        swap-orchestrator's call to make (it knows whether proceeding is
        actually unsafe), not this best-effort primitive's.
        """
        with self._lock:
            model = self._models.get(alias)
            if model is None:
                return True

            try:
                if bool(getattr(model, "is_loaded", True)):
                    model.unload()
            except Exception:
                logger.warning(
                    "'%s' modeli unload edilirken hata oluştu; model resident "
                    "kalmaya devam edecek.",
                    alias,
                    exc_info=True,
                )
                return False

            del self._models[alias]
            return True

    def unload_all(self) -> None:
        with self._lock:
            for model in self._models.values():
                try:
                    if bool(getattr(model, "is_loaded", True)):
                        model.unload()
                except Exception:
                    pass
            self._models.clear()


foundry_provider = FoundryProvider()
