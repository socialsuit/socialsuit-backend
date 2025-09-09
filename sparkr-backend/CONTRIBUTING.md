# Contributing to Sparkr Backend

Thank you for your interest in contributing to Sparkr Backend!

Please refer to the [main CONTRIBUTING.md](../CONTRIBUTING.md) file in the root directory for detailed contribution guidelines that apply to all projects in this repository.

## Project-Specific Guidelines

### Sparkr Backend Specific Development Setup

1. Follow the setup instructions in the [README.md](./README.md)
2. Create and activate a virtual environment
3. Install dependencies with `pip install -r requirements.txt`
4. Set up environment variables as described in the README

### Testing

Run tests with:

```bash
pytest
```

For coverage reports:

```bash
pytest --cov=app tests/
```

### Code Style

This project follows PEP 8 style guidelines. Before submitting a PR, please run:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8

# Run type checking
mypy app/
```

## Getting Help

If you have questions about contributing to Sparkr Backend, feel free to open an issue with the "question" label.