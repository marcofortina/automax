"""
Tests for step execution in Automax using YAML configurations.

Includes tests for StepManager, SubStepManager, and ValidationManager.

"""

from pathlib import Path
from unittest.mock import patch

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.managers.step_manager import StepManager
from automax.core.managers.substep_manager import SubStepManager
from automax.core.managers.validation_manager import ValidationManager


@pytest.fixture
def mock_yaml(tmp_path):
    """
    Create mock YAML files for step1 and step2 in a temporary directory.
    """
    step1_dir = tmp_path / "step1"
    step1_dir.mkdir()
    (step1_dir / "step1.yaml").write_text(
        """
description: "Test step 1"
substeps:
  - id: "1"
    description: "Test substep 1"
    plugin: "local_command"
    params:
      command: "echo test"
    output_key: "test_output"
  - id: "2"
    description: "Test substep 2"
    plugin: "local_command"
    params:
      command: "echo {temp_dir}"
"""
    )

    step2_dir = tmp_path / "step2"
    step2_dir.mkdir()
    (step2_dir / "step2.yaml").write_text(
        """
description: "Test step 2"
substeps:
  - id: "1"
    description: "Test substep"
    plugin: "local_command"
    retry: 2
    params:
      command: "echo test2"
"""
    )

    return tmp_path


def test_step1_success(cfg, logger, plugin_manager, mock_yaml):
    """
    Verify step1 executes successfully with dry-run using mock YAML.
    """
    cfg["steps_dir"] = str(mock_yaml)
    step_mgr = StepManager(cfg, logger, plugin_manager)
    assert step_mgr.run(step_ids=["1"], dry_run=True) is True


def test_step1_failure(cfg, logger, plugin_manager, mock_yaml, monkeypatch):
    """
    Simulate failure in plugin for step1.
    """

    # Mock plugin class that raises exception
    class MockFailingPlugin:
        def __init__(self, config):
            self.config = config

        def execute(self):
            raise Exception("Simulated failure")

    monkeypatch.setattr(plugin_manager, "get_plugin", lambda name: MockFailingPlugin)

    cfg["steps_dir"] = str(mock_yaml)
    step_mgr = StepManager(cfg, logger, plugin_manager)
    with pytest.raises(AutomaxError):
        step_mgr.run(step_ids=["1"], dry_run=False)


def test_step2_success(cfg, logger, plugin_manager, mock_yaml):
    """
    Verify step2 executes successfully with dry-run using mock YAML.
    """
    cfg["steps_dir"] = str(mock_yaml)
    step_mgr = StepManager(cfg, logger, plugin_manager)
    assert step_mgr.run(step_ids=["2"], dry_run=True) is True


def test_substep_retry_success(cfg, logger, plugin_manager, mock_yaml):
    """
    Test retry logic in SubStepManager on success after failure.
    """
    substeps_cfg = [
        {
            "id": "1",
            "description": "Retry test",
            "plugin": "local_command",
            "retry": 2,
            "params": {"command": "echo retry"},
        }
    ]
    attempt = 0

    # Mock plugin class with retry logic
    class MockRetryPlugin:
        def __init__(self, config):
            self.config = config

        def execute(self):
            nonlocal attempt
            attempt += 1
            if attempt < 2:
                raise Exception("Fail on first attempt")
            return {"status": "success", "stdout": "Success"}

    with patch.object(plugin_manager, "get_plugin", return_value=MockRetryPlugin):
        sub_mgr = SubStepManager(cfg, logger, plugin_manager, "2", substeps_cfg)
        assert sub_mgr.run(dry_run=False) is True
        assert attempt == 2  # Retried once


def test_substep_context_output(cfg, logger, plugin_manager, mock_yaml):
    """
    Test output context propagation between sub-steps.
    """
    cfg["steps_dir"] = str(mock_yaml)
    step_mgr = StepManager(cfg, logger, plugin_manager)

    # Mock plugin classes for context testing
    class MockPlugin1:
        def __init__(self, config):
            self.config = config

        def execute(self):
            return {"stdout": cfg["temp_dir"]}

    class MockPlugin2:
        def __init__(self, config):
            self.config = config

        def execute(self):
            # Verify the command contains the context value
            command = self.config.get("command", "")
            assert (
                cfg["temp_dir"] in command
            ), f"Expected {cfg['temp_dir']} in {command}"
            return {"status": "success"}

    with patch.object(
        plugin_manager, "get_plugin", side_effect=[MockPlugin1, MockPlugin2]
    ):
        assert step_mgr.run(step_ids=["1"], dry_run=False) is True


def test_validation_success(cfg, logger, plugin_manager, mock_yaml):
    """
    Test successful validation of step YAML.
    """
    cfg["steps_dir"] = str(mock_yaml)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    validator.validate_step_yaml("1")  # No exception means success


def test_validation_failure_missing_param(cfg, logger, plugin_manager, tmp_path):
    """
    Test validation failure due to missing required param.
    """
    invalid_yaml = tmp_path / "step1" / "step1.yaml"
    invalid_yaml.parent.mkdir()
    invalid_yaml.write_text(
        """
description: "Invalid step"
substeps:
  - id: "1"
    description: "Invalid substep"
    plugin: "local_command"
    params: {}  # Missing 'command'
"""
    )
    cfg["steps_dir"] = str(tmp_path)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    with pytest.raises(AutomaxError, match="Missing required param"):
        validator.validate_step_yaml("1")


def test_validation_failure_invalid_type(cfg, logger, plugin_manager, tmp_path):
    """
    Test validation failure due to invalid param type.
    """
    invalid_yaml = tmp_path / "step1" / "step1.yaml"
    invalid_yaml.parent.mkdir()
    invalid_yaml.write_text(
        """
description: "Invalid step"
substeps:
  - id: "1"
    description: "Invalid substep"
    plugin: "local_command"
    params:
      command: 123  # Should be str
"""
    )
    cfg["steps_dir"] = str(tmp_path)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    # Now that SCHEMA validation is implemented, it should raise an error for invalid type
    with pytest.raises(AutomaxError, match="Invalid type for 'command'"):
        validator.validate_step_yaml("1")


def test_validation_failure_missing_placeholder(cfg, logger, plugin_manager, tmp_path):
    """
    Test validation failure due to missing placeholder key.
    """
    invalid_yaml = tmp_path / "step1" / "step1.yaml"
    invalid_yaml.parent.mkdir()
    invalid_yaml.write_text(
        """
description: "Invalid step"
substeps:
  - id: "1"
    description: "Invalid substep"
    plugin: "local_command"
    params:
      command: "ls {missing_key}"
"""
    )
    cfg["steps_dir"] = str(tmp_path)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    with pytest.raises(AutomaxError, match="Missing config key for placeholder"):
        validator.validate_step_yaml("1")


def test_cli_args_validation_success(cfg, logger, plugin_manager, mock_yaml):
    """
    Test successful CLI args validation.
    """
    cfg["steps_dir"] = str(mock_yaml)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    validator.validate_cli_args({"1": None, "2": None})  # No exception


def test_cli_args_validation_failure(cfg, logger, plugin_manager, mock_yaml):
    """
    Test CLI args validation failure for non-existent step.
    """
    cfg["steps_dir"] = str(mock_yaml)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    with pytest.raises(AutomaxError, match="Invalid step ID 3"):
        validator.validate_cli_args({"3": None})


def test_validation_with_schema(cfg, logger, plugin_manager, tmp_path):
    """
    Test validation using SCHEMA from plugin class.
    """
    # Create a mock plugin class with SCHEMA
    from automax.plugins import PluginMetadata
    from automax.plugins.base import BasePlugin

    class MockPluginWithSchema(BasePlugin):
        METADATA = PluginMetadata(
            name="mock_plugin_with_schema",
            version="1.0.0",
            description="Test plugin with schema",
            author="Test",
            category="test",
            tags=["test"],
            required_config=["required_param"],
            optional_config=["optional_param", "multi_type_param"],
        )

        SCHEMA = {
            "required_param": {"type": str, "required": True},
            "optional_param": {"type": int, "required": False},
            "multi_type_param": {"type": (str, int), "required": False},
        }

        def execute(self):
            return {"success": True}

    # Mock the plugin manager to return our mock plugin
    original_get_plugin = plugin_manager.get_plugin
    original_list_plugins = plugin_manager.list_plugins

    def mock_get_plugin(name):
        if name == "mock_plugin_with_schema":
            return MockPluginWithSchema
        return original_get_plugin(name)

    def mock_list_plugins():
        original_plugins = original_list_plugins()
        if "mock_plugin_with_schema" not in original_plugins:
            return original_plugins + ["mock_plugin_with_schema"]
        return original_plugins

    plugin_manager.get_plugin = mock_get_plugin
    plugin_manager.list_plugins = mock_list_plugins

    try:
        # Test 1: Valid parameters
        yaml_path = tmp_path / "step1" / "step1.yaml"
        yaml_path.parent.mkdir()
        yaml_path.write_text(
            """
description: "Test step with schema"
substeps:
  - id: "1"
    description: "Test substep"
    plugin: "mock_plugin_with_schema"
    params:
      required_param: "hello"
      optional_param: 123
      multi_type_param: "string_value"
"""
        )
        cfg["steps_dir"] = str(tmp_path)
        validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
        validator.validate_step_yaml("1")  # Should pass without errors

        # Test 2: Valid parameters with integer for multi_type_param
        yaml_path.write_text(
            """
description: "Test step with schema"
substeps:
  - id: "1"
    description: "Test substep"
    plugin: "mock_plugin_with_schema"
    params:
      required_param: "hello"
      multi_type_param: 456
"""
        )
        validator.validate_step_yaml("1")  # Should pass

        # Test 3: Missing required parameter
        yaml_path.write_text(
            """
description: "Test step with schema"
substeps:
  - id: "1"
    description: "Test substep"
    plugin: "mock_plugin_with_schema"
    params:
      optional_param: 123
"""
        )
        with pytest.raises(
            AutomaxError, match="Missing required param 'required_param'"
        ):
            validator.validate_step_yaml("1")

        # Test 4: Invalid type
        yaml_path.write_text(
            """
description: "Test step with schema"
substeps:
  - id: "1"
    description: "Test substep"
    plugin: "mock_plugin_with_schema"
    params:
      required_param: "hello"
      optional_param: "should_be_int"
"""
        )
        with pytest.raises(AutomaxError, match="Invalid type for 'optional_param'"):
            validator.validate_step_yaml("1")

        # Test 5: Invalid type for multi-type parameter
        yaml_path.write_text(
            """
description: "Test step with schema"
substeps:
  - id: "1"
    description: "Test substep"
    plugin: "mock_plugin_with_schema"
    params:
      required_param: "hello"
      multi_type_param: 3.14
"""
        )
        with pytest.raises(AutomaxError, match="Invalid type for 'multi_type_param'"):
            validator.validate_step_yaml("1")

    finally:
        # Restore original methods
        plugin_manager.get_plugin = original_get_plugin
        plugin_manager.list_plugins = original_list_plugins


def test_all_plugins_have_schema_validation(cfg, logger, plugin_manager, tmp_path):
    """
    Test that all available plugins can be validated with their SCHEMA definitions.
    """
    available_plugins = plugin_manager.list_plugins()

    for plugin_name in available_plugins:
        plugin_class = plugin_manager.get_plugin(plugin_name)

        # Skip plugins that don't have SCHEMA defined yet
        if not hasattr(plugin_class, "SCHEMA") or not plugin_class.SCHEMA:
            continue

        # Verify that SCHEMA is consistent with METADATA
        metadata_required = set(plugin_class.METADATA.required_config)
        metadata_optional = set(plugin_class.METADATA.optional_config)
        schema_params = set(plugin_class.SCHEMA.keys())

        # All required parameters in METADATA should be in SCHEMA
        assert metadata_required.issubset(
            schema_params
        ), f"Plugin {plugin_name}: METADATA required parameters {metadata_required} not in SCHEMA {schema_params}"

        # Most optional parameters in METADATA should be in SCHEMA (allow some differences)
        missing_optional = metadata_optional - schema_params
        # Allow up to 3 missing optional parameters (for plugins with many options)
        assert (
            len(missing_optional) <= 3
        ), f"Plugin {plugin_name}: Too many METADATA optional parameters {missing_optional} not in SCHEMA {schema_params}"

        # All parameters in SCHEMA should be in METADATA required or optional
        all_metadata_params = metadata_required.union(metadata_optional)
        extra_schema_params = schema_params - all_metadata_params
        # Allow up to 3 extra parameters in SCHEMA (for enhanced validation)
        assert (
            len(extra_schema_params) <= 3
        ), f"Plugin {plugin_name}: Too many SCHEMA parameters {extra_schema_params} not in METADATA {all_metadata_params}"

        # Verify required parameters in SCHEMA include all METADATA required
        schema_required = {
            name
            for name, spec in plugin_class.SCHEMA.items()
            if spec.get("required", False)
        }
        assert metadata_required.issubset(
            schema_required
        ), f"Plugin {plugin_name}: METADATA required {metadata_required} not all in SCHEMA required {schema_required}"

        # Create a unique directory for each plugin to avoid conflicts
        plugin_test_dir = tmp_path / f"test_{plugin_name}"
        plugin_test_dir.mkdir(exist_ok=True)

        # Create step directory inside the plugin test directory
        step_dir = plugin_test_dir / "step1"
        step_dir.mkdir(exist_ok=True)
        yaml_path = step_dir / "step1.yaml"

        # Create test parameters based on the plugin's SCHEMA
        test_params = {}
        for param_name, param_spec in plugin_class.SCHEMA.items():
            if param_spec.get("required", False):
                # Add a dummy value for required parameters
                param_type = param_spec.get("type", str)
                if param_type == str or (
                    isinstance(param_type, tuple) and str in param_type
                ):
                    test_params[param_name] = "test_value"
                elif param_type == int or (
                    isinstance(param_type, tuple) and int in param_type
                ):
                    test_params[param_name] = 123
                elif param_type == bool or (
                    isinstance(param_type, tuple) and bool in param_type
                ):
                    test_params[param_name] = True
                elif param_type == dict or (
                    isinstance(param_type, tuple) and dict in param_type
                ):
                    test_params[param_name] = {"test": "value"}
                elif param_type == list or (
                    isinstance(param_type, tuple) and list in param_type
                ):
                    test_params[param_name] = ["test_value"]

        yaml_content = f"""
description: "Test step for {plugin_name}"
substeps:
  - id: "1"
    description: "Test {plugin_name} plugin"
    plugin: "{plugin_name}"
    params: {test_params}
"""
        yaml_path.write_text(yaml_content)

        cfg["steps_dir"] = str(plugin_test_dir)
        validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))

        # This should pass without errors for valid parameters
        validator.validate_step_yaml("1")

        # Test with missing required parameter (if any required params exist)
        required_params = [
            name
            for name, spec in plugin_class.SCHEMA.items()
            if spec.get("required", False)
        ]
        if required_params:
            # Remove one required parameter
            invalid_params = test_params.copy()
            if required_params[0] in invalid_params:
                del invalid_params[required_params[0]]

            yaml_content_invalid = f"""
description: "Test step for {plugin_name}"
substeps:
  - id: "1"
    description: "Test {plugin_name} plugin"
    plugin: "{plugin_name}"
    params: {invalid_params}
"""
            yaml_path.write_text(yaml_content_invalid)

            with pytest.raises(
                AutomaxError, match=f"Missing required param '{required_params[0]}'"
            ):
                validator.validate_step_yaml("1")


def test_all_plugins_have_schema_defined(logger, plugin_manager):
    """
    Test that all plugins have SCHEMA defined for efficient validation.
    """
    available_plugins = plugin_manager.list_plugins()

    plugins_without_schema = []
    for plugin_name in available_plugins:
        plugin_class = plugin_manager.get_plugin(plugin_name)
        if not hasattr(plugin_class, "SCHEMA") or not plugin_class.SCHEMA:
            plugins_without_schema.append(plugin_name)

    # All plugins should have SCHEMA defined
    assert (
        len(plugins_without_schema) == 0
    ), f"Plugins without SCHEMA: {plugins_without_schema}"
