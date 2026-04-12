"""Tests for main module."""

from unittest.mock import patch

import pytest
import core

from main import cli_args, main, parse_image_id


def test_cli_args_output_dir_default():
    """Test that the output directory defaults to the current directory."""
    args = cli_args([])

    assert args.output_dir == "."


def test_cli_args_output_dir_override():
    """Test parsing the output directory override argument."""
    args = cli_args(["--output-dir", "downloads", "--id", "123", "--zoom", "max"])

    assert args.output_dir == "downloads"


def test_cli_args_filename_pattern_default():
    """Test that the file-name pattern defaults to the core default."""
    args = cli_args([])

    assert args.filename_pattern == core.DEFAULT_FILENAME_PATTERN


def test_cli_args_filename_pattern_override():
    """Test parsing the file-name pattern override argument."""
    args = cli_args(["--filename-pattern", "{id}_{zoom}", "--id", "123", "--zoom", "max"])

    assert args.filename_pattern == "{id}_{zoom}"


def test_cli_args_no_download_flag():
    """Test parsing the no-download flag."""
    args = cli_args(["--no-download"])

    assert args.no_download is True


def test_cli_args_no_kml_flag():
    """Test parsing the no-kml flag."""
    args = cli_args(["--no-kml"])

    assert args.no_kml is True


def test_parse_image_id_rejects_non_positive_integer():
    """Test that image IDs must be positive integers."""
    with pytest.raises(ValueError, match="Image ID must be a positive integer."):
        parse_image_id(0)

    with pytest.raises(ValueError, match="Image ID must be a positive integer."):
        parse_image_id(-1)

@patch("main.console.print")
@patch("main.core.main")
@patch("builtins.input", side_effect=["0", ""])
def test_main_rejects_non_positive_interactive_id(mock_input, mock_core_main, mock_console_print):
    """Test that a non-positive interactive ID shows a specific error message."""
    main([])

    assert mock_input.call_count == 2
    mock_core_main.assert_not_called()
    mock_console_print.assert_any_call("Image ID must be a positive integer.")
    mock_console_print.assert_any_call("Try again.", style="bold red")


@patch("main.console.print")
@patch("main.core.main")
def test_main_rejects_non_positive_cli_id(mock_core_main, mock_console_print):
    """Test that a non-positive CLI ID shows a specific error without retry text."""
    main(["--id", "0", "--zoom", "max"])

    mock_core_main.assert_not_called()
    mock_console_print.assert_any_call("Image ID must be a positive integer.")
    printed_messages = [call.args[0] for call in mock_console_print.call_args_list if call.args]
    assert "Try again." not in printed_messages


@patch("main.core.main")
def test_main_passes_no_download_to_core(mock_core_main):
    """Test that the CLI passes the no-download flag into the core flow."""
    main(["--id", "123", "--zoom", "max", "--no-download"])

    _, kwargs = mock_core_main.call_args
    assert kwargs["no_download"] is True


@patch("main.core.main")
def test_main_passes_no_kml_to_core(mock_core_main):
    """Test that the CLI passes the no-kml flag into the core flow."""
    main(["--id", "123", "--zoom", "max", "--no-kml"])

    _, kwargs = mock_core_main.call_args
    assert kwargs["no_kml"] is True
