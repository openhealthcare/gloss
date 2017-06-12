import json
from unittest import TestCase
from gloss.models import (
    engine, GlossolaliaReference, PatientIdentifier, InpatientAdmission,
    Subscription, Patient, Allergy, InpatientLocation, Base, Result
)
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from gloss.conf import settings
from mock import patch, MagicMock


class GlossTestCase(TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine)
        self.session = Session()
        self.patch_session = patch(
            'gloss.models.get_session', return_value=self.session
        )
        self.patch_session.start()
        self.patch_close = patch.object(self.session, 'close')
        self.patch_close.start()
        self.patch_requests_post = patch("requests.post")
        self.mock_requests_post = self.patch_requests_post.start()
        self.patch_socket = patch("socket.socket")
        self.mock_socket = self.patch_socket.start()

        self.patch_mllp_client = patch("hl7.client.MLLPClient")
        self.mock_mllp_client = self.patch_mllp_client.start()

        self.mock_mllp_send = MagicMock()
        client_instance = MagicMock()
        client_instance.send_message = self.mock_mllp_send;
        enter = MagicMock(return_value=client_instance)
        self.mock_mllp_client.name = "client"
        self.mllp_api_client_instance = MagicMock()
        self.mock_mllp_client.return_value = self.mllp_api_client_instance
        self.mllp_api_client_instance.__enter__ = enter

    def tearDown(self):
        self.patch_session.stop()
        self.patch_close.stop()
        self.patch_requests_post.stop()
        self.patch_socket.stop()
        self.session.close()
        self.patch_mllp_client.stop()
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

    def get_inpatient_admission(self, identifier, issuing_source):
        inpatient_admission = self.create_subrecord_with_id(
            InpatientAdmission, identifier, issuing_source
        )

        inpatient_admission.external_identifier = "940347"
        inpatient_admission.datetime_of_admission = datetime(
            2012, 10, 10, 17, 12
        )
        inpatient_admission.admission_diagnosis = "vertigo"
        return inpatient_admission

    def get_inpatient_location(self, inpatient_admission):
        inpatient_location = InpatientLocation()
        inpatient_location.ward_code = "BBNU"
        inpatient_location.room_code = "BCOT"
        inpatient_location.bed_code = "BCOT-02B"
        inpatient_location.inpatient_admission = inpatient_admission
        return inpatient_location

    def get_allergy_dict(self):
        return dict(
            allergy_type_description="Product Allergy",
            certainty_id="CERT-1",
            certainty_description="Definite",
            allergy_reference_name="Penecillin",
            allergy_description="Penecillin",
            allergen_reference_system="UDM",
            allergen_reference="8e75c6d8-45b7-4b40-913f-8ca1f59b5350",
            status_id="1",
            status_description="Active",
            diagnosis_datetime=datetime(2015, 11, 19, 9, 15),
            allergy_start_datetime=datetime(2015, 11, 19, 9, 14)
        )

    def get_allergy(self, identifier, issuing_source):
        allergy = self.create_subrecord_with_id(
            Allergy, identifier, issuing_source
        )
        allergy_dict = self.get_allergy_dict()
        for k, v in allergy_dict.iteritems():
            setattr(allergy, k, v)
        return allergy

    def get_result_dict(self):
        comments = " ".join([
            "Units: mL/min/1.73sqm Multiply eGFR by 1.21 for people of",
        ])

        observations = [
            {
                "result_status": "FINAL",
                "observation_value": "143",
                "comments": comments,
                "test_code": "NA",
                "value_type": "NM",
                "test_name": "Sodium",
                "units": "mmol/L",
                "reference_range": "135-145"
            },
            {
                "result_status": "FINAL",
                "observation_value": "3.9",
                "comments": None,
                "test_code": "K",
                "value_type": "NM",
                "test_name": "Potassium",
                "units": "mmol/L",
                "reference_range": "3.5-5.1"
            }
        ]

        return {
            "profile_code": "ELU",
            "profile_description": "RENAL PROFILE",
            "result_status": "FINAL",
            "lab_number": None,
            "last_edited": None,
            "observation_datetime": None,
            "observations": json.dumps(observations),
            "request_datetime": None
        }

    def get_result(self, identifier, issuing_source):
        result = self.create_subrecord_with_id(
            Result, identifier, issuing_source
        )
        result_dict = self.get_result_dict()
        for k, v in result_dict.iteritems():
            setattr(result, k, v)
        return result

    def create_patient(self, identifier, issuing_source):
        patient = self.create_subrecord_with_id(
            Patient, identifier, issuing_source
        )
        patient.first_name = "Jane"
        patient.surname = "Smith"
        patient.title = "Ms"
        patient.date_of_birth = date(1983, 12, 12)
        return patient
