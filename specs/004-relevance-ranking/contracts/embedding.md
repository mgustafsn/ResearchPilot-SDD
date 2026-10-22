# EmbeddingProvider and local setup contract

**Status**: Approved with the plan by the user on 2026-10-21 (reply: “I approve”); tasks/implementation subsequently authorized (reply: “Start”).

## Vendor-free interface

`async embed(inputs: list[EmbeddingInput]) -> EmbeddingBatch`

- Input IDs unique, context first then stable provider paper IDs; nonempty normalized
  text. At most 251 inputs. Call only after successful nonempty deduplication.
- Output covers exactly the ordered input IDs; validate no missing/extra/duplicate
  ID, no boolean/nonfinite component, common dimension >0 and fixed model identity.
- Each item includes vector, hash of actual unpadded truncated token IDs, token
  count and truncation flag. Domain computes full normalized UTF-8 text hash.
- Local adapter returns 384 float32 components, 256-token maximum, pinned revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, inputVersion `ranking-input-v1`.
- Token hash = SHA-256 over UTF-8 JSON of token IDs, compact separators, decimal
  integer list, no trailing newline; includes special tokens, excludes padding.
- Return vectors in common Python structures, not torch/NumPy objects outside the
  adapter. Test fakes need no model installation or vendor imports.
- Safe typed errors: `model_missing`, `model_invalid`, `busy`, `timeout`,
  `invalid_response`, `unavailable`. Never propagate original exception strings.
- Cancellation terminates/reaps child and releases ranking slot; no background
  inference retry. No child has database access or writes results directly.

## Runtime loading

Manifest-verified local directory only. Set offline/telemetry controls before ML
imports, including HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE, HF_HUB_DISABLE_TELEMETRY,
HF_HUB_DISABLE_IMPLICIT_TOKEN and DO_NOT_TRACK. Force local_files_only,
trust_remote_code false, token false, CPU, safetensors, eval/no-grad, batch size 32,
max 256 tokens, right truncation, no input prompts or dimension truncation.
Require the pinned standard Transformer, mean Pooling and Normalize modules only; reject extra module
classes/configurations rather than dynamically importing arbitrary local/remote code.
No arbitrary Hub model lookup, telemetry, implicit login, or automatic repair.

The parent enforces 60-second job budget inclusive of model loading, one active
job per app process, and cancellation cleanup. Model/worker logs never include raw
texts, vector values, native tracebacks, tokens, credentials or local file paths.

## Explicit setup CLI (proposed)

`PYTHONPATH=backend uv run python -m researchpilot.integrations.setup_embeddings`

This command is implemented. Download only the pinned public model's
approved files, without an account token or any project/paper inputs. Require
explicit invocation; never invoked by app startup, GET, Search, tests, or CI.
Use HTTPS, an allowlist and bounded timeouts (30 seconds/request, 10 minutes total,
no application-level retry); manifest and atomic promotion on completion. Default
destination is ignored `.models/all-MiniLM-L6-v2/<revision>/`. Repeated setup with a
verified complete installation exits without network; incomplete/different target
fails with a repair instruction, not deletion/overwrite. Setup failures log a safe
category, leave no completion marker and never alter application data.

Hash every installed model/config/tokenizer file, retain revision/license, and
verify pinned safetensors rather than pickle assets. Setup may use its own staging
directory, not the application database. Test using mocked downloads and temporary
directories only; never invoke live setup from the repeatable suite.
