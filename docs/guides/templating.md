# Templating Guide

Automax now supports Jinja2 templing for parameter resolution, providing powerful template capabilities while maintaining full backward compatibility.

## Overview

Jinja2 integration allows you to use advanced template features in your parameter values, including:

- Variable substitution with filters
- Conditional logic
- Loops and iterations
- Complex expressions
- Custom filters (future)

## Syntax Reference

### Basic Variable Substitution

```yaml
params:
  path: "{{ config.temp_dir }}/logs"
  user: "{{ config.user }}"
  file: "{{ context.previous_output }}"
```

### Environment Variables

```yaml
params:
  home_dir: "{{ env.HOME }}"
  path_var: "{{ env.PATH }}"
```

### Filters

Jinja2 provides built-in filters for data transformation:

```yaml
params:
  upper_name: "{{ config.app_name | upper }}"
  lower_env: "{{ config.environment | lower }}"
  join_items: "{{ context.items | join(', ') }}"
```

### Conditional Logic

```yaml
params:
  debug_flag: "{% if config.environment == 'development' %}--debug{% else %}--production{% endif %}"
```

### Complex Expressions

```yaml
params:
  full_path: "{{ config.base_path }}/releases/{{ context.version }}/{{ config.app_name }}"
  formatted: "Version {{ context.major }}.{{ context.minor }}.{{ context.patch }}"
```

## Advanced Features

### Dynamic Step Configuration

Step and substep IDs and descriptions can use templates:

```yaml
id: "deploy-{{ config.environment }}"
description: "Deploy {{ config.app_name }}"
substeps:
  - id: "backup-{{ context.timestamp }}"
    description: "Backup {{ config.app_name }}"
    plugin: "local_command"
    params:
      command: "backup --app {{ config.app_name }}"
```

### Template Output Mapping

Transform output data using Jinja2 templates:

```yaml
output_mapping:
  source: "data"
  transforms:
    - "template:{{ data | selectattr('active') | map(attribute='name') | list }}"
  target: "active_users"
```

### Explicit Template Flags

Use `_is_template` suffix for explicit template rendering:

```yaml
plugin: "write_file_content"
params:
  file_path: "/opt/app/config.yaml"
  content: "Environment: {{ config.environment }}"
  content_is_template: true
```

## Backward Compatibility

The legacy placeholder syntax continues to work unchanged:

### Legacy Syntax

```yaml
params:
  path: "{temp_dir}/files"
  env_var: "$HOME"
```

### New Syntax (Recommended)

```yaml
params:
  path: "{{ config.temp_dir }}/files"
  env_var: "{{ env.HOME }}"
```

### Context Variables

The following context is available in templates:

- config: Complete configuration dictionary
- context: Step execution context (outputs from previous steps)
- env: Environment variables

## Best Practices

1. Use New Syntax: Prefer {{ config.key }} over {key} for better readability
2. Error Handling: Templates fail fast on undefined variables - ensure all variables exist
3. Complex Logic: Use filters and conditionals for data transformation instead of custom code
4. Testing: Test complex templates with sample data before deployment

## Examples

### Advanced Path Construction

```yaml
params:
  log_path: "{{ config.log_dir }}/{{ config.environment }}/app-{{ context.timestamp }}.log"
```

### Conditional Configuration

```yaml
params:
  options: "{% if config.debug %}--verbose --log-level=DEBUG{% else %}--quiet{% endif %}"
```

### Multi-value Construction

```yaml
params:
  command: "deploy.sh --env={{ config.environment }} --version={{ context.build_version }} --region={{ config.region }}"
```

## Error Handling

Template errors provide detailed information about the failure:

- Undefined variables
- Syntax errors
- Filter application errors

Always test templates with representative data to catch errors early.
