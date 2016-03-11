from unittest import TestCase
from gloss.models import (
    engine, GlossolaliaReference, PatientIdentifier, InpatientEpisode,
    Subscription, Patient, Allergy, InpatientLocation, Base
)
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from mock import patch


class GlossTestCase(TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine)
        self.session = Session()
        self.patch_session = patch(
            'gloss.models.get_session', return_value=self.session
        )
        self.patch_close = patch.object(self.session, 'close')
        self.patch_session.start()
        self.patch_close.start()

    def tearDown(self):
        self.patch_session.stop()
        self.patch_close.stop()
        self.session.close()
        Base.metadata.drop_all(engine)

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

    def get_inpatient_episode(self, identifier, issuing_source):
        inpatient_episode = self.create_subrecord_with_id(
            InpatientEpisode, identifier, issuing_source
        )

        inpatient_episode.visit_number = "940347"
        inpatient_episode.datetime_of_admission = datetime(
            2012, 10, 10, 17, 12
        )
        return inpatient_episode

    def get_inpatient_location(self, inpatient_episode):
        inpatient_location = InpatientLocation()
        inpatient_location.ward_code = "BBNU"
        inpatient_location.room_code = "BCOT"
        inpatient_location.bed_code = "BCOT-02B"
        inpatient_location.inpatient_episode = inpatient_episode
        return inpatient_location

    def get_allergy(self, identifier, issuing_source):
        allergy = self.create_subrecord_with_id(
            Allergy, identifier, issuing_source
        )
        allergy.allergy_type = "1"
        allergy.allergy_type_description = "Product Allergy"
        allergy.certainty_id = "CERT-1"
        allergy.certainty_description = "Definite"
        allergy.allergy_reference_name = "Penecillin"
        allergy.allergy_description = "Penecillin"
        allergy.allergen_reference_system = "UDM"
        allergy.allergen_reference = "8e75c6d8-45b7-4b40-913f-8ca1f59b5350"
        allergy.status_id = "1"
        allergy.status_description = "Active"
        allergy.diagnosis_datetime = datetime(2015, 11, 19, 9, 15)
        allergy.allergy_start_datetime = datetime(2015, 11, 19, 9, 14)
        return allergy


    def create_patient(self, identifier, issuing_source):
        patient = self.create_subrecord_with_id(
            Patient, identifier, issuing_source
        )
        patient.first_name = "Jane"
        patient.surname = "Smith"
        patient.title = "Ms"
        patient.date_of_birth = date(1983, 12, 12)
        return patient
