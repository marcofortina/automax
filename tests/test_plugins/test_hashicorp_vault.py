"""
Unit tests for Hashicorp Vault plugin.
"""

from unittest.mock import Mock, patch

import pytest

from automax.core.exceptions import AutomaxError
from automax.plugins.hashicorp_vault import vault_read_secret, vault_write_secret


class TestHashicorpVaultPlugin:
    """
    Test suite for Hashicorp Vault plugin.
    """

    def setup_method(self):
        """
        Set up test fixtures.
        """
        self.mock_logger = Mock()

    @patch("automax.plugins.hashicorp_vault.hvac.Client")
    def test_vault_read_secret_success_token_auth(self, mock_client):
        """
        Test successful secret reading with token authentication.
        """
        # Mock setup
        mock_instance = Mock()
        mock_instance.is_authenticated.return_value = True
        mock_instance.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "test-user", "password": "test-pass"}}
        }
        mock_client.return_value = mock_instance

        # Execute
        result = vault_read_secret(
            vault_url="https://vault.example.com",
            secret_path="secret/data/test",
            auth_method="token",
            auth_config={"token": "test-token"},
            logger=self.mock_logger,
        )

        # Assertions
        mock_client.assert_called_once_with(url="https://vault.example.com")
        assert mock_instance.token == "test-token"
        mock_instance.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="secret/data/test", mount_point="secret"
        )
        assert result == {"username": "test-user", "password": "test-pass"}

    @patch("automax.plugins.hashicorp_vault.hvac.Client")
    def test_vault_read_secret_success_approle_auth(self, mock_client):
        """
        Test successful secret reading with AppRole authentication.
        """
        # Mock setup
        mock_instance = Mock()
        mock_instance.is_authenticated.return_value = True
        mock_instance.auth.approle.login.return_value = {
            "auth": {"client_token": "approle-token"}
        }
        mock_instance.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test-key"}}
        }
        mock_client.return_value = mock_instance

        # Execute
        result = vault_read_secret(
            vault_url="https://vault.example.com",
            secret_path="secret/data/test",
            auth_method="approle",
            auth_config={"role_id": "test-role-id", "secret_id": "test-secret-id"},
            logger=self.mock_logger,
        )

        # Assertions
        mock_instance.auth.approle.login.assert_called_once_with(
            role_id="test-role-id", secret_id="test-secret-id"
        )
        assert mock_instance.token == "approle-token"
        assert result == {"api_key": "test-key"}

    @patch("automax.plugins.hashicorp_vault.hvac.Client")
    def test_vault_read_secret_kv_v1(self, mock_client):
        """
        Test reading secret from KV v1 engine.
        """
        # Mock setup
        mock_instance = Mock()
        mock_instance.is_authenticated.return_value = True
        mock_instance.secrets.kv.v1.read_secret.return_value = {
            "data": {"password": "v1-secret"}
        }
        mock_client.return_value = mock_instance

        # Execute
        result = vault_read_secret(
            vault_url="https://vault.example.com",
            secret_path="kv/test",
            auth_method="token",
            auth_config={"token": "test-token"},
            kv_version=1,
            mount_point="kv",
        )

        # Assertions
        mock_instance.secrets.kv.v1.read_secret.assert_called_once_with(
            path="kv/test", mount_point="kv"
        )
        assert result == {"password": "v1-secret"}

    def test_vault_read_secret_missing_token(self):
        """
        Test missing token in auth_config.
        """
        with pytest.raises(AutomaxError) as exc_info:
            vault_read_secret(
                vault_url="https://vault.example.com",
                secret_path="secret/data/test",
                auth_method="token",
                auth_config={},  # Missing token
            )

        assert "Token authentication requires 'token' in auth_config" in str(
            exc_info.value
        )

    def test_vault_read_secret_missing_approle_credentials(self):
        """
        Test missing AppRole credentials.
        """
        with pytest.raises(AutomaxError) as exc_info:
            vault_read_secret(
                vault_url="https://vault.example.com",
                secret_path="secret/data/test",
                auth_method="approle",
                auth_config={"role_id": "test-role-id"},  # Missing secret_id
            )

        assert "AppRole authentication requires 'role_id' and 'secret_id'" in str(
            exc_info.value
        )

    @patch("automax.plugins.hashicorp_vault.hvac.Client")
    def test_vault_read_secret_authentication_failed(self, mock_client):
        """
        Test failed Vault authentication.
        """
        # Mock setup
        mock_instance = Mock()
        mock_instance.is_authenticated.return_value = False
        mock_client.return_value = mock_instance

        with pytest.raises(AutomaxError) as exc_info:
            vault_read_secret(
                vault_url="https://vault.example.com",
                secret_path="secret/data/test",
                auth_method="token",
                auth_config={"token": "invalid-token"},
            )

        assert "Vault authentication failed" in str(exc_info.value)

    @patch("automax.plugins.hashicorp_vault.hvac.Client")
    def test_vault_read_secret_fail_fast_false(self, mock_client):
        """
        Test read secret with fail_fast=False.
        """
        # Mock setup
        mock_instance = Mock()
        mock_instance.is_authenticated.return_value = False
        mock_client.return_value = mock_instance

        # Execute with fail_fast=False
        result = vault_read_secret(
            vault_url="https://vault.example.com",
            secret_path="secret/data/test",
            auth_method="token",
            auth_config={"token": "invalid-token"},
            fail_fast=False,
        )

        # Should return empty dict instead of raising exception
        assert result == {}

    @patch("automax.plugins.hashicorp_vault.hvac.Client")
    def test_vault_write_secret_success(self, mock_client):
        """
        Test successful secret writing.
        """
        # Mock setup
        mock_instance = Mock()
        mock_instance.is_authenticated.return_value = True
        mock_client.return_value = mock_instance

        # Execute
        result = vault_write_secret(
            vault_url="https://vault.example.com",
            secret_path="secret/data/test",
            secret_data={"password": "new-password"},
            auth_method="token",
            auth_config={"token": "test-token"},
            logger=self.mock_logger,
        )

        # Assertions
        mock_instance.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="secret/data/test",
            secret={"password": "new-password"},
            mount_point="secret",
        )
        assert result is True

    @patch("automax.plugins.hashicorp_vault.hvac.Client")
    def test_vault_write_secret_kv_v1(self, mock_client):
        """
        Test writing secret to KV v1 engine.
        """
        # Mock setup
        mock_instance = Mock()
        mock_instance.is_authenticated.return_value = True
        mock_client.return_value = mock_instance

        # Execute
        result = vault_write_secret(
            vault_url="https://vault.example.com",
            secret_path="kv/test",
            secret_data={"api_key": "test-key"},
            auth_method="token",
            auth_config={"token": "test-token"},
            kv_version=1,
            mount_point="kv",
        )

        # Assertions
        mock_instance.secrets.kv.v1.create_or_update_secret.assert_called_once_with(
            path="kv/test", secret={"api_key": "test-key"}, mount_point="kv"
        )
        assert result is True

    @patch("automax.plugins.hashicorp_vault.hvac.Client")
    def test_vault_write_secret_exception_handling(self, mock_client):
        """
        Test exception handling in write secret.
        """
        # Mock setup
        mock_instance = Mock()
        mock_instance.is_authenticated.return_value = True
        mock_instance.secrets.kv.v2.create_or_update_secret.side_effect = Exception(
            "Write failed"
        )
        mock_client.return_value = mock_instance

        # Execute with fail_fast=False
        result = vault_write_secret(
            vault_url="https://vault.example.com",
            secret_path="secret/data/test",
            secret_data={"password": "new-password"},
            auth_method="token",
            auth_config={"token": "test-token"},
            fail_fast=False,
        )

        # Should return False instead of raising exception
        assert result is False

    def test_vault_unsupported_auth_method(self):
        """
        Test unsupported authentication method.
        """
        with pytest.raises(AutomaxError) as exc_info:
            vault_read_secret(
                vault_url="https://vault.example.com",
                secret_path="secret/data/test",
                auth_method="unsupported_method",
                auth_config={},
            )

        assert "Unsupported authentication method: unsupported_method" in str(
            exc_info.value
        )
