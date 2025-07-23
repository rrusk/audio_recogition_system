"""
This module handles loading and merging configuration files for the application.
It reads settings from default and development JSON files and combines them.
"""

import json
import os.path

CONFIG_DEFAULT_FILE = "config.json"
CONFIG_DEVELOPMENT_FILE = "config-development.json"


def get_config():
    """
    Loads configuration from multiple files and returns the merged result.
    It combines a hardcoded default, the contents of config.json,
    and the contents of config-development.json.

    Returns:
        dict: A dictionary containing the merged configuration settings.
    """
    default_config = {"env": "unknown"}

    return merge_configs(
        default_config,
        parse_config(CONFIG_DEFAULT_FILE),
        parse_config(CONFIG_DEVELOPMENT_FILE),
    )


def parse_config(filename):
    """
    Parses a configuration dictionary from a specific JSON file.

    Will return an empty dictionary if the file does not exist or
    cannot be read.

    Args:
        filename (str): The path to the configuration file.

    Returns:
        dict: The configuration dictionary loaded from the file.
    """
    config = {}

    if os.path.isfile(filename):
        # file exists, open it and parse it
        try:
            with open(filename, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (IOError, json.JSONDecodeError):
            print(f"Warning: Could not read or parse config file: {filename}")

    return config


def merge_configs(*configs):
    """
    Merges multiple dictionaries into one.

    Later dictionaries in the argument list will overwrite earlier ones
    if keys conflict.

    Args:
        *configs: A variable number of dictionary objects to merge.

    Returns:
        dict: A single dictionary containing all merged key-value pairs.
    """
    merged_config = {}
    for config in configs:
        if config:
            merged_config |= config
    return merged_config
