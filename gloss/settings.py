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
