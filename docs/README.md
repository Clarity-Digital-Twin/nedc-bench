# NEDC-BENCH Documentation

## Overview

Complete documentation for NEDC-BENCH - a production-ready EEG benchmarking platform with 100% parity to NEDC v6.0.0.

## Documentation Structure

### 📚 Getting Started

- [`installation.md`](installation.md) - How to install NEDC-BENCH
- [`quickstart.md`](quickstart.md) - 5-minute guide to get running

### 👤 User Guide

- [`user-guide/`](user-guide/) - Complete user documentation
  - Overview, algorithms, input/output formats, API usage

### 🔌 API Documentation

- [`api/`](api/) - REST API and WebSocket documentation
  - OpenAPI spec, endpoints, examples, Python client

### 🧑‍💻 Developer Guide

- [`developer/`](developer/) - For contributors and developers
  - Architecture, testing, code style, debugging
  - [Beta configuration](developer/beta_config.md) and [design details](developer/beta_config_design.md)
  - [2025 bug fixes](developer/bug_fixes_2025.md)

### 🧮 Algorithm Reference

- [`algorithms/`](algorithms/) - Detailed algorithm specifications
  - TAES, Epoch, Overlap, DP Alignment, IRA, metrics

### 🚀 Deployment

- [`deployment/`](deployment/) - Production deployment guides
  - Docker, Kubernetes, configuration, monitoring, scaling

### 📖 Reference

- [`reference/`](reference/) - Complete reference material
  - Configuration, CLI, API reference, glossary, FAQ, [Parity Status](reference/parity.md)

### 🔄 Migration

- [`migration/`](migration/) - Migration and upgrade guides
  - From NEDC v6.0.0, version upgrades, data format conversion

### 📦 Archive

- [`archive/`](archive/) - Historical documentation (being migrated)
  - Use the [Archive Migration Plan](developer/archive_migration_plan.md) to track what has already been folded into the main docs.
  - Legacy parity histories, bug investigations, and phased implementation notes remain here until migration is complete.

## Quick Links

- [Project README](../README.md)
- [Installation Guide](installation.md)
- [API Documentation](api/endpoints.md)
- [Algorithm Guide](algorithms/overview.md)
- [Docker Deployment](deployment/docker.md)

## Documentation Status

- Algorithms, API, developer, migration, and reference sections are complete and current.
- Deployment, installation, and quickstart guides provide practical, verified steps.

Last updated: 2025-10-10
