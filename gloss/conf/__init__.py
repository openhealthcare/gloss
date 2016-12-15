import os
import sys
import pytest
import importlib
from gloss.core import settings_utils

from gloss.utils import import_from_string

IN_TEST = getattr(sys, '_called_from_test', False)


class TestSettings(object):
    DATABASE_STRING = 'sqlite:///:memory:'
    ISSUING_SOURCE = "uclh"


class BaseSetting(object):
    DEBUG = False
    DATE_FORMAT = '%d/%m/%Y'
    DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'
    SAVE_LOCATION = True
    SAVE_ERRORS = True
    PROCESS_MESSAGES = True
    HOST = "localhost"
    PORTS = [2574, 2575]
    SEND_MLLP_TO_SELF = True
    DEMOGRAPHICS_HOST = "USOAAPT"
    DEMOGRAPHICS_PORT = 8155
    USE_EXTERNAL_LOOKUP = True
    SEND_MESSAGES_CONSOLE = True
    MOCK_EXTERNAL_API = None
    MOCK_API = None

    GLOSS_SERVICE = "gloss.gloss_service.GLOSS_SERVICE"


    # if this is created we will send dummy data from the defined function
    # MOCK_API = "sites.uch.mock_api.get_mock_data"
    # MOCK_EXTERNAL_API = "sites.uch.mock_api.save_mock_patients"
    GLOSS_API_PORT = 6767
    GLOSS_API_HOST = "0.0.0.0"


class LazySettings(object):
    _cache = {}

    def get_app_settings(self):
        if IN_TEST:
            site = pytest.config.option.site

            if site:
                settings_utils.set_settings_env(site)
                return settings_utils.get_settings_mod()
            if not site:
                return object()
        else:
            return settings_utils.get_settings_mod()

    def __getattr__(self, name):
        if name in self._cache:
            return self._cache[name]

        settings = [self.get_app_settings, BaseSetting]

        if IN_TEST:
            settings.insert(0, TestSettings)

        for settings_mod in settings:
            settings_container = settings_mod()
            if hasattr(settings_container, name):
                result = getattr(settings_container, name)
                self._cache[name] = result
                return result

        if name == 'ISSUING_SOURCE':
            return name

        raise ImportError("unable to find {} in settings".format(name))

settings = LazySettings()
