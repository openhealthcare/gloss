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

try:
    from local_settings import *
except:
    pass
