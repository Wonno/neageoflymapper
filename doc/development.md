# 🛠️ Development

## 📋 Requirements

- 🐍 Python 3.11.13
- 📦 Poetry

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

```bash
poetry install
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
poetry run pylint src/main.py tests/
```

## 🔨 Building the Binary

To create a standalone executable:

```bash
poetry run pyinstaller --onefile src/main.py --name nea-geofly-mapper
```

The resulting binary will be located in the `dist/` directory.
