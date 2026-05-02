# Contributing to USDw

Thanks for your interest! USDw is a teaching project, so contributions that improve **clarity** and **learning value** are especially welcome.

## How to contribute

1. **Check the [issues](../../issues)** for something to work on, or open a new one to discuss your idea before writing code.
2. **Fork** the repo and create a feature branch: `git checkout -b feature/your-idea`.
3. **Make your changes**, with tests where it makes sense.
4. **Run the checks** locally (see below) before opening a PR.
5. **Open a pull request** filling in the template.

## Local development

```bash
# Set up
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Run tests
pytest

# Lint
ruff check python_sim ui tests

# Run the UI
streamlit run ui/app.py
```

## Coding style

- **Python**: ruff defaults (PEP 8). Type hints encouraged for public APIs.
- **JavaScript chaincode**: stay close to the existing minimal style — small contracts read better than over-engineered ones.
- **Tests**: prefer many small, descriptive tests over a few large ones. Use `pytest` fixtures for setup.

## Commits and PRs

- Small, focused PRs are easier to review than sweeping ones.
- Update the README or docs if you change behavior or add a feature.
- Don't commit virtualenvs, `node_modules/`, or `.DS_Store` files (the `.gitignore` covers these).

## Reporting security issues

Please do **not** open public issues for security vulnerabilities. Email the maintainers directly. Since this is a teaching project, "vulnerabilities" in the regulatory or cryptographic mocks are expected — focus reports on bugs that could mislead readers about real-world stablecoin security.

## Code of Conduct

By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
