"""Explicit setup only; never called from application startup or Search."""

import json
import multiprocessing
import os
import shutil
import tempfile
from pathlib import Path

from researchpilot.embedding_provider import MODEL_ID, MODEL_REVISION, EmbeddingError
from researchpilot.integrations.local_embeddings import (
    DEFAULT_DIRECTORY,
    MODEL_FILES,
    file_hash,
    verify_installation,
)


def _download(destination):
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["HF_HUB_ETAG_TIMEOUT"] = "30"
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "30"
    from huggingface_hub import snapshot_download
    from huggingface_hub.utils import disable_progress_bars

    disable_progress_bars()
    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=destination,
        allow_patterns=list(MODEL_FILES),
        token=False,
        max_workers=2,
    )


def _download_worker(destination):
    with open(os.devnull, "w") as sink:
        os.dup2(sink.fileno(), 1)
        os.dup2(sink.fileno(), 2)
    try:
        _download(destination)
    except Exception:
        raise SystemExit(1) from None


def install_model(destination, downloader=None):
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        verify_installation(destination)
        return
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".embedding-setup-", dir=destination.parent) as tmp:
            raw, ready = Path(tmp) / "download", Path(tmp) / "ready"
            raw.mkdir()
            ready.mkdir()
            if downloader is not None:
                downloader(
                    repo_id=MODEL_ID,
                    revision=MODEL_REVISION,
                    local_dir=str(raw),
                    allow_patterns=list(MODEL_FILES),
                    token=False,
                    max_workers=2,
                )
            else:
                process = multiprocessing.get_context("spawn").Process(
                    target=_download_worker, args=(str(raw),)
                )
                try:
                    process.start()
                    process.join(timeout=600)
                    if process.is_alive() or process.exitcode != 0:
                        raise EmbeddingError("unavailable")
                finally:
                    if process.is_alive():
                        process.terminate()
                        process.join(timeout=1)
                    if process.is_alive():
                        process.kill()
                        process.join()
            for name in MODEL_FILES:
                source, target = raw / name, ready / name
                if source.is_symlink() or not source.is_file():
                    raise EmbeddingError("model_invalid")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            manifest = {
                "modelId": MODEL_ID,
                "modelRevision": MODEL_REVISION,
                "license": "apache-2.0",
                "files": {name: file_hash(ready / name) for name in MODEL_FILES},
            }
            (ready / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
            verify_installation(ready)
            # Never replace an existing directory, including a concurrently created target.
            if destination.exists() or destination.is_symlink():
                raise EmbeddingError("model_invalid")
            ready.rename(destination)
    except EmbeddingError:
        raise
    except Exception:
        raise EmbeddingError("unavailable") from None


if __name__ == "__main__":
    try:
        install_model(os.environ.get("EMBEDDING_MODEL_DIR") or DEFAULT_DIRECTORY)
    except EmbeddingError as error:
        raise SystemExit(f"Local model setup failed ({error.category}); existing files/data kept.")
    print(f"Local model ready: {MODEL_ID} revision {MODEL_REVISION}")
