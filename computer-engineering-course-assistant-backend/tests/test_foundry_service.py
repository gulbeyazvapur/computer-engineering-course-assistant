from __future__ import annotations

import pytest

from app.core.config import settings
from app.services import foundry_service
from app.services.foundry_service import (
    FoundryProvider,
    _ensure_cuda_execution_provider,
    _select_cached_variant_if_available,
)


class _FakeRuntime:
    def __init__(self, device_type):
        self.device_type = device_type


class _FakeInfo:
    def __init__(self, device_type):
        self.runtime = _FakeRuntime(device_type)


class _FakeVariant:
    def __init__(self, id_, cached, device_type="CPU"):
        self.id = id_
        self._cached = cached
        self.info = _FakeInfo(device_type)

    @property
    def is_cached(self):
        return self._cached


class _FakeModel:
    def __init__(self, alias, variants, selected_index=0):
        self.alias = alias
        self.variants = variants
        self._selected = variants[selected_index]
        self.select_variant_calls: list = []

    @property
    def id(self):
        return self._selected.id

    @property
    def is_cached(self):
        return self._selected.is_cached

    @property
    def is_loaded(self):
        return False

    def select_variant(self, variant):
        self.select_variant_calls.append(variant)
        self._selected = variant


def test_switches_to_cached_variant_when_selected_is_not_cached():
    """A. Selected variant not cached, a different variant is cached -> switch."""
    cpu = _FakeVariant("phi-4-mini-generic-cpu:5", cached=False, device_type="CPU")
    gpu = _FakeVariant("phi-4-mini-cuda-gpu:5", cached=True, device_type="GPU")
    model = _FakeModel("phi-4-mini", [cpu, gpu], selected_index=0)

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == [gpu]
    assert model._selected is gpu


def test_prefers_gpu_among_multiple_cached_variants():
    cpu_uncached = _FakeVariant("m-cpu:1", cached=False, device_type="CPU")
    cpu_cached = _FakeVariant("m-cpu:2", cached=True, device_type="CPU")
    gpu_cached = _FakeVariant("m-gpu:1", cached=True, device_type="GPU")
    model = _FakeModel(
        "some-model", [cpu_uncached, cpu_cached, gpu_cached], selected_index=0
    )

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == [gpu_cached]


def test_prefers_cached_gpu_even_when_selected_cpu_is_already_cached():
    """1. THE PRODUCTION REGRESSION: after CUDA EP registration, the SDK's own
    default selection landed on an already-cached CPU variant while a cached
    CUDA variant sat unused, because the old "already cached -> do nothing"
    early-return never looked at the other variants. GPU must win here even
    though the selected CPU variant is itself perfectly cached."""
    cpu = _FakeVariant("phi-4-mini-generic-cpu:5", cached=True, device_type="CPU")
    gpu = _FakeVariant("phi-4-mini-cuda-gpu:5", cached=True, device_type="GPU")
    model = _FakeModel("phi-4-mini", [cpu, gpu], selected_index=0)

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == [gpu]
    assert model._selected is gpu


def test_does_not_reselect_when_gpu_already_selected_and_cached():
    """2. Selected variant is already the cached GPU one -> select_variant()
    must not be called again."""
    gpu = _FakeVariant("m-gpu:1", cached=True, device_type="GPU")
    cpu = _FakeVariant("m-cpu:1", cached=False, device_type="CPU")
    model = _FakeModel("some-model", [gpu, cpu], selected_index=0)

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == []
    assert model._selected is gpu


def test_keeps_cached_cpu_selection_when_gpu_variant_is_not_cached():
    """4. Selected CPU is already cached; a GPU variant exists but is NOT
    cached -> keep CPU. An uncached GPU variant must never be selected just
    because it's GPU."""
    cpu = _FakeVariant("m-cpu:1", cached=True, device_type="CPU")
    gpu = _FakeVariant("m-gpu:1", cached=False, device_type="GPU")
    model = _FakeModel("some-model", [cpu, gpu], selected_index=0)

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == []
    assert model._selected is cpu


def test_keeps_selection_when_no_gpu_variant_exists_at_all():
    """5. No GPU variant among the model's variants at all; the selected
    (CPU) variant is already cached -> keep it."""
    cpu1 = _FakeVariant("m-cpu:1", cached=True, device_type="CPU")
    cpu2 = _FakeVariant("m-cpu:2", cached=False, device_type="CPU")
    model = _FakeModel("some-model", [cpu1, cpu2], selected_index=0)

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == []
    assert model._selected is cpu1


def test_falls_back_to_cached_non_gpu_variant_when_no_gpu_cached():
    """6. Selected variant not cached, no cached GPU exists, but another
    cached (non-GPU) variant does -> original cached-fallback behavior is
    preserved."""
    selected_uncached = _FakeVariant("m-cpu:1", cached=False, device_type="CPU")
    other_cached = _FakeVariant("m-cpu:2", cached=True, device_type="CPU")
    model = _FakeModel(
        "some-model", [selected_uncached, other_cached], selected_index=0
    )

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == [other_cached]


def test_generic_behavior_applies_to_embedding_model_too():
    """9. No model-name/id-substring hardcoding: qwen3-embedding-0.6b hits
    the exact same cached-CPU-selected-but-cached-GPU-available fix as
    phi-4-mini, purely via _is_gpu_variant's runtime.device_type check."""
    cpu = _FakeVariant(
        "qwen3-embedding-0.6b-generic-cpu:1", cached=True, device_type="CPU"
    )
    gpu = _FakeVariant(
        "qwen3-embedding-0.6b-cuda-gpu:1", cached=True, device_type="GPU"
    )
    model = _FakeModel("qwen3-embedding-0.6b", [cpu, gpu], selected_index=0)

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == [gpu]
    assert model._selected is gpu


def test_noop_when_selected_variant_already_cached():
    """B. Selected variant already cached -> no redundant re-selection.

    Also covers the embedding-model regression scenario: qwen3-embedding-0.6b
    already resolves to a cached variant today, so this must be a pure no-op.
    """
    gpu = _FakeVariant("qwen3-embedding-cuda-gpu:1", cached=True, device_type="GPU")
    cpu = _FakeVariant("qwen3-embedding-cpu:1", cached=False, device_type="CPU")
    model = _FakeModel("qwen3-embedding-0.6b", [gpu, cpu], selected_index=0)

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == []
    assert model._selected is gpu


def test_noop_when_nothing_is_cached():
    """C. No variant cached at all -> leave normal load()/download() path alone."""
    cpu = _FakeVariant("m-cpu:1", cached=False, device_type="CPU")
    gpu = _FakeVariant("m-gpu:1", cached=False, device_type="GPU")
    model = _FakeModel("some-model", [cpu, gpu], selected_index=0)

    _select_cached_variant_if_available(model)

    assert model.select_variant_calls == []
    assert model._selected is cpu


def test_noop_when_model_exposes_no_variants():
    class _SingleVariantModel:
        alias = "some-model"
        is_cached = False
        variants: list = []

    model = _SingleVariantModel()

    _select_cached_variant_if_available(model)  # must not raise


def test_raises_clear_error_when_select_variant_fails():
    """Point 6: a failed selection must raise immediately, never hang or
    silently fall back."""

    class _BrokenModel(_FakeModel):
        def select_variant(self, variant):
            raise RuntimeError("boom")

    cpu = _FakeVariant("m-cpu:1", cached=False, device_type="CPU")
    gpu = _FakeVariant("m-gpu:1", cached=True, device_type="GPU")
    model = _BrokenModel("some-model", [cpu, gpu], selected_index=0)

    with pytest.raises(RuntimeError, match="secilemedi"):
        _select_cached_variant_if_available(model)


class _FakeEp:
    def __init__(self, name, is_registered):
        self.name = name
        self.is_registered = is_registered


class _FakeEpResult:
    def __init__(self, success, status="", registered_eps=None, failed_eps=None):
        self.success = success
        self.status = status
        self.registered_eps = registered_eps or []
        self.failed_eps = failed_eps or []


class _FakeEpManager:
    """Fake manager exposing only discover_eps()/download_and_register_eps(),
    matching the subset of the real FoundryLocalManager surface that
    _ensure_cuda_execution_provider uses."""

    def __init__(self, initial_eps, register_result=None, eps_after_register=None):
        self._initial_eps = initial_eps
        self._eps_after_register = (
            eps_after_register if eps_after_register is not None else initial_eps
        )
        self._discover_call_count = 0
        self.register_result = register_result
        self.download_and_register_calls: list = []

    def discover_eps(self):
        self._discover_call_count += 1
        if self._discover_call_count == 1:
            return self._initial_eps
        return self._eps_after_register

    def download_and_register_eps(self, names, **kwargs):
        self.download_and_register_calls.append(names)
        return self.register_result


def test_ensure_cuda_ep_noop_when_already_registered():
    """A. CUDA discovered and already registered -> no download/register call."""
    manager = _FakeEpManager(initial_eps=[_FakeEp("CUDAExecutionProvider", True)])

    _ensure_cuda_execution_provider(manager)

    assert manager.download_and_register_calls == []


def test_ensure_cuda_ep_registers_only_cuda_when_not_registered():
    """B. CUDA discovered but not registered -> only CUDAExecutionProvider
    is requested, no other EP names."""
    manager = _FakeEpManager(
        initial_eps=[
            _FakeEp("CUDAExecutionProvider", False),
            _FakeEp("WebGpuExecutionProvider", False),
        ],
        register_result=_FakeEpResult(
            True, "ok", registered_eps=["CUDAExecutionProvider"]
        ),
        eps_after_register=[_FakeEp("CUDAExecutionProvider", True)],
    )

    _ensure_cuda_execution_provider(manager)  # C: must not raise

    assert manager.download_and_register_calls == [["CUDAExecutionProvider"]]


def test_ensure_cuda_ep_raises_when_cuda_not_discovered():
    """D. CUDA not in discover_eps() at all -> clear exception, no silent
    CPU fallback."""
    manager = _FakeEpManager(initial_eps=[_FakeEp("WebGpuExecutionProvider", False)])

    with pytest.raises(RuntimeError, match="keşfedilemedi"):
        _ensure_cuda_execution_provider(manager)

    assert manager.download_and_register_calls == []


def test_ensure_cuda_ep_raises_when_registration_result_fails():
    """E. download_and_register_eps() reports failure -> clear exception."""
    manager = _FakeEpManager(
        initial_eps=[_FakeEp("CUDAExecutionProvider", False)],
        register_result=_FakeEpResult(
            False, "Bootstrapper failed", registered_eps=[], failed_eps=["CUDAExecutionProvider"]
        ),
    )

    with pytest.raises(RuntimeError, match="başarısız"):
        _ensure_cuda_execution_provider(manager)


def test_ensure_cuda_ep_raises_when_post_check_still_unregistered():
    """E (variant): result.success=True but a post-registration discover_eps()
    still reports registered=False -> must not be trusted silently."""
    manager = _FakeEpManager(
        initial_eps=[_FakeEp("CUDAExecutionProvider", False)],
        register_result=_FakeEpResult(
            True, "ok", registered_eps=["CUDAExecutionProvider"]
        ),
        eps_after_register=[_FakeEp("CUDAExecutionProvider", False)],
    )

    with pytest.raises(RuntimeError, match="hâlâ registered=False"):
        _ensure_cuda_execution_provider(manager)


def test_get_manager_registers_cuda_before_caching_manager(monkeypatch):
    """F: _get_manager() must run CUDA EP registration before it hands the
    manager back (and therefore before get_loaded_model() ever touches
    manager.catalog, since get_loaded_model calls _get_manager() first)."""
    import foundry_local_sdk

    fake_instance = object()
    calls: list = []

    class _FakeConfiguration:
        def __init__(self, app_name, model_cache_dir=None):
            self.app_name = app_name
            self.model_cache_dir = model_cache_dir

    class _FakeFoundryLocalManager:
        instance = None

        @staticmethod
        def initialize(config):
            calls.append("initialize")
            _FakeFoundryLocalManager.instance = fake_instance

    def fake_ensure(manager):
        calls.append("ensure_cuda")
        assert manager is fake_instance

    monkeypatch.setattr(foundry_local_sdk, "Configuration", _FakeConfiguration)
    monkeypatch.setattr(
        foundry_local_sdk, "FoundryLocalManager", _FakeFoundryLocalManager
    )
    monkeypatch.setattr(
        foundry_service, "_ensure_cuda_execution_provider", fake_ensure
    )

    provider = FoundryProvider()
    result = provider._get_manager()

    assert result is fake_instance
    assert calls == ["initialize", "ensure_cuda"]
    # Second call must be a pure cache hit: no re-initialize, no re-register.
    provider._get_manager()
    assert calls == ["initialize", "ensure_cuda"]


def test_get_manager_passes_model_cache_dir_to_configuration(monkeypatch):
    """A: the Configuration handed to FoundryLocalManager.initialize() must
    carry settings.foundry_model_cache_dir, so the SDK looks at the same
    cache root as the Foundry CLI instead of its own per-app_name default."""
    import foundry_local_sdk

    fake_instance = object()
    captured: dict = {}

    class _FakeConfiguration:
        def __init__(self, app_name, model_cache_dir=None):
            captured["app_name"] = app_name
            captured["model_cache_dir"] = model_cache_dir

    class _FakeFoundryLocalManager:
        instance = None

        @staticmethod
        def initialize(config):
            _FakeFoundryLocalManager.instance = fake_instance

    monkeypatch.setattr(foundry_local_sdk, "Configuration", _FakeConfiguration)
    monkeypatch.setattr(
        foundry_local_sdk, "FoundryLocalManager", _FakeFoundryLocalManager
    )
    monkeypatch.setattr(
        foundry_service, "_ensure_cuda_execution_provider", lambda manager: None
    )

    provider = FoundryProvider()
    result = provider._get_manager()

    assert result is fake_instance
    assert captured["app_name"] == settings.app_name
    assert captured["model_cache_dir"] == str(settings.foundry_model_cache_dir)


def test_get_manager_does_not_cache_manager_when_cuda_registration_fails(monkeypatch):
    import foundry_local_sdk

    fake_instance = object()

    class _FakeConfiguration:
        def __init__(self, app_name, model_cache_dir=None):
            self.app_name = app_name
            self.model_cache_dir = model_cache_dir

    class _FakeFoundryLocalManager:
        instance = None

        @staticmethod
        def initialize(config):
            _FakeFoundryLocalManager.instance = fake_instance

    def fake_ensure(manager):
        raise RuntimeError("CUDA registration boom")

    monkeypatch.setattr(foundry_local_sdk, "Configuration", _FakeConfiguration)
    monkeypatch.setattr(
        foundry_local_sdk, "FoundryLocalManager", _FakeFoundryLocalManager
    )
    monkeypatch.setattr(
        foundry_service, "_ensure_cuda_execution_provider", fake_ensure
    )

    provider = FoundryProvider()
    with pytest.raises(RuntimeError, match="CUDA registration boom"):
        provider._get_manager()

    assert provider._manager is None


def test_get_loaded_model_applies_selection_before_load(monkeypatch):
    cpu = _FakeVariant("phi-4-mini-generic-cpu:5", cached=False, device_type="CPU")
    gpu = _FakeVariant("phi-4-mini-cuda-gpu:5", cached=True, device_type="GPU")
    model = _FakeModel("phi-4-mini", [cpu, gpu], selected_index=0)
    model.load_called = False
    model.load = lambda: setattr(model, "load_called", True)

    class _FakeCatalog:
        def get_model(self, alias):
            assert alias == "phi-4-mini"
            return model

    class _FakeManager:
        catalog = _FakeCatalog()

    provider = FoundryProvider()
    monkeypatch.setattr(provider, "_get_manager", lambda: _FakeManager())

    result = provider.get_loaded_model("phi-4-mini")

    assert result is model
    assert model.select_variant_calls == [gpu]
    assert model.load_called is True


class _FakeLoadedModel:
    """Minimal stand-in for an already-loaded Foundry model: tracks whether
    unload() was called and whether it should raise, without touching the
    real SDK."""

    def __init__(self, is_loaded=True, raise_on_unload=False):
        self.is_loaded = is_loaded
        self.unload_called = False
        self._raise_on_unload = raise_on_unload

    def unload(self):
        self.unload_called = True
        if self._raise_on_unload:
            raise RuntimeError("unload boom")
        self.is_loaded = False


def test_unload_model_only_affects_requested_alias():
    """A. unload_model(alias) unloads only the requested model; every other
    cached alias (e.g. the chat model) stays untouched -- this is also the
    direct guarantee for 'embedding unload does not affect the chat
    model'."""
    embedding_model = _FakeLoadedModel()
    chat_model = _FakeLoadedModel()
    provider = FoundryProvider()
    provider._models["qwen3-embedding-0.6b"] = embedding_model
    provider._models["phi-4-mini"] = chat_model

    result = provider.unload_model("qwen3-embedding-0.6b")

    assert result is True
    assert embedding_model.unload_called is True
    assert "qwen3-embedding-0.6b" not in provider._models
    assert chat_model.unload_called is False
    assert provider._models["phi-4-mini"] is chat_model


def test_unload_model_is_noop_when_alias_not_cached():
    """B, I. Unloading an alias that was never loaded (or already unloaded)
    must not raise, must not touch the cache, and must report success
    (True) -- a caller doing GPU model swapping must be able to treat "was
    never loaded" the same as "successfully unloaded": both mean it's safe
    to load a different model now."""
    provider = FoundryProvider()
    other_model = _FakeLoadedModel()
    provider._models["phi-4-mini"] = other_model

    result = provider.unload_model("qwen3-embedding-0.6b")  # must not raise

    assert result is True
    assert provider._models == {"phi-4-mini": other_model}
    assert other_model.unload_called is False


def test_unload_model_allows_reload_on_next_get_loaded_model(monkeypatch):
    """D. After unload_model() removes the alias from the cache,
    get_loaded_model() must go through the full load path again (catalog
    lookup + load()) instead of treating it as still loaded."""
    embedding_model = _FakeLoadedModel()
    provider = FoundryProvider()
    provider._models["qwen3-embedding-0.6b"] = embedding_model

    provider.unload_model("qwen3-embedding-0.6b")
    assert "qwen3-embedding-0.6b" not in provider._models

    reloaded = _FakeVariant("m-gpu:1", cached=True, device_type="GPU")
    fresh_model = _FakeModel("qwen3-embedding-0.6b", [reloaded], selected_index=0)
    fresh_model.load_called = False
    fresh_model.load = lambda: setattr(fresh_model, "load_called", True)

    class _FakeCatalog:
        def get_model(self, alias):
            assert alias == "qwen3-embedding-0.6b"
            return fresh_model

    class _FakeManager:
        catalog = _FakeCatalog()

    monkeypatch.setattr(provider, "_get_manager", lambda: _FakeManager())

    result = provider.get_loaded_model("qwen3-embedding-0.6b")

    assert result is fresh_model
    assert fresh_model.load_called is True
    assert provider._models["qwen3-embedding-0.6b"] is fresh_model


def test_unload_model_failure_is_logged_and_swallowed():
    """Unload failures must not raise or corrupt state: the model stays in
    the cache (still considered resident) instead of being dropped on a
    failed unload() call."""
    broken_model = _FakeLoadedModel(raise_on_unload=True)
    provider = FoundryProvider()
    provider._models["qwen3-embedding-0.6b"] = broken_model

    result = provider.unload_model("qwen3-embedding-0.6b")  # must not raise

    assert result is False
    assert broken_model.unload_called is True
    assert provider._models["qwen3-embedding-0.6b"] is broken_model


def test_unload_all_still_unloads_every_model_and_clears_cache():
    """G. unload_all() keeps its existing behavior: every cached model is
    unloaded and the cache is cleared, regardless of the new unload_model()
    method."""
    embedding_model = _FakeLoadedModel()
    chat_model = _FakeLoadedModel()
    provider = FoundryProvider()
    provider._models["qwen3-embedding-0.6b"] = embedding_model
    provider._models["phi-4-mini"] = chat_model

    provider.unload_all()

    assert embedding_model.unload_called is True
    assert chat_model.unload_called is True
    assert provider._models == {}
