# Release Process

This document outlines the release process for NEDC-BENCH.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking API changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

### Pre-release Versions

- **0.x.y**: Pre-1.0 releases indicate the API is not yet stable
- **Alpha**: 0.1.0 - 0.3.x (early development, frequent changes)
- **Beta**: 0.4.0 - 0.9.x (feature complete, stabilizing)
- **Release Candidate**: 1.0.0-rc.1, 1.0.0-rc.2, etc.

## Current Version

**v1.0.0** - Production Stable

- Status: Production ready
- API stability: Stable
- Production ready: Yes

## Release Checklist

### 1. Pre-release

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md with release date
- [ ] Run full test suite: `make ci`
- [ ] Build documentation: `make docs`
- [ ] Review and update README if needed

### 2. Create Release

```bash
# 1. Commit version changes
git add pyproject.toml CHANGELOG.md
git commit -m "Release v0.1.0"

# 2. Create annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0

Alpha release with dual-pipeline architecture:
- NEDCAlphaWrapper for NEDC v6.0.0 integration
- Foundation for Beta pipeline implementation
- Comprehensive test suite
- API server and batch processing scripts

See CHANGELOG.md for details."

# 3. Push changes and tag
git push origin main
git push origin v0.1.0
```

### 3. GitHub Release

1. Go to GitHub releases page
1. Click "Create a new release"
1. Select the tag (e.g., v0.1.0)
1. Set release title: "v0.1.0 - Alpha Release"
1. Copy relevant section from CHANGELOG.md
1. Mark as pre-release if version \< 1.0.0
1. Publish release

### 4. Post-release

- [ ] Verify GitHub release appears correctly
- [ ] Update version in pyproject.toml to next development version (e.g., 0.2.0-dev)
- [ ] Add new \[Unreleased\] section to CHANGELOG.md
- [ ] Commit: `git commit -m "Bump version to 0.2.0-dev"`

## Version History

| Version | Date       | Status   | Notes             |
| ------- | ---------- | -------- | ----------------- |
| 0.0.1   | 2024-12-01 | Released | Initial structure |
| 0.1.0   | 2024-12-15 | Released | Alpha release     |
| 1.0.0   | 2025-09-15 | Current  | Production stable |

## Versioning Guidelines

### When to increment PATCH (0.1.0 → 0.1.1)

- Bug fixes
- Documentation updates
- Minor performance improvements
- Dependency updates (non-breaking)

### When to increment MINOR (0.1.0 → 0.2.0)

- New features
- New algorithms
- API additions (backwards compatible)
- Significant performance improvements

### When to increment MAJOR (0.x.y → 1.0.0)

- Breaking API changes
- Major architectural changes
- Removal of deprecated features
- First stable release (0.x → 1.0)

## Notes

- Keep CHANGELOG.md updated with every PR
- Tag releases match version in pyproject.toml
- All releases \< 1.0.0 are considered pre-release
- Version 1.0.0 indicates API stability and production readiness
