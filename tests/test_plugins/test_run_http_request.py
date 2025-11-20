"""
Tests for run_http_request plugin.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestRunHttpRequestPlugin:
    """
    Test suite for run_http_request plugin.
    """

    def test_run_http_request_plugin_registered(self):
        """
        Verify that run_http_request plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "run_http_request" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("run_http_request")
        assert metadata.name == "run_http_request"
        assert "http" in metadata.tags
        assert "url" in metadata.required_config

    def test_run_http_request_plugin_instantiation(self):
        """
        Verify run_http_request plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        config = {
            "url": "https://api.example.com/data",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "data": "{}",
            "timeout": 60,
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_run_http_request_plugin_configuration_validation(self):
        """
        Verify run_http_request plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({})  # missing url
        assert "required configuration" in str(exc_info.value).lower()

    @patch("requests.request")
    def test_run_http_request_plugin_execution_success(self, mock_request):
        """
        Test run_http_request plugin execution with successful request.
        """
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"message": "success"}'
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_request.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class(
            {
                "url": "https://api.example.com/data",
                "method": "GET",
                "headers": {"Authorization": "Bearer token123"},
                "timeout": 30,
            }
        )

        result = plugin.execute()

        assert result["status"] == "success"
        assert result["url"] == "https://api.example.com/data"
        assert result["method"] == "GET"
        assert result["status_code"] == 200
        assert result["content"] == '{"message": "success"}'
        assert result["elapsed"] == 0.5

        mock_request.assert_called_once_with(
            method="GET",
            url="https://api.example.com/data",
            headers={"Authorization": "Bearer token123"},
            data=None,
            params={},
            timeout=30,
            verify=True,
            auth=None,
        )

    @patch("requests.request")
    def test_run_http_request_plugin_post_request(self, mock_request):
        """
        Test run_http_request plugin execution with POST request.
        """
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"id": 123}'
        mock_response.elapsed.total_seconds.return_value = 1.2
        mock_request.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class(
            {
                "url": "https://api.example.com/users",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "data": '{"name": "John"}',
                "timeout": 10,
            }
        )

        result = plugin.execute()

        assert result["status"] == "success"
        assert result["method"] == "POST"
        assert result["status_code"] == 201
        mock_request.assert_called_once_with(
            method="POST",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            data='{"name": "John"}',
            params={},
            timeout=10,
            verify=True,
            auth=None,
        )

    @patch("requests.request")
    def test_run_http_request_plugin_with_params(self, mock_request):
        """
        Test run_http_request plugin execution with query parameters.
        """
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "response content"
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_request.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class(
            {
                "url": "https://api.example.com/search",
                "method": "GET",
                "params": {"q": "python", "page": "1"},
                "verify_ssl": False,
            }
        )

        result = plugin.execute()

        assert result["status"] == "success"
        mock_request.assert_called_once_with(
            method="GET",
            url="https://api.example.com/search",
            headers={},
            data=None,
            params={"q": "python", "page": "1"},
            timeout=30,
            verify=False,
            auth=None,
        )

    @patch("requests.request")
    def test_run_http_request_plugin_http_error(self, mock_request):
        """
        Test run_http_request plugin execution with HTTP error status.
        """
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_response.text = "Not found"
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class(
            {"url": "https://api.example.com/nonexistent", "method": "GET"}
        )

        result = plugin.execute()

        assert result["status"] == "failure"
        assert result["status_code"] == 404
        assert result["content"] == "Not found"

    @patch("requests.request")
    def test_run_http_request_plugin_request_exception(self, mock_request):
        """
        Test run_http_request plugin execution with request exception.
        """
        # Setup mocks
        mock_request.side_effect = requests.exceptions.RequestException(
            "Connection error"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class({"url": "https://api.example.com/data", "method": "GET"})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "HTTP request failed" in str(exc_info.value)


class TestRunHttpRequestErrorHandling:
    """
    Additional test suite for Run HTTP Request error scenarios.

    These tests complement the existing tests without modifying them.

    """

    @patch("requests.request")
    def test_run_http_request_plugin_connection_error(self, mock_request):
        """
        Test run_http_request plugin execution with connection error.
        """
        # Setup mock to raise connection error
        mock_request.side_effect = requests.exceptions.ConnectionError(
            "Connection error"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class(
            {"url": "https://unreachable.example.com", "method": "GET"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Connection error" in str(exc_info.value)

    @patch("requests.request")
    def test_run_http_request_plugin_timeout(self, mock_request):
        """
        Test run_http_request plugin execution with timeout.
        """
        # Setup mock to raise timeout
        mock_request.side_effect = requests.exceptions.Timeout("Request timeout")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class(
            {
                "url": "https://slow.example.com",
                "method": "GET",
                "timeout": 5,
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Request timeout" in str(exc_info.value)

    @patch("requests.request")
    def test_run_http_request_plugin_ssl_error(self, mock_request):
        """
        Test run_http_request plugin execution with SSL error.
        """
        # Setup mock to raise SSL error
        mock_request.side_effect = requests.exceptions.SSLError("SSL certificate error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class(
            {"url": "https://invalid-ssl.example.com", "method": "GET"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "SSL certificate error" in str(exc_info.value)

    @patch("requests.request")
    def test_run_http_request_plugin_invalid_url(self, mock_request):
        """
        Test run_http_request plugin execution with invalid URL.
        """
        # Setup mock to raise invalid URL error
        mock_request.side_effect = requests.exceptions.InvalidURL("Invalid URL")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class({"url": "invalid-url", "method": "GET"})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Invalid URL" in str(exc_info.value)

    @patch("requests.request")
    def test_run_http_request_plugin_too_many_redirects(self, mock_request):
        """
        Test run_http_request plugin execution with too many redirects.
        """
        # Setup mock to raise too many redirects error
        mock_request.side_effect = requests.exceptions.TooManyRedirects(
            "Too many redirects"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class(
            {"url": "https://redirect-loop.example.com", "method": "GET"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Too many redirects" in str(exc_info.value)

    @patch("requests.request")
    def test_run_http_request_plugin_chunked_encoding_error(self, mock_request):
        """
        Test run_http_request plugin execution with chunked encoding error.
        """
        # Setup mock to raise chunked encoding error
        mock_request.side_effect = requests.exceptions.ChunkedEncodingError(
            "Chunked encoding error"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("run_http_request")
        plugin = plugin_class(
            {"url": "https://chunked-error.example.com", "method": "GET"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Chunked encoding error" in str(exc_info.value)
