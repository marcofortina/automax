# Development Utilities

Automax provides a comprehensive set of command-line utilities to assist developers in validating and testing configurations, steps, and plugins. These tools are essential during development to ensure everything is correctly structured and compatible with the class-based plugin system.

## Available Utilities

### check_config.py

Validates the main configuration file for proper structure and syntax.

```bash
python utils/check_config.py --config examples/config/config.yaml
```

**Output:**
```
[INFO] Config examples/config/config.yaml is valid
```

### check_step_deps.py

Checks step dependencies and validates step configurations against the plugin registry.

```bash
python utils/check_step_deps.py --steps-dir examples/steps/ --config examples/config/config.yaml
```

**Output:**
```
[OK] Step validated: examples/steps/step2/step2.yaml
[OK] Step validated: examples/steps/step1/step1.yaml

Validation finished with 0 error(s).
```

### dry_run_validate.py

Performs a comprehensive dry-run validation of the entire workflow without executing any steps. This includes plugin discovery and registration.

```bash
python utils/dry_run_validate.py --config examples/config/config.yaml --steps 1
```

**Output:**
```
2025-11-15T13:59:30.360+01:00 [ INFO  ]  Loaded 14 plugins
2025-11-15T13:59:30.360+01:00 [ INFO  ]  Validation successful
2025-11-15T13:59:30.360+01:00 [ INFO  ]  Validate-only mode: Exiting after successful validation
[INFO] Dry-run completed with exit code 0
```

### lint_yaml.py

Validates the syntax and structure of YAML files.

```bash
python utils/lint_yaml.py --file examples/config/config.yaml
```

**Output:**
```
[INFO] examples/config/config.yaml is valid YAML
```

### validate_plugin.py

**New in class-based plugin system**: Validates individual plugin files to ensure they meet all requirements for the class-based architecture. This is essential when developing new plugins.

```bash
python utils/validate_plugin.py --plugin src/automax/plugins/aws_secrets_manager.py
```

**Output:**
```
📦 Successfully loaded plugin from: src/automax/plugins/aws_secrets_manager.py
🔍 Validating plugin: aws_secrets_manager
   Class: AwsSecretsManagerPlugin
   ✅ execute method present
   ✅ METADATA present
   ✅ name: aws_secrets_manager
   ✅ version: 2.0.0
   ✅ description: Retrieve secrets from AWS Secrets Manager
   ✅ author: Automax Team
   ✅ category: cloud
   ✅ tags: ['aws', 'secrets', 'cloud']
   ✅ required_config: ['secret_name']
   ✅ optional_config: ['region_name', 'profile_name', 'role_arn']
   ✅ SCHEMA present with 4 fields
   ✅ SCHEMA field 'secret_name': type=<class 'str'>, required=True
   ✅ SCHEMA field 'region_name': type=<class 'str'>, required=False
   ✅ SCHEMA field 'profile_name': type=<class 'str'>, required=False
   ✅ SCHEMA field 'role_arn': type=<class 'str'>, required=False
   ✅ Plugin has docstring
   ✅ Inherits from BasePlugin
   ✅ execute method has docstring

==================================================
✅ Plugin validation passed!
```

### validate_step.py

Validates a single step YAML file against the schema, plugin registry, and configuration placeholders.

```bash
python utils/validate_step.py --step-file examples/steps/step1/step1.yaml --config examples/config/config.yaml
```

**Output:**
```
[OK] examples/steps/step1/step1.yaml validated successfully
```

## Usage Notes

- Run all utilities from the project root directory
- Activate the virtual environment before execution
- Utilities work with source code directly - no installation required
- Perfect for CI/CD pipelines and development workflows
- All tools provide clear success/error messages for easy debugging

These utilities form a complete development toolkit for ensuring quality and compatibility across all aspects of Automax configurations and plugins.
