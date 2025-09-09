# Contributing to Social Suit and Sparkr Backend

Thank you for your interest in contributing to our projects! This document provides guidelines and instructions for contributing to both the Social Suit and Sparkr Backend repositories.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Security Vulnerabilities](#security-vulnerabilities)

## Code of Conduct

We are committed to fostering an open and welcoming environment. All contributors are expected to adhere to our Code of Conduct:

- Be respectful and inclusive
- Exercise empathy and kindness
- Provide constructive feedback
- Focus on what is best for the community
- Show courtesy and respect towards other community members

## Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:

- For Social Suit (Node.js):
  - Node.js (v16+)
  - npm or yarn
  - Docker and Docker Compose (for local development)

- For Sparkr Backend (Python):
  - Python 3.9+
  - pip
  - Docker and Docker Compose (for local development)

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment following the instructions in the README.md
4. Create a new branch for your feature or bugfix

## Development Workflow

1. **Choose an issue**: Start by selecting an open issue from the issue tracker or create a new one if you've found a bug or have a feature suggestion.

2. **Create a branch**: Create a new branch with a descriptive name:
   ```
   # For features
   git checkout -b feature/your-feature-name
   
   # For bugfixes
   git checkout -b fix/issue-description
   ```

3. **Make changes**: Implement your changes, following the coding standards.

4. **Write tests**: Add tests for your changes to ensure they work as expected and prevent future regressions.

5. **Update documentation**: Update any relevant documentation, including inline code comments, README, and other markdown files.

6. **Commit your changes**: Use clear and descriptive commit messages:
   ```
   git commit -m "feat: add user authentication feature"
   git commit -m "fix: resolve issue with database connection"
   ```

7. **Push to your fork**: Push your changes to your forked repository:
   ```
   git push origin your-branch-name
   ```

8. **Create a Pull Request**: Open a pull request against the main repository.

## Pull Request Process

1. **Fill out the PR template**: Complete all sections of the pull request template.

2. **Link related issues**: Reference any related issues in your PR description using keywords like "Fixes #123" or "Relates to #456".

3. **CI checks**: Ensure all CI checks pass. Fix any issues that arise.

4. **Code review**: Address any feedback from code reviewers promptly.

5. **Approval**: PRs require approval from at least one maintainer before merging.

6. **Merge**: Once approved, a maintainer will merge your PR.

## Coding Standards

### For Social Suit (JavaScript/TypeScript)

- Follow the ESLint configuration provided in the repository
- Use TypeScript for new code
- Follow the existing code style and architecture patterns
- Use meaningful variable and function names
- Add JSDoc comments for public APIs

### For Sparkr Backend (Python)

- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Follow the existing code architecture patterns
- Use meaningful variable and function names
- Add docstrings for modules, classes, and functions

## Testing

- Write unit tests for all new functionality
- Ensure all existing tests pass before submitting a PR
- Aim for high test coverage for critical paths

### Social Suit Testing

```bash
npm test
```

### Sparkr Backend Testing

```bash
pytest
```

## Documentation

- Update README.md if you're adding or changing features
- Update API documentation for any API changes
- Add inline code comments for complex logic
- Update environment variable documentation if you're adding new configuration options

## Issue Reporting

When reporting issues, please use the issue templates provided and include:

1. A clear and descriptive title
2. Steps to reproduce the issue
3. Expected behavior
4. Actual behavior
5. Screenshots or logs (if applicable)
6. Environment information (OS, browser, etc.)

## Security Vulnerabilities

If you discover a security vulnerability, please do NOT open an issue. Instead, email [security@example.com](mailto:security@example.com) with details. We take security issues very seriously and will address them promptly.

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

Thank you for contributing to our projects! Your time and expertise help make these tools better for everyone.