# Automax Documentation

Welcome to the Automax documentation - your guide to enterprise automation.

## Overview

Automax is a powerful, extensible automation framework designed for enterprise workflows.
It provides a class-based plugin architecture for automating tasks across cloud providers,
on-premises systems, and custom applications.

## Quick Start

```yaml
# Basic configuration example
steps:
  - id: "1"
    description: "Check network connectivity"
    plugin: "check_tcp_connection"
    params:
      host: "api.example.com"
      port: 443
      timeout: 10
```

## Examples & Tutorials

Jumpstart your automation with our comprehensive examples:

### 🚀 Getting Started
- [Basic Examples](guides/using-examples.md#basic-examples) - Simple workflows for learning
- [Advanced Examples](guides/using-examples.md#advanced-examples) - Production-ready workflows
- [Using Examples Guide](guides/using-examples.md) - Complete usage instructions

### 🛠️ Quick Start
```bash
# Run your first example
automax run --config examples/config/config.yaml --steps basic/local-commands
```

## Key Features

- **Class-Based Plugin System**: Extensible architecture with 15+ built-in plugins
- **YAML-Driven Workflows**: Define automation steps in simple YAML files
- **Advanced Output Mapping**: Transform and filter data between steps with powerful data pipelines
- **Multi-Cloud Support**: AWS, Azure, GCP, and HashiCorp Vault integration
- **Comprehensive Testing**: Full test coverage with pytest
- **Security First**: Secure secret management and access controls
- **Validation Framework**: Schema-based configuration validation

## Getting Started

- [Browse available plugins](plugins/index.md)
- [Create a new plugin](guides/creating-plugins.md)
- [Learn templating](guides/templating.md)
- [Learn output mapping](guides/output-mapping.md)
- [API Reference](reference/api.md)

## Plugin Categories

- **Cloud Integration**: AWS Secrets Manager, Azure Key Vault, Google Secret Manager, HashiCorp Vault
- **System Operations**: Local Command, SSH Command, Network Checks
- **File Operations**: Read/Write Files, Compression, Extraction
- **Communication**: HTTP Requests, Email Notifications
- **Database**: SQL operations via ODBC

## Templating

Automax now features Jinja2 templating support for dynamic parameter resolution:

```yaml
params:
  log_path: "{{ config.log_dir }}/{{ config.environment }}/app.log"
  debug_flag: "{% if config.debug %}--verbose{% endif %}"
```
