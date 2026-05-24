# Zero-DoF Spec-Conditioned Decoding Engine

This repository contains a prototype implementation of a spec-conditioned synthesis engine for code generation.
The core idea is to combine streaming generation, semantic checkpoints, and an executable oracle to commit only verified code fragments.

## Repository structure

- `llm_client.py`: LLM client wrapper with Gemini API support and a fallback stubbed token stream.
- `ast_parser.py`: Semantic checkpoint detector using `codeop` and Python AST validation.
- `oracle_sandbox.py`: Restricted sandbox executor with syntax filtering, safe builtins, and predicate-based invariant checking.
- `zero_scd_engine.py`: Main engine orchestrator for speculative decoding with retries, backoff, and rollback.
- `raw_generation_baseline.py`: Plain generative baseline using the same LLM client interface.
- `tests/`: Unit tests covering parser, sandbox, client, and synthesis flow.
- `prompts/example.txt`: Example prompt file for demo usage.

## Running the demo

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the Zero-SCD engine:

```powershell
python zero_scd_engine.py
```

Run the baseline generator:

```powershell
python raw_generation_baseline.py
```

Use a prompt file for reproducible demo runs:

```powershell
python zero_scd_engine.py --prompt-file prompts/example.txt --verbose
python raw_generation_baseline.py --prompt-file prompts/example.txt --temperature 0.3 --max-tokens 128
```

## CLI options

`zero_scd_engine.py` supports:

- `--prompt` / `--prompt-file`
- `--api-key`, `--model`, `--api-url`
- `--max-retries`, `--backoff-base`, `--max-backoff`
- `--sandbox-timeout`
- `--verbose`

`raw_generation_baseline.py` supports the same model configuration flags.

## Model configuration

The engine uses a real model when `GEMINI_API_KEY` or `LLM_API_KEY` is available.
Otherwise it falls back to a local stubbed completion stream for demo and testing.

If you want to target a custom endpoint, set `LLM_API_URL` or pass `--api-url`.

## Example prompt

`prompts/example.txt` contains a sample prompt to bootstrap the synthesis engine.

## Testing

Run the repository tests with:

```powershell
python -m pytest -q
```

## Notes for paper-ready presentation

- This prototype demonstrates the Zero-SCD concept, not a production-ready service.
- The current sandbox is intentionally minimal and designed for local prototype evaluation.
- The included fallback stub stream makes the demo deterministic without external API access.
- Use `--verbose` on `zero_scd_engine.py` to expose synthesis progress and checkpoint decisions.
