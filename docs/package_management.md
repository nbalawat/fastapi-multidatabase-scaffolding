# Package Management Guide

This project supports both UV and pip for package management, allowing team members to use their preferred tool.

## Using UV (Recommended)

UV is a fast, reliable Python package installer and resolver. It's significantly faster than pip and provides better dependency resolution.

### Installation

```bash
# Install UV
pip install uv
```

### Basic Commands

```bash
# Install all dependencies from pyproject.toml
uv pip sync

# Install a new package and add it to pyproject.toml
uv pip install package_name

# Install development dependencies
uv pip sync --dev

# Run a command in the virtual environment
uv run python -m pytest
```

## Using pip

For team members who prefer pip, we maintain a requirements.txt file that mirrors the dependencies in pyproject.toml.

### Basic Commands

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Install a new package
pip install package_name
```

## Keeping Requirements in Sync

When adding new dependencies to the project:

1. If using UV, add them to `pyproject.toml` in the appropriate section
2. If using pip, add them to `requirements.txt`
3. Inform the team about the new dependency

Team members using UV should run `uv pip sync` to update their environment, while those using pip should run `pip install -r requirements.txt`.

## Docker Environment

Our Docker setup uses UV by default for faster builds, but the application will work the same regardless of which package manager you use locally.

## Troubleshooting

If you encounter dependency conflicts:

- UV users: Try `uv pip sync --refresh` to rebuild the environment
- pip users: Try `pip install --upgrade -r requirements.txt`

For any other package management issues, please reach out to the team lead.
