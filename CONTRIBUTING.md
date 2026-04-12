# Contributing

Thank you for your interest in contributing! To maintain high code quality and consistency, please follow these guidelines.

## Development Environment Setup

1. **Python Version**: Ensure you are using Python 3.11.13.
2. **Install Poetry**: Follow the instructions in the [README.md](./README.md#1-install-poetry).
3. **Install Dependencies**:
   ```bash
   poetry install
   ```

## Contribution Workflow

### 1. Code Standards
We enforce strict linting rules using **Pylint**. Your code MUST maintain a **10.00/10** rating.
- Every module, class, and function MUST have a descriptive docstring.
- Follow PEP 8 style guidelines.
- Run the linter before submitting:
  ```bash
  poetry run pylint src/main.py src tests
  ```

### 2. Testing
Every new feature or bug fix MUST include corresponding tests in the `tests/` directory.
- Verify your changes by running:
  ```bash
  poetry run pytest
  ```
- Pull requests with failing tests or decreased coverage will not be merged.

### 3. Versioning
We use **Semantic Versioning (SemVer)**. The version is managed in `pyproject.toml`.
- Do NOT manually update the version in `pyproject.toml` unless instructed.
- Releases are handled via the [Manual Release GitHub Workflow](.github/workflows/release.yml).

### 4. Pull Request Process
1. Create a new branch for your feature or fix.
2. Ensure your code passes all tests and linting checks.
3. Update the `README.md` if you are changing CLI arguments or behavior.
4. Submit your PR with a clear description of the changes.

## Commands Reference

- **Run Application**: `poetry run python src/main.py --help`
- **Run Tests**: `poetry run pytest`
- **Run Linter**: `poetry run pylint src/main.py src tests`
- **Build Binary**: `poetry pyinstaller build`
