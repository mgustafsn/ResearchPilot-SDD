"""Manifest-verified CPU inference in a bounded, offline child process."""

import asyncio
import hashlib
import json
import multiprocessing
import os
import socket
import threading
import time
from importlib.metadata import version
from pathlib import Path

from researchpilot.embedding_provider import (
    MODEL_ID,
    MODEL_REVISION,
    EmbeddingBatch,
    EmbeddingError,
    EmbeddingInput,
    EmbeddingItem,
)
from researchpilot.ranking_domain import token_hash, validate_batch

MODEL_FILES = (
    "modules.json",
    "1_Pooling/config.json",
    "sentence_bert_config.json",
    "config.json",
    "config_sentence_transformers.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "vocab.txt",
    "model.safetensors",
    "README.md",
)
DEFAULT_DIRECTORY = (
    Path(__file__).resolve().parents[3] / ".models" / "all-MiniLM-L6-v2" / MODEL_REVISION
)
OFFLINE_FLAGS = (
    "HF_HUB_OFFLINE",
    "TRANSFORMERS_OFFLINE",
    "HF_HUB_DISABLE_TELEMETRY",
    "HF_HUB_DISABLE_IMPLICIT_TOKEN",
    "DO_NOT_TRACK",
)


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_installation(directory):
    directory = Path(directory)
    if not directory.exists():
        raise EmbeddingError("model_missing")
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError
        paths = list(directory.rglob("*"))
        if any(path.is_symlink() for path in paths):
            raise ValueError
        files = {p.relative_to(directory).as_posix() for p in paths if p.is_file()}
        if files != set(MODEL_FILES) | {"manifest.json"}:
            raise ValueError
        manifest = json.loads((directory / "manifest.json").read_text())
        if (
            manifest["modelId"] != MODEL_ID
            or manifest["modelRevision"] != MODEL_REVISION
            or manifest["license"] != "apache-2.0"
            or set(manifest["files"]) != set(MODEL_FILES)
        ):
            raise ValueError
        for name in MODEL_FILES:
            if file_hash(directory / name) != manifest["files"][name]:
                raise ValueError
        modules = json.loads((directory / "modules.json").read_text())
        expected = [("", "Transformer"), ("1_Pooling", "Pooling"), ("2_Normalize", "Normalize")]
        if len(modules) != 3:
            raise ValueError
        for index, (path, kind) in enumerate(expected):
            if modules[index] != {
                "idx": index,
                "name": str(index),
                "path": path,
                "type": f"sentence_transformers.models.{kind}",
            }:
                raise ValueError
        config = json.loads((directory / "config.json").read_text())
        sequence = json.loads((directory / "sentence_bert_config.json").read_text())
        pooling = json.loads((directory / "1_Pooling/config.json").read_text())
        if (
            config.get("model_type") != "bert"
            or config.get("hidden_size") != 384
            or sequence.get("max_seq_length") != 256
            or pooling.get("word_embedding_dimension") != 384
            or pooling.get("pooling_mode_mean_tokens") is not True
            or any(
                value
                for key, value in pooling.items()
                if key.startswith("pooling_mode_") and key != "pooling_mode_mean_tokens"
            )
        ):
            raise ValueError
        return manifest
    except (OSError, ValueError, KeyError, TypeError):
        raise EmbeddingError("model_invalid") from None


def load_model(directory, factory=None):
    for flag in OFFLINE_FLAGS:
        os.environ[flag] = "1"
    verify_installation(directory)
    if factory is None:
        from sentence_transformers import SentenceTransformer

        factory = SentenceTransformer
    model = factory(
        str(Path(directory).resolve()),
        device="cpu",
        local_files_only=True,
        trust_remote_code=False,
        token=False,
        model_kwargs={"use_safetensors": True, "dtype": "float32"},
    )
    model.max_seq_length = 256
    if model.get_sentence_embedding_dimension() != 384:
        raise EmbeddingError("model_invalid")
    model.eval()
    return model


def encode_inputs(model, inputs):
    import torch

    model.tokenizer.truncation_side = "right"
    items = []
    for start in range(0, len(inputs), 32):
        chunk = inputs[start : start + 32]
        texts = [item.text for item in chunk]
        lengths = [
            len(model.tokenizer(text, truncation=False, add_special_tokens=True)["input_ids"])
            for text in texts
        ]
        features = model.tokenizer(
            texts, padding=True, truncation=True, max_length=256, return_tensors="pt"
        )
        with torch.inference_mode():
            vectors = model(features)["sentence_embedding"].cpu().float().tolist()
        for index, (item, vector) in enumerate(zip(chunk, vectors, strict=True)):
            tokens = features["input_ids"][index][features["attention_mask"][index].bool()].tolist()
            items.append(
                EmbeddingItem(
                    id=item.id,
                    vector=vector,
                    token_hash=token_hash(tokens),
                    token_count=len(tokens),
                    truncated=lengths[index] > 256,
                )
            )
    return EmbeddingBatch(
        model_id=MODEL_ID,
        model_revision=MODEL_REVISION,
        dimension=384,
        items=items,
        package_versions={
            name: version(name)
            for name in ("sentence-transformers", "torch", "transformers", "tokenizers")
        },
    )


def deny_network(*args, **kwargs):
    raise OSError("Network disabled for local inference")


def inference_worker(connection, directory, inputs):
    # Confine both library network access and native/library diagnostics to this child.
    with open(os.devnull, "w") as sink:
        os.dup2(sink.fileno(), 1)
        os.dup2(sink.fileno(), 2)
    socket.socket.connect = deny_network
    socket.socket.connect_ex = deny_network
    socket.create_connection = deny_network
    socket.getaddrinfo = deny_network
    for flag in OFFLINE_FLAGS:
        os.environ[flag] = "1"
    try:
        import torch

        torch.set_num_threads(4)
        torch.set_num_interop_threads(1)
        model = load_model(directory)
        parsed = [EmbeddingInput.model_validate(item) for item in inputs]
        connection.send({"ok": encode_inputs(model, parsed).model_dump()})
    except EmbeddingError as error:
        connection.send({"error": error.category})
    except Exception:
        connection.send({"error": "unavailable"})
    finally:
        connection.close()


class LocalEmbeddingProvider:
    def __init__(self, directory=None, timeout=60, worker=None):
        self.directory = Path(
            directory or os.environ.get("EMBEDDING_MODEL_DIR") or DEFAULT_DIRECTORY
        )
        self.timeout = timeout
        self.worker = worker or inference_worker
        self._slot = threading.Lock()
        self.active_process = None
        self.closed = False

    @property
    def busy(self):
        return self._slot.locked()

    def _stop_child(self):
        process = self.active_process
        if process is not None:
            if process.is_alive():
                process.terminate()
            process.join(timeout=0.3)
            if process.is_alive():
                process.kill()
                process.join(timeout=1)
            self.active_process = None

    async def embed(self, inputs):
        if self.closed:
            raise EmbeddingError("unavailable")
        if not self._slot.acquire(blocking=False):
            raise EmbeddingError("busy")
        receiver = sender = None
        try:
            if not 1 <= len(inputs) <= 251:
                raise EmbeddingError("invalid_response")
            context = multiprocessing.get_context("spawn")
            receiver, sender = context.Pipe(duplex=False)
            process = context.Process(
                target=self.worker,
                args=(sender, str(self.directory), [item.model_dump() for item in inputs]),
                daemon=True,
            )
            started = time.monotonic()
            process.start()
            self.active_process = process
            sender.close()
            while not receiver.poll():
                if time.monotonic() - started >= self.timeout:
                    raise EmbeddingError("timeout")
                if not process.is_alive():
                    raise EmbeddingError("unavailable")
                await asyncio.sleep(0.02)
            message = receiver.recv()
            if "error" in message:
                category = message["error"]
                if category not in {"model_missing", "model_invalid", "unavailable"}:
                    category = "unavailable"
                raise EmbeddingError(category)
            result = validate_batch(inputs, message["ok"])
            if result.dimension != 384:
                raise EmbeddingError("invalid_response")
            return result
        except EmbeddingError:
            raise
        except Exception:
            raise EmbeddingError("unavailable") from None
        finally:
            self._stop_child()
            if receiver is not None:
                receiver.close()
            if sender is not None:
                sender.close()
            self._slot.release()

    async def aclose(self):
        self.closed = True
        self._stop_child()
