# 🛠️ Development

## 📋 Requirements

- 🐍 Python 3.11.13
- 📦 Poetry 2.3.3

## 🚀 Setup

### 1. 📥 Install Poetry

If you don't have Poetry installed, follow the official installation instructions for your OS:

**🐧 Linux / 🍎 macOS / 🖥️ WSL:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**🪟 Windows (PowerShell):**

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python3 -
```

### 2. ⚙️ Configure Poetry (Recommended)

To keep virtual environments within the project directory:

```bash
poetry config virtualenvs.in-project true
```

### 3. 🧶 Install Dependencies

Install dependencies including optional build tooling

```bash
poetry install --with build
```

## 🔄 Updating Dependencies

Use Poetry to update dependencies instead of `pip`.

Update all locked dependencies to the newest versions allowed by `pyproject.toml`:

```bash
poetry update
```

Update one dependency:

```bash
poetry update requests
```

Add a new runtime dependency:

```bash
poetry add requests
```

Add a dependency to a specific group:

```bash
poetry add --group test pytest-mock
poetry add --group build pyinstaller
```

Remove a dependency:

```bash
poetry remove requests
poetry remove --group test pytest-mock
```

After dependency changes, reinstall the environment with the groups you need:

```bash
poetry install --with build
```

## 💻 Usage

Run the script directly:

```bash
poetry run python src/main.py --version
```

Example:

```bash
poetry run python src/main.py --help
```

## 🧪 Running Tests

Run the tests using pytest:

```bash
poetry run pytest
```

## 🔍 Linting

Run the linter using pylint:

```bash
poetry run pylint src/main.py src tests
```

## 🔨 Building the Binary

To create a standalone executable:

```bash
poetry install --with build
poetry run pyinstaller --onefile src/main.py --name nea-geofly-mapper
```

The resulting binary will be located in the `dist/` directory.
