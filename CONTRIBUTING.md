# Contributing to MarketReality OS

Thank you for your interest in contributing.

## Contribution Workflow

1. Fork the repository.
2. Create a branch (`git checkout -b feature/your-feature`).
3. Make your changes.
4. Add/update tests where applicable.
5. Run checks (lint, build).
6. Open a pull request.

## Engineering Rules

- **Preserve deterministic calculations**: Do not introduce randomness into the `reality.py` engine.
- **Don't fabricate market data**: If an endpoint fails, fail gracefully.
- **Preserve evidence provenance**: Any new calculation must generate a corresponding `Evidence` object.
- **Document CMC endpoint changes**: If you add a new CMC endpoint, update `docs/cmc-integration.md`.
- **Add tests**: Any changes to analytical logic must be tested.
- **Avoid unnecessary dependencies**: Keep the core lightweight. No heavy machine learning libraries for the core engine.
