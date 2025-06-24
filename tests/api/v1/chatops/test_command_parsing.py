"""
Unit tests for ChatOps command parsing logic.

This module contains unit tests for the command parsing logic in the ChatOps API.
"""

from src.api.v1.chatops.router import COMMAND_PATTERN, PARAM_PATTERN


class TestCommandParsing:
    """Test suite for command parsing logic."""

    def test_command_pattern_valid_commands(self):
        """Test that COMMAND_PATTERN correctly matches valid commands."""
        test_cases = [
            ("!help", ("help", None)),
            ("!status abc123", ("status", "abc123")),
            ("!deploy auth-service", ("deploy", "auth-service")),
            (
                "!spec Create a user authentication API",
                ("spec", "Create a user authentication API"),
            ),
            ("!code Generate a Redis client", ("code", "Generate a Redis client")),
        ]

        for command, expected in test_cases:
            match = COMMAND_PATTERN.match(command)
            assert match is not None, f"Failed to match command: {command}"

            cmd_type = match.group(1).lower()
            args = match.group(2) or None

            assert (
                cmd_type == expected[0]
            ), f"Expected command type {expected[0]}, got {cmd_type}"
            assert args == expected[1], f"Expected args {expected[1]}, got {args}"

    def test_command_pattern_invalid_commands(self):
        """Test that COMMAND_PATTERN does not match invalid commands."""
        invalid_commands = [
            "help",
            " !help",
            "! help",
            "help!",
            "!",
            "",
        ]

        for command in invalid_commands:
            match = COMMAND_PATTERN.match(command)
            assert match is None, f"Should not match invalid command: {command}"

    def test_param_pattern_valid_params(self):
        """Test that PARAM_PATTERN correctly matches valid parameters."""
        test_cases = [
            ("--env=prod", ("env", "prod")),
            ("--id=abc123", ("id", "abc123")),
            ("--format=json", ("format", "json")),
            ("--priority=high", ("priority", "high")),
            ("--version=1.0.0", ("version", "1.0.0")),
        ]

        for param, expected in test_cases:
            match = PARAM_PATTERN.match(param)
            assert match is not None, f"Failed to match parameter: {param}"

            name = match.group(1)
            value = match.group(2)

            assert name == expected[0], f"Expected param name {expected[0]}, got {name}"
            assert (
                value == expected[1]
            ), f"Expected param value {expected[1]}, got {value}"

    def test_param_pattern_invalid_params(self):
        """Test that PARAM_PATTERN does not match invalid parameters."""
        invalid_params = [
            "-env=prod",
            "--env prod",
            "env=prod",
            "--env=",
            "--=prod",
            "--",
            "",
        ]

        for param in invalid_params:
            match = PARAM_PATTERN.match(param)
            assert match is None, f"Should not match invalid parameter: {param}"

    def test_param_pattern_in_command(self):
        """Test finding multiple parameters in a command string."""
        command = "!deploy auth-service --env=prod --region=us-east-1 --replicas=3"

        # Parse the command
        command_match = COMMAND_PATTERN.match(command)
        assert command_match is not None

        command_type = command_match.group(1).lower()
        command_args = command_match.group(2) or ""

        assert command_type == "deploy"
        assert "auth-service" in command_args

        # Find all parameters
        params = {}
        for param_match in PARAM_PATTERN.finditer(command_args):
            param_name = param_match.group(1)
            param_value = param_match.group(2)
            params[param_name] = param_value

        # Check that all parameters were found
        assert params == {
            "env": "prod",
            "region": "us-east-1",
            "replicas": "3",
        }

        # Clean up the command args by removing parameters
        for param in params:
            command_args = command_args.replace(
                f"--{param}={params[param]}", ""
            ).strip()

        assert (
            command_args == "auth-service"
        ), f"Expected 'auth-service', got '{command_args}'"
