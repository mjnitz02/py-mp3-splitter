from unittest import mock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests
import requests_mock  # pylint: disable=unused-import

from mp3splitter.splitter import Splitter


@pytest.fixture
def mock_request_with_retry():
    with patch.object(Splitter, "request_with_retry") as mock_method:
        mock_response = Mock()
        mock_response.json.return_value = {"title": "Test Album"}
        mock_method.return_value = mock_response
        yield mock_method


def test_get_elapsed_duration():
    duration = "2:30"
    expected_elapsed_time = 150000  # 2 minutes and 30 seconds in milliseconds
    assert Splitter.get_elapsed_duration(duration) == expected_elapsed_time


def test_get_mp3_tags():
    metadata = {"title": "Test Album", "artists": [{"name": "Test Artist"}]}
    track_info = {
        "position": "1",
        "title": "Test Track",
        "artists": [{"name": "Test Artist"}],
    }
    expected_tags = {
        "track": "1",
        "title": "Test Track",
        "artist": "Test Artist",
        "album": "Test Album",
        "albumartist": "Test Artist",
    }
    assert Splitter.get_mp3_tags(metadata, track_info) == expected_tags


def test_get_export_name(tmp_path):
    track_info = {
        "position": "1",
        "title": "Test Track",
        "artists": [{"name": "Test Artist"}],
    }
    output_path = tmp_path
    expected_export_name = tmp_path / "1 - Test Artist - Test Track.mp3"
    assert Splitter.get_export_name(track_info, output_path) == str(expected_export_name)


def test_get_metadata(mock_request_with_retry):
    splitter = Splitter()
    release_id = 12345
    expected_metadata = {"title": "Test Album"}
    assert splitter.get_metadata(release_id) == expected_metadata
    Splitter.request_with_retry.assert_called_once_with(f"https://api.discogs.com/releases/{release_id}")


@patch("mp3splitter.splitter.sleep")
def test_request_with_retry_success(mock_sleep, requests_mock):
    requests_mock.get("http://example.com/file", json={"data": "file content"})

    result = Splitter.request_with_retry("http://example.com/file")

    assert result.status_code == 200
    assert result.json() == {"data": "file content"}
    mock_sleep.assert_called_once_with(0.3)


@patch("mp3splitter.splitter.sleep")
def test_request_with_retry_retry_success(mock_sleep, requests_mock):
    requests_mock.get(
        "http://example.com/file",
        [
            {"json": {"data": "file content"}, "status_code": 500},
            {"json": {"data": "file content"}, "status_code": 200},
        ],
    )

    result = Splitter.request_with_retry("http://example.com/file")

    assert result.status_code == 200
    # Should have 1 retry of 5s sleep, and one default sleep of 0.3 on success
    mock_sleep.assert_has_calls(
        [
            mock.call(5),
            mock.call(0.3),
        ]
    )


@patch("mp3splitter.splitter.sleep")
def test_request_with_retry_timeout(mock_sleep, requests_mock):
    requests_mock.get("http://example.com/file", exc=requests.exceptions.ConnectTimeout)

    with pytest.raises(
        EnvironmentError,
        match="Failed to receive response from http://example.com/file after 3 attempts",
    ):
        Splitter.request_with_retry("http://example.com/file")

    # Assert has 3 retry sleeps of increasing time
    mock_sleep.assert_has_calls(
        [
            mock.call(5),
            mock.call(10),
            mock.call(15),
        ]
    )


@patch("mp3splitter.splitter.sleep")
def test_request_with_retry_failure(mock_sleep, requests_mock):
    requests_mock.get("http://example.com/file", json={"data": "file content"}, status_code=500)

    with pytest.raises(
        EnvironmentError,
        match="Failed to receive response from http://example.com/file after 3 attempts",
    ):
        Splitter.request_with_retry("http://example.com/file")

    # Assert has 3 retry sleeps of increasing time
    mock_sleep.assert_has_calls(
        [
            mock.call(5),
            mock.call(10),
            mock.call(15),
        ]
    )
