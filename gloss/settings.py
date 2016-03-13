"""
Gloss settings
"""
import sys
sys.path.append('.')

if getattr(sys, '_called_from_test', None):
    DATABASE_STRING = 'sqlite:///:memory:'
else:
    DATABASE_STRING = 'sqlite:///mllpHandler.db'

PASSTHROUGH_SUBSCRIPTIONS = {}

DEBUG = False

DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'
SAVE_LOCATION = True
SAVE_ERRORS = True
PROCESS_MESSAGES = True
HOST = "localhost"
PORT = 2575

try:
    from local_settings import *
except ImportError:
    pass
