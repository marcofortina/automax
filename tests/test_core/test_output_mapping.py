"""
Tests for output mapping functionality in SubStepManager.
"""

from unittest.mock import MagicMock

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.managers.substep_manager import SubStepManager


class TestOutputMapping:
    """
    Test suite for output mapping functionality.
    """

    def test_output_mapping_simple_selection(self):
        """
        Test simple field selection with output mapping.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        # Mock plugin that returns complex data
        class MockPlugin:
            def __init__(self, config):
                self.config = config

            def execute(self):
                return {
                    "data": {
                        "users": [
                            {"id": 1, "name": "Alice", "active": True},
                            {"id": 2, "name": "Bob", "active": False},
                        ]
                    }
                }

        mock_plugin_manager.get_plugin.return_value = MockPlugin

        substeps_cfg = [
            {
                "id": "1",
                "description": "Test output mapping",
                "plugin": "mock_plugin",
                "params": {},
                "output_mapping": {
                    "source": "data.users",
                    "transforms": ["filter:active==True", "map:item.name"],
                    "target": "active_user_names",
                },
            }
        ]

        manager = SubStepManager(
            cfg={},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=substeps_cfg,
        )

        result = manager.run(dry_run=False)

        assert result is True
        assert "active_user_names" in manager.context
        assert manager.context["active_user_names"] == ["Alice"]

    def test_output_mapping_backward_compatibility(self):
        """
        Test backward compatibility with output_key.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        class MockPlugin:
            def __init__(self, config):
                self.config = config

            def execute(self):
                return {"result": "success", "data": "test_data"}

        mock_plugin_manager.get_plugin.return_value = MockPlugin

        substeps_cfg = [
            {
                "id": "1",
                "description": "Test backward compatibility",
                "plugin": "mock_plugin",
                "params": {},
                "output_key": "simple_output",
            }
        ]

        manager = SubStepManager(
            cfg={},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=substeps_cfg,
        )

        result = manager.run(dry_run=False)

        assert result is True
        assert "simple_output" in manager.context
        assert manager.context["simple_output"]["result"] == "success"

    def test_output_mapping_error_handling(self):
        """
        Test error handling in output mapping.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        class MockPlugin:
            def __init__(self, config):
                self.config = config

            def execute(self):
                return {"data": "simple_data"}

        mock_plugin_manager.get_plugin.return_value = MockPlugin

        substeps_cfg = [
            {
                "id": "1",
                "description": "Test error handling",
                "plugin": "mock_plugin",
                "params": {},
                "output_mapping": {
                    "source": "nonexistent.path",
                    "transforms": ["invalid:transform"],
                    "target": "result",
                },
            }
        ]

        manager = SubStepManager(
            cfg={},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=substeps_cfg,
        )

        with pytest.raises(AutomaxError):
            manager.run(dry_run=False)

    def test_output_mapping_with_context_resolution(self):
        """
        Test output mapping with context variable resolution.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        class MockPlugin:
            def __init__(self, config):
                self.config = config

            def execute(self):
                return {
                    "items": [
                        {"name": "product1", "price": 100},
                        {"name": "product2", "price": 200},
                    ]
                }

        mock_plugin_manager.get_plugin.return_value = MockPlugin

        substeps_cfg = [
            {
                "id": "1",
                "description": "Test context resolution",
                "plugin": "mock_plugin",
                "params": {},
                "output_mapping": {
                    "source": "items",
                    "transforms": ["map:item.price", "as:list"],
                    "target": "product_prices",
                },
            }
        ]

        manager = SubStepManager(
            cfg={},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=substeps_cfg,
        )

        # Set up initial context
        manager.context["discount"] = 10

        result = manager.run(dry_run=False)

        assert result is True
        assert "product_prices" in manager.context
        assert manager.context["product_prices"] == [100, 200]
