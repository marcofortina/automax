"""
Unit tests for Azure Key Vault plugin.
"""

from unittest.mock import Mock, patch

from azure.core.exceptions import ResourceNotFoundError
import pytest

from automax.core.exceptions import AutomaxError
from automax.plugins.azure_key_vault import azure_get_secret, azure_set_secret


class TestAzureKeyVaultPlugin:
    """
    Test suite for Azure Key Vault plugin.
    """

    def setup_method(self):
        """
        Set up test fixtures.
        """
        self.mock_logger = Mock()

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.DefaultAzureCredential")
    def test_azure_get_secret_success_default_auth(
        self, mock_credential, mock_secret_client
    ):
        """
        Test successful secret retrieval with default authentication.
        """
        # Mock setup
        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance

        mock_secret_instance = Mock()
        mock_secret_client.return_value = mock_secret_instance

        mock_secret = Mock()
        mock_secret.value = "secret-value-123"
        mock_secret_instance.get_secret.return_value = mock_secret

        # Execute
        result = azure_get_secret(
            vault_url="https://test-vault.vault.azure.net/",
            secret_name="test-secret",
            auth_method="default",
            logger=self.mock_logger,
        )

        # Assertions
        mock_credential.assert_called_once()
        mock_secret_client.assert_called_once_with(
            vault_url="https://test-vault.vault.azure.net/",
            credential=mock_credential_instance,
        )
        mock_secret_instance.get_secret.assert_called_once_with("test-secret")
        assert result == "secret-value-123"

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.ClientSecretCredential")
    def test_azure_get_secret_success_client_secret_auth(
        self, mock_credential, mock_secret_client
    ):
        """
        Test successful secret retrieval with client secret authentication.
        """
        # Mock setup
        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance

        mock_secret_instance = Mock()
        mock_secret_client.return_value = mock_secret_instance

        mock_secret = Mock()
        mock_secret.value = "client-secret-value"
        mock_secret_instance.get_secret.return_value = mock_secret

        # Execute
        result = azure_get_secret(
            vault_url="https://test-vault.vault.azure.net/",
            secret_name="test-secret",
            auth_method="client_secret",
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
        )

        # Assertions
        mock_credential.assert_called_once_with(
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
        )
        assert result == "client-secret-value"

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.DefaultAzureCredential")
    def test_azure_get_secret_resource_not_found(
        self, mock_credential, mock_secret_client
    ):
        """
        Test ResourceNotFoundError handling.
        """
        # Mock setup
        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance

        mock_secret_instance = Mock()
        mock_secret_client.return_value = mock_secret_instance
        mock_secret_instance.get_secret.side_effect = ResourceNotFoundError(
            "Secret not found"
        )

        # Execute with fail_fast=False
        result = azure_get_secret(
            vault_url="https://test-vault.vault.azure.net/",
            secret_name="non-existent-secret",
            auth_method="default",
            fail_fast=False,
        )

        # Should return empty string instead of raising exception
        assert result == ""

    def test_azure_get_secret_missing_client_secret_credentials(self):
        """
        Test missing client secret credentials.
        """
        with pytest.raises(AutomaxError) as exc_info:
            azure_get_secret(
                vault_url="https://test-vault.vault.azure.net/",
                secret_name="test-secret",
                auth_method="client_secret",
                tenant_id="test-tenant",
                client_id="test-client",
                # Missing client_secret
            )

        assert (
            "client_secret authentication requires tenant_id, client_id, and client_secret"
            in str(exc_info.value)
        )

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.DefaultAzureCredential")
    def test_azure_set_secret_success(self, mock_credential, mock_secret_client):
        """
        Test successful secret setting.
        """
        # Mock setup
        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance

        mock_secret_instance = Mock()
        mock_secret_client.return_value = mock_secret_instance

        # Execute
        result = azure_set_secret(
            vault_url="https://test-vault.vault.azure.net/",
            secret_name="new-secret",
            secret_value="new-secret-value",
            auth_method="default",
            logger=self.mock_logger,
        )

        # Assertions
        mock_secret_instance.set_secret.assert_called_once_with(
            "new-secret", "new-secret-value"
        )
        assert result is True

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.ClientSecretCredential")
    def test_azure_set_secret_client_secret_auth(
        self, mock_credential, mock_secret_client
    ):
        """
        Test secret setting with client secret authentication.
        """
        # Mock setup
        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance

        mock_secret_instance = Mock()
        mock_secret_client.return_value = mock_secret_instance

        # Execute
        result = azure_set_secret(
            vault_url="https://test-vault.vault.azure.net/",
            secret_name="new-secret",
            secret_value="new-secret-value",
            auth_method="client_secret",
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
        )

        # Assertions
        mock_credential.assert_called_once_with(
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
        )
        assert result is True

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.DefaultAzureCredential")
    def test_azure_set_secret_exception_handling(
        self, mock_credential, mock_secret_client
    ):
        """
        Test exception handling in set secret.
        """
        # Mock setup
        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance

        mock_secret_instance = Mock()
        mock_secret_client.return_value = mock_secret_instance
        mock_secret_instance.set_secret.side_effect = Exception("Set secret failed")

        # Execute with fail_fast=False
        result = azure_set_secret(
            vault_url="https://test-vault.vault.azure.net/",
            secret_name="new-secret",
            secret_value="new-secret-value",
            auth_method="default",
            fail_fast=False,
        )

        # Should return False instead of raising exception
        assert result is False

    def test_azure_unsupported_auth_method(self):
        """
        Test unsupported authentication method.
        """
        with pytest.raises(AutomaxError) as exc_info:
            azure_get_secret(
                vault_url="https://test-vault.vault.azure.net/",
                secret_name="test-secret",
                auth_method="unsupported_method",
            )

        assert "Unsupported authentication method: unsupported_method" in str(
            exc_info.value
        )
