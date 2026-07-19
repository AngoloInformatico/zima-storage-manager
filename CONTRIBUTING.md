# Contributing

1. Open an issue describing the problem or proposal.
2. Create a focused branch.
3. Add or update tests.
4. Run `pytest` and `ruff check .`.
5. Submit a pull request with reproduction steps and safety considerations.

Changes to privileged workflows must preserve automatic backup, validation, transaction handling and rollback behavior.
