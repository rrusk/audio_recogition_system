import json
import os.path

CONFIG_DEFAULT_FILE = "config.json"
CONFIG_DEVELOPMENT_FILE = "config-development.json"


# load config from multiple files,
# and return merged result
def get_config():
    defaultConfig = {"env": "unknown"}

    return merge_configs(
        defaultConfig,
        parse_config(CONFIG_DEFAULT_FILE),
        parse_config(CONFIG_DEVELOPMENT_FILE),
    )


# parse config from specific filename
# will return empty config if file not exists, or isn't readable
def parse_config(filename):
    """
    Parse config from specific filename
    Will return empty config if file not exists, or isn't readable
    """
    config = {}

    if os.path.isfile(filename):
        # file exists, open it and parse it
        with open(filename, "r") as f:
            config = json.load(f)

    return config


# @merge multiple dicts into one
def merge_configs(*configs):
    z = {}

    for config in configs:
        z.update(config)

    return z
