import os
import importlib


def set_settings_env(app_name):
    env_name = "sites.{}.settings".format(app_name)
    os.environ['GLOSS_APP'] = env_name


def get_settings_mod():
    settings_path = os.environ.get("GLOSS_APP")
    if not settings_path:
        raise ValueError("env variable for settings not set")
    return importlib.import_module(settings_path)
