from unittest import TestCase
from gloss.models import engine, GlossolaliaReference, PatientIdentifier
from sqlalchemy.orm import sessionmaker


class GlossTestCase(TestCase):
    def setUp(self):
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.rollback()

    def create_subrecord(self, some_class):
        gloss_ref = GlossolaliaReference()
        self.session.add(gloss_ref)
        return some_class(gloss_reference=gloss_ref)

    def create_subrecord_with_id(
        self, some_class, identifier, issuing_source="uclh"
    ):
        subrecord = self.create_subrecord(some_class)
        hospital_identifier = PatientIdentifier(
            identifier=identifier,
            issuing_source="uclh",
            gloss_reference=subrecord.gloss_reference
        )
        self.session.add(hospital_identifier)
        return subrecord
