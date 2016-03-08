"""
Gloss settings
"""
import sys
sys.path.append('.')

if getattr(sys, '_called_from_test', None):
    DATABASE_STRING = 'sqlite:///:memory:'
    COMMIT = False
else:
    DATABASE_STRING = 'sqlite:///mllpHandler.db'
    COMMIT = True

PASSTHROUGH_SUBSCRIPTIONS = {}

DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i:s'
SAVE_LOCATION = True

try:
    from local_settings import *
except:
    pass
