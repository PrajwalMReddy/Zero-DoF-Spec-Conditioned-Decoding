# Zero-DoF Spec-Conditioned Decoding Engine

This repository implements a prototype of the Zero-DoF Spec-Conditioned Decoding Engine (Zero-SCD).

## Files

- `llm_client.py`: LLM stream manager with a stubbed token stream and rollback-friendly interface.
- `ast_parser.py`: Semantic checkpoint detection using Python AST and compile-time validation.
- `oracle_sandbox.py`: Isolated sandbox executor with restricted builtins, syntactic blacklist, timeout enforcement, and mini property-based checking.
- `zero_scd_engine.py`: Orchestrator loop implementing speculative buffering, semantic checkpoints, rollback, and error injection.
- `raw_generation_baseline.py`: Simple baseline generation script using the same LLM client interface.

## Running

Use `python zero_scd_engine.py` to run a minimal local demo.
Use `python raw_generation_baseline.py` to run a baseline generation sample.

## Notes

- This implementation is a local prototype and uses a stubbed LLM stream.
- Replace `LLMClient._simulate_stream` with a real Gemini 2.0 Flash API integration for production use.
- The sandbox enforces a 20ms timeout and rejects unsafe syntax patterns before execution.
