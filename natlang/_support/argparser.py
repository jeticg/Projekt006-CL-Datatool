import argparse
from configparser import SafeConfigParser


def processConfig(description, defaultConfig):
    """
    Process arguments

    @description: str, version info
    return: config, a dict of configurations
    """
    ap = argparse.ArgumentParser(
        description=description)
    for key in defaultConfig:
        if isinstance(defaultConfig[key], int):
            ap.add_argument("--" + key, dest=key, type=int)
        elif isinstance(defaultconfig[key], float):
            ap.add_argument("--" + key, dest=key, type=float)
        elif defaultConfig[key] is False:
            ap.add_argument("--" + key, dest=key, action="store_true")
        elif defaultConfig[key] is True:
            ap.add_argument("--" + key, dest=key, action="store_false")
        elif defaultConfig[key] is None:
            ap.add_argument("--" + key)
        else:
            ap.add_argument("--" + key, dest=key)

    # Reset default values to config file
    ap.set_defaults(**defaultConfig)
    config = defaultConfig
    args = ap.parse_args()
    config.update(vars(args))
    return config
