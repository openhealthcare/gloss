"""
Gloss settings
"""
import sys

DATABASE_STRING = 'sqlite:///mllpHandler.db'
PASSTHROUGH_SUBSCRIPTIONS = {}
SUBSCRIPTIONS = tuple()

DEBUG = False
SEND_MESSAGES_CONSOLE = True

DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'
SAVE_LOCATION = True
SAVE_ERRORS = True
PROCESS_MESSAGES = True
HOST = "localhost"
PORTS = [2574, 2575]

DEMOGRAPHICS_HOST = "USOAAPT"
DEMOGRAPHICS_PORT = 8155
USE_EXTERNAL_LOOKUP = True

# if this is created we will send dummy data from the defined function
# MOCK_API = "gloss.sites.uch.mock_api.get_mock_data"
MOCK_EXTERNAL_API = "gloss.sites.uch.mock_api.save_mock_patients"

GLOSS_API_PORT = 6767
GLOSS_API_HOST = "0.0.0.0"

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
