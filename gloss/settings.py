"""
Gloss settings
"""
import sys

DATABASE_STRING = 'sqlite:///mllpHandler.db'
PASSTHROUGH_SUBSCRIPTIONS = {}
SUBSCRIPTIONS = tuple()

DEBUG = False

DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'
SAVE_LOCATION = True
SAVE_ERRORS = True
PROCESS_MESSAGES = True
HOST = "localhost"
PORTS = [2574, 2575]

DEMOGRAPHICS_HOST = "USOAAPT"
DEMOGRAPHICS_PORT = 8155

# if this is created we will send dummy data from the defined function
MOCK_API = "gloss.sites.uch.mock_api.get_mock_data"


if getattr(sys, '_called_from_test', None):
    try:
        from test_settings import *
    except ImportError:
        pass
else:
    try:
        from local_settings import *
    except ImportError:
        pass
