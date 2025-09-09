# Versioning Strategy for Shared Utils

This document outlines the versioning strategy for the shared utilities package used by both Social Suit and Sparkr projects.

## Semantic Versioning

The shared package follows [Semantic Versioning 2.0.0](https://semver.org/) with version numbers in the format of `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incremented for incompatible API changes that require updates to consuming applications
- **MINOR**: Incremented for new functionality added in a backward-compatible manner
- **PATCH**: Incremented for backward-compatible bug fixes

## Git Tags

Each release is tagged in the git repository using the format `v{MAJOR}.{MINOR}.{PATCH}` (e.g., `v0.1.0`, `v1.0.0`).

### Creating a New Release

1. Update version in both `setup.py` and `pyproject.toml`
2. Update the `CHANGELOG.md` with details of changes
3. Commit the changes with a message like "Bump version to X.Y.Z"
4. Create and push a git tag:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

## Application Integration

### Pinning Versions

Applications should pin to specific versions of the shared package to ensure stability:

#### In requirements.txt

```
shared-utils==0.1.0
```

#### In pyproject.toml

```toml
dependencies = [
    "shared-utils==0.1.0",
]
```

### Version Upgrade Process

1. Review the CHANGELOG.md to understand changes in the new version
2. Update the pinned version in your application's dependency specifications
3. Run tests to verify compatibility
4. If breaking changes are present, update application code as needed

## Deprecation Policy

- Features will be marked as deprecated before removal
- Deprecated features will remain for at least one MINOR version before removal
- MAJOR version bumps may remove previously deprecated features

## Backward Compatibility

- MINOR and PATCH releases must maintain backward compatibility
- Shim modules will be maintained for backward compatibility during transition periods
- Deprecation warnings will guide developers to updated APIs