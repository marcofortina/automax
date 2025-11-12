"""
Tests for Google Cloud Secret Manager plugin.
"""

from unittest.mock import Mock, patch

from google.api_core import exceptions
import pytest

from automax.core.exceptions import AutomaxError
from automax.plugins.google_secret_manager import get_secret_google_secret_manager


class TestGoogleSecretManagerPlugin:
    """
    Test cases for Google Secret Manager plugin.
    """

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_get_secret_success(self, mock_client_class):
        """
        Test successful secret retrieval.
        """
        # Mock client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.payload.data = b"my-secret-value"
        mock_client.access_secret_version.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = {"project_id": "test-project", "secret_id": "my-secret"}

        result = get_secret_google_secret_manager(config)

        assert result == "my-secret-value"
        mock_client.access_secret_version.assert_called_once_with(
            request={"name": "projects/test-project/secrets/my-secret/versions/latest"}
        )

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_get_secret_with_custom_version(self, mock_client_class):
        """
        Test secret retrieval with custom version.
        """
        mock_client = Mock()
        mock_response = Mock()
        mock_response.payload.data = b"my-secret-value"
        mock_client.access_secret_version.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = {
            "project_id": "test-project",
            "secret_id": "my-secret",
            "version": "2",
        }

        result = get_secret_google_secret_manager(config)

        assert result == "my-secret-value"
        mock_client.access_secret_version.assert_called_once_with(
            request={"name": "projects/test-project/secrets/my-secret/versions/2"}
        )

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_get_secret_permission_denied_fail_fast(self, mock_client_class):
        """
        Test secret retrieval with permission denied and fail_fast=True.
        """
        mock_client = Mock()
        mock_client.access_secret_version.side_effect = exceptions.PermissionDenied(
            "Permission denied"
        )
        mock_client_class.return_value = mock_client

        config = {
            "project_id": "test-project",
            "secret_id": "my-secret",
            "fail_fast": True,
        }

        with pytest.raises(AutomaxError, match="Permission denied accessing secret"):
            get_secret_google_secret_manager(config)

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_get_secret_permission_denied_no_fail_fast(self, mock_client_class):
        """
        Test secret retrieval with permission denied and fail_fast=False.
        """
        mock_client = Mock()
        mock_client.access_secret_version.side_effect = exceptions.PermissionDenied(
            "Permission denied"
        )
        mock_client_class.return_value = mock_client

        config = {
            "project_id": "test-project",
            "secret_id": "my-secret",
            "fail_fast": False,
        }

        result = get_secret_google_secret_manager(config)
        assert result is None

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_get_secret_not_found(self, mock_client_class):
        """
        Test secret retrieval with not found error.
        """
        mock_client = Mock()
        mock_client.access_secret_version.side_effect = exceptions.NotFound(
            "Secret not found"
        )
        mock_client_class.return_value = mock_client

        config = {
            "project_id": "test-project",
            "secret_id": "my-secret",
            "fail_fast": True,
        }

        with pytest.raises(AutomaxError, match="Secret 'my-secret' not found"):
            get_secret_google_secret_manager(config)

    def test_get_secret_missing_secret_id(self):
        """
        Test secret retrieval without secret_id.
        """
        config = {"project_id": "test-project"}

        with pytest.raises(AutomaxError, match="secret_id is required"):
            get_secret_google_secret_manager(config)

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_get_secret_missing_project_id(self, mock_client_class):
        """
        Test secret retrieval without project ID.
        """
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        config = {"secret_id": "my-secret", "fail_fast": False}

        result = get_secret_google_secret_manager(config)
        assert result is None

    @patch("automax.plugins.google_secret_manager.service_account.Credentials")
    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_credentials_from_json(self, mock_client_class, mock_credentials):
        """
        Test authentication with service account JSON.
        """
        credentials_json = '{"type": "service_account", "project_id": "test-project"}'
        config = {
            "credentials_json": credentials_json,
            "project_id": "test-project",
            "secret_id": "my-secret",
        }

        get_secret_google_secret_manager(config)

        mock_credentials.from_service_account_info.assert_called_once()

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_default_credentials(self, mock_client_class):
        """
        Test authentication with default credentials.
        """
        config = {"project_id": "test-project", "secret_id": "my-secret"}

        get_secret_google_secret_manager(config)

        mock_client_class.assert_called_once_with(credentials=None)

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_get_secret_with_logger(self, mock_client_class):
        """
        Test secret retrieval with logger parameter.
        """
        mock_client = Mock()
        mock_response = Mock()
        mock_response.payload.data = b"my-secret-value"
        mock_client.access_secret_version.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = {"project_id": "test-project", "secret_id": "my-secret"}

        # Mock logger
        mock_logger = Mock()

        result = get_secret_google_secret_manager(config, logger=mock_logger)
        assert result == "my-secret-value"
