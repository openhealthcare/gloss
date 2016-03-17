"""
Gloss settings
"""
import sys

if getattr(sys, '_called_from_test', None):
    DATABASE_STRING = 'sqlite:///:memory:'
else:
    DATABASE_STRING = 'sqlite:///mllpHandler.db'
    DATABASE_STRING = 'postgresql://gloss:gloss@localhost/gloss'

PASSTHROUGH_SUBSCRIPTIONS = {}

DEBUG = False

DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'
SAVE_LOCATION = True
SAVE_ERRORS = True
PROCESS_MESSAGES = True
HOST = "localhost"
PORTS = [2574, 2575]


try:
    from local_settings import *
except ImportError:
    pass
