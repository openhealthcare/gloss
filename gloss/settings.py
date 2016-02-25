from sqlalchemy import create_engine
import sys

if getattr(sys, '_called_from_test'):
    engine = create_engine('sqlite:///:memory:')
else:
    engine = create_engine('sqlite:///mllpHandler.db')
