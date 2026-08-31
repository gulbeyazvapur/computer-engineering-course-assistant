"""Download/cache and load the Foundry Local models once while online.

After the models are cached locally, set AUTO_DOWNLOAD_MODELS=false to make
missing model files fail fast instead of trying to download them.
"""

from app.core.config import settings
from app.services.foundry_service import foundry_provider


def main() -> None:
    aliases = [
        settings.embedding_model_name,
        settings.chat_model_name,
    ]

    for alias in aliases:
        print(f"Preparing model: {alias}")
        model = foundry_provider.get_loaded_model(alias)
        print(
            f"  cached={getattr(model, 'is_cached', 'unknown')} "
            f"loaded={getattr(model, 'is_loaded', 'unknown')}"
        )

    print("Models are ready.")
    foundry_provider.unload_all()


if __name__ == "__main__":
    main()
