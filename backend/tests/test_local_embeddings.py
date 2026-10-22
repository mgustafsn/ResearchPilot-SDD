"""FR-RNK-008/009 offline adapter/setup contract, never download real weights."""

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path

import pytest
from researchpilot.embedding_provider import (
    MODEL_ID,
    MODEL_REVISION,
    EmbeddingError,
    EmbeddingInput,
)
from researchpilot.integrations.local_embeddings import (
    LocalEmbeddingProvider,
    encode_inputs,
    load_model,
    verify_installation,
)
from researchpilot.integrations.setup_embeddings import install_model
from researchpilot.ranking_domain import token_hash

FILES = {
    "modules.json": json.dumps(
        [
            {"idx": 0, "name": "0", "path": "", "type": "sentence_transformers.models.Transformer"},
            {
                "idx": 1,
                "name": "1",
                "path": "1_Pooling",
                "type": "sentence_transformers.models.Pooling",
            },
            {
                "idx": 2,
                "name": "2",
                "path": "2_Normalize",
                "type": "sentence_transformers.models.Normalize",
            },
        ]
    ),
    "1_Pooling/config.json": json.dumps(
        {
            "word_embedding_dimension": 384,
            "pooling_mode_mean_tokens": True,
            "pooling_mode_cls_token": False,
            "pooling_mode_max_tokens": False,
            "pooling_mode_mean_sqrt_len_tokens": False,
        }
    ),
    "sentence_bert_config.json": '{"max_seq_length":256,"do_lower_case":false}',
    "config.json": '{"model_type":"bert","hidden_size":384}',
    "config_sentence_transformers.json": "{}",
    "tokenizer.json": "{}",
    "tokenizer_config.json": "{}",
    "special_tokens_map.json": "{}",
    "vocab.txt": "[PAD]\n",
    "model.safetensors": "fake weights",
    "README.md": "license: apache-2.0",
}


def fake_download(**kwargs):
    assert kwargs["repo_id"] == MODEL_ID
    assert kwargs["revision"] == MODEL_REVISION
    assert kwargs["token"] is False
    assert set(kwargs["allow_patterns"]) == set(FILES)
    for name, content in FILES.items():
        path = Path(kwargs["local_dir"]) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def installed(tmp_path):
    target = tmp_path / "model"
    install_model(target, downloader=fake_download)
    return target


def test_FR_RNK_009_setup_verified_repeat_and_no_network(tmp_path):
    target = installed(tmp_path)
    manifest = verify_installation(target)
    assert manifest["modelRevision"] == MODEL_REVISION
    assert manifest["license"] == "apache-2.0"
    assert manifest["files"]["model.safetensors"] == hashlib.sha256(b"fake weights").hexdigest()
    install_model(target, downloader=lambda **kw: pytest.fail("unexpected download"))


@pytest.mark.parametrize("defect", ["missing", "tamper", "module", "revision", "symlink", "extra"])
def test_FR_RNK_009_refuse_invalid_installations(tmp_path, defect):
    target = installed(tmp_path)
    if defect == "missing":
        (target / "model.safetensors").unlink()
    elif defect == "tamper":
        (target / "vocab.txt").write_text("modified")
    elif defect == "module":
        path = target / "modules.json"
        path.write_text('[{"type":"os.system"}]')
        manifest_path = target / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["files"]["modules.json"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
    elif defect == "revision":
        manifest = json.loads((target / "manifest.json").read_text())
        manifest["modelRevision"] = "main"
        (target / "manifest.json").write_text(json.dumps(manifest))
    elif defect == "symlink":
        path = target / "vocab.txt"
        path.unlink()
        path.symlink_to(tmp_path / "outside")
    elif defect == "extra":
        (target / "evil.py").write_text("raise Exception")
    with pytest.raises(EmbeddingError, match="Local embedding"):
        verify_installation(target)


def test_FR_RNK_009_partial_setup_not_overwritten(tmp_path):
    target = tmp_path / "model"
    target.mkdir()
    (target / "user-file").write_text("keep")
    with pytest.raises(EmbeddingError):
        install_model(target, downloader=lambda **kw: pytest.fail("unexpected download"))
    assert (target / "user-file").read_text() == "keep"


def test_FR_RNK_009_failed_download_has_no_complete_install(tmp_path):
    def fail(**kwargs):
        raise RuntimeError("secret/path/body")

    with pytest.raises(EmbeddingError) as error:
        install_model(tmp_path / "model", downloader=fail)
    assert "secret" not in str(error.value)
    assert not (tmp_path / "model").exists()


def test_FR_RNK_008_loader_forces_local_flags(tmp_path):
    target = installed(tmp_path)

    def factory(path, **kwargs):
        assert Path(path).is_absolute()
        assert kwargs["local_files_only"] is True
        assert kwargs["trust_remote_code"] is False
        assert kwargs["device"] == "cpu" and kwargs["token"] is False
        assert kwargs["model_kwargs"]["use_safetensors"] is True
        for key in (
            "HF_HUB_OFFLINE",
            "HF_HUB_DISABLE_TELEMETRY",
            "HF_HUB_DISABLE_IMPLICIT_TOKEN",
            "TRANSFORMERS_OFFLINE",
            "DO_NOT_TRACK",
        ):
            assert os.environ[key] == "1"

        class Model:
            def eval(self):
                return self

            def get_sentence_embedding_dimension(self):
                return 384

        return Model()

    assert load_model(target, factory=factory).get_sentence_embedding_dimension() == 384


def test_FR_RNK_001_002_exact_truncated_tokens(tmp_path):
    import torch

    class Tokenizer:
        truncation_side = "right"

        def __call__(self, texts, **kwargs):
            if isinstance(texts, str):
                return {"input_ids": list(range(300 if texts == "long" else 3))}
            return {
                "input_ids": torch.tensor([list(range(256)), [0, 1, 2] + [0] * 253]),
                "attention_mask": torch.tensor([[1] * 256, [1] * 3 + [0] * 253]),
            }

    class Model:
        tokenizer = Tokenizer()

        def __call__(self, features):
            assert not torch.is_grad_enabled()
            return {"sentence_embedding": torch.ones((2, 384))}

    inputs = [EmbeddingInput(id="context", text="long"), EmbeddingInput(id="W1", text="short")]
    batch = encode_inputs(Model(), inputs)
    assert batch.dimension == 384
    assert batch.items[0].truncated and not batch.items[1].truncated
    assert batch.items[0].token_count == 256
    assert batch.items[1].token_count == 3
    assert batch.items[0].token_hash == token_hash(list(range(256)))
    assert batch.items[1].token_hash == token_hash([0, 1, 2])


def hanging_worker(connection, directory, inputs):
    time.sleep(20)


def crashing_worker(connection, directory, inputs):
    connection.close()


@pytest.mark.parametrize(
    "worker,category", [(hanging_worker, "timeout"), (crashing_worker, "unavailable")]
)
def test_FR_RNK_007_worker_failure_cleanup(tmp_path, worker, category):
    async def run():
        provider = LocalEmbeddingProvider(tmp_path, timeout=0.3, worker=worker)
        with pytest.raises(EmbeddingError) as error:
            await provider.embed([EmbeddingInput(id="context", text="Q")])
        assert error.value.category == category
        assert provider.active_process is None
        assert not provider.busy
        await provider.aclose()

    asyncio.run(run())


def test_FR_RNK_007_busy_cancel_and_slot_release(tmp_path):
    async def run():
        provider = LocalEmbeddingProvider(tmp_path, worker=hanging_worker)
        task = asyncio.create_task(provider.embed([EmbeddingInput(id="context", text="Q")]))
        while provider.active_process is None:
            await asyncio.sleep(0)
            if task.done():
                await task
        with pytest.raises(EmbeddingError) as error:
            await provider.embed([EmbeddingInput(id="context", text="Q")])
        assert error.value.category == "busy"
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not provider.busy and provider.active_process is None
        await provider.aclose()

    asyncio.run(run())
