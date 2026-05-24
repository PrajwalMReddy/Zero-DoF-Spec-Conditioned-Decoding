# Zero-DoF Spec-Conditioned Decoding Engine

This repository implements a prototype of the Zero-DoF Spec-Conditioned Decoding Engine (Zero-SCD).

## Files

- `llm_client.py`: LLM stream manager with a stubbed token stream and rollback-friendly interface.
- `ast_parser.py`: Semantic checkpoint detection using Python AST and compile-time validation.
- `oracle_sandbox.py`: Isolated sandbox executor with restricted builtins, syntactic blacklist, timeout enforcement, and mini property-based checking.
- `zero_scd_engine.py`: Orchestrator loop implementing speculative buffering, semantic checkpoints, rollback, and error injection.
- `raw_generation_baseline.py`: Simple baseline generation script using the same LLM client interface.

## Running

Use `python zero_scd_engine.py` to run the synthesis engine.
Use `python raw_generation_baseline.py` to run a baseline generation sample.

### Examples

Run the spec-conditioned synthesis engine with a custom prompt:

```bash
python zero_scd_engine.py --prompt "# Complete the function implementation below"
```

Change retry/backoff behavior:

```bash
python zero_scd_engine.py --prompt "# Complete the function implementation below" --max-retries 5 --backoff-base 0.1 --max-backoff 1.0
```

Run the baseline generator with a prompt file:

```bash
python raw_generation_baseline.py --prompt-file prompts/example.txt --temperature 0.3 --max-tokens 128
```

Use `GEMINI_API_KEY` or `LLM_API_KEY` to configure the model API key.

## Notes

- This implementation is a local prototype and uses a stubbed LLM stream.
- Replace `LLMClient._simulate_stream` with a real Gemini 2.0 Flash API integration for production use.
- Configure the API key via `GEMINI_API_KEY` or `LLM_API_KEY`.
- Optionally use `LLM_API_URL` to point to a custom model endpoint instead of the default Gemini URL.
- The sandbox enforces a 20ms timeout and rejects unsafe syntax patterns before execution.
