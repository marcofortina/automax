# Automax Documentation

Welcome to the Automax documentation - your guide to enterprise automation.

## Overview

Automax is a powerful, extensible automation platform designed for enterprise workflows.
It provides a plugin-based architecture for automating tasks across cloud providers,
on-premises systems, and custom applications.

## Quick Start

```yaml
# Basic configuration example
workflow:
  name: "deploy_application"
  steps:
    - name: "check_environment"
      plugin: "check_tcp_connection"
      config:
        host: "api.example.com"
        port: 443
```

## Key Features

- **Plugin System**: Extensible architecture with 15+ built-in plugins
- **Workflow Management**: Conditional execution and error handling
- **Multi-Cloud Support**: AWS, Azure, GCP, and HashiCorp Vault integration
- **Security First**: Secure secret management and access controls

## Getting Help

- [Create a new plugin](guides/creating-plugins.md)
- [Browse available plugins](plugins/index.md)
- [API Reference](reference/api.md)
