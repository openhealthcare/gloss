from unittest import TestCase
from gloss.models import (
    engine, GlossolaliaReference, PatientIdentifier, InpatientEpisode,
    Subscription, Patient, Allergy
)
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date


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
        self, some_class, identifier, issuing_source="uclh", subscribed=True
    ):
        subrecord = self.create_subrecord(some_class)
        hospital_identifier = PatientIdentifier(
            identifier=identifier,
            issuing_source=issuing_source,
            gloss_reference=subrecord.gloss_reference
        )
        self.session.add(hospital_identifier)
        subscription = Subscription(
            gloss_reference=subrecord.gloss_reference,
            system=issuing_source,
        )
        self.session.add(subscription)
        return subrecord

    def get_inpatient_admission(self, identifier, issuing_source):
        inpatient_episode = self.create_subrecord_with_id(
            InpatientEpisode, identifier, issuing_source
        )

        inpatient_episode.visit_number = "940347"
        inpatient_episode.datetime_of_admission = datetime(
            2012, 10, 10, 17, 12
        )
        inpatient_episode.ward_code = "F3NU"
        inpatient_episode.room_code = "F3SR"
        inpatient_episode.bed_code = "F3SR-36"
        return inpatient_episode

    def get_allergy(self, identifier, issuing_source):
        allergy = self.create_subrecord_with_id(
            Allergy, identifier, issuing_source
        )
        allergy.name = "penicillin"
        return allergy

    def create_patient(self, identifier, issuing_source):
        patient = self.create_subrecord_with_id(
            Patient, identifier, issuing_source
        )
        patient.first_name = "Jane"
        patient.surname = "Smith"
        patient.tite = "Ms"
        patient.date_of_birth = date(1983, 12, 12)
