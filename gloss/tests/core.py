from unittest import TestCase
from gloss.models import engine
from sqlalchemy.orm import sessionmaker


class GlossTestCase(TestCase):
    def setUp(self):
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.rollback()
