"""
Unittests for gloss.api
"""
import json, datetime
from mock import patch

from gloss import models
from gloss.tests import test_messages
from gloss.tests.core import GlossTestCase
from gloss import api, settings


NOPE = '{"status": "error", "data": "We\'ve not implemented this yet - sorry"}'


class PatientQueryTestCase(GlossTestCase):
    def test_not_found(self):
        self.mock_mllp_send.return_value = test_messages.PATIENT_NOT_FOUND
        msg = '{"status": "error", "data": "We can\'t find any patients with that identifier"}'
        resp = api.patient_query('555-nope')
        self.assertEqual(msg, resp.data)

    def test_with_patient(self):
        self.session.add(self.create_patient('555-yeppers', 'uclh'))
        resp = api.patient_query('555-yeppers')
        data = json.loads(resp.data)

        demographics = [{
            'first_name': 'Jane',
            'surname': 'Smith',
            'middle_name': None,
            'title': 'Ms',
            'gp_practice_code': None,
            'post_code': None,
            'ethnicity': None,
            'sex': None,
            'marital_status': None,
            'death_indicator': False,
            'date_of_birth': '12/12/1983',
            'date_of_death': None,
        }]

        self.assertEqual('success', data['status'])
        self.assertEqual(len(data['messages']), 1)
        self.assertEqual(demographics, data['messages']['demographics'])

    def test_with_allergies(self):
        self.session.add(self.create_patient('555-yeppers', 'uclh'))
        self.session.add(self.get_allergy('555-yeppers', 'uclh'))
        resp = api.patient_query('555-yeppers')
        data = json.loads(resp.data)
        allergies = [dict(
            allergy_type="1",
            allergy_type_description="Product Allergy",
            certainty_id="CERT-1",
            certainty_description="Definite",
            allergy_reference_name="Penecillin",
            allergy_description="Penecillin",
            allergen_reference_system="UDM",
            allergen_reference="8e75c6d8-45b7-4b40-913f-8ca1f59b5350",
            status_id="1",
            status_description="Active",
            diagnosis_datetime="19/11/2015 09:15:00",
            allergy_start_datetime="19/11/2015 09:14:00",
            no_allergies=False
        )]

        self.assertEqual('success', data['status'])
        self.assertEqual(len(data['messages']), 2)
        self.assertEqual(allergies, data['messages']['allergies'])
        self.assertNotIn("results", data["messages"])


    @patch("gloss.api.post_message_for_identifier")
    def test_remote_get_demographics(self, post_message):
        self.session.add(self.get_allergy('555-yeppers', 'uclh'))
        patient = self.create_patient('555-yeppers', 'uclh')
        post_message.side_effect = lambda x: self.session.add(patient)
        resp = api.patient_query('555-yeppers')
        data = json.loads(resp.data)
        allergies = [dict(
            allergy_type="1",
            allergy_type_description="Product Allergy",
            certainty_id="CERT-1",
            certainty_description="Definite",
            allergy_reference_name="Penecillin",
            allergy_description="Penecillin",
            allergen_reference_system="UDM",
            allergen_reference="8e75c6d8-45b7-4b40-913f-8ca1f59b5350",
            status_id="1",
            status_description="Active",
            diagnosis_datetime="19/11/2015 09:15:00",
            allergy_start_datetime="19/11/2015 09:14:00",
            no_allergies=False
        )]

        demographics = [{
            'first_name': 'Jane',
            'surname': 'Smith',
            'middle_name': None,
            'title': 'Ms',
            'gp_practice_code': None,
            'post_code': None,
            'ethnicity': None,
            'sex': None,
            'marital_status': None,
            'death_indicator': False,
            'date_of_birth': '12/12/1983',
            'date_of_death': None,
        }]

        self.assertEqual('success', data['status'])
        self.assertEqual(len(data['messages']), 2)
        self.assertEqual(allergies, data['messages']['allergies'])
        self.assertEqual(demographics, data['messages']['demographics'])
        self.assertNotIn("results", data["messages"])


class DemographicsCreateTestCase(GlossTestCase):
    def test_unimplemented(self):
        resp = api.demographics_create()
        self.assertEqual(NOPE, resp.data)


class DemographicsQueryTestCase(GlossTestCase):
    def test_not_found(self):
        self.mock_mllp_send.return_value = test_messages.PATIENT_NOT_FOUND
        msg = '{"status": "error", "data": "We can\'t find any patients with that identifier"}'
        resp = api.demographics_query('555-nope')
        self.assertEqual(msg, resp.data)
        self.assertEqual(self.session.query(models.Patient).count(), 0)

    def test_found_on_api(self):
        self.mock_mllp_send.return_value = test_messages.PATIENT_QUERY_RESPONSE
        resp = json.loads(api.demographics_query('50013000').data)
        self.assertEqual(self.session.query(models.Patient).count(), 1)

        self.mock_mllp_client.assert_called_once_with(
            settings.DEMOGRAPHICS_HOST,
            settings.DEMOGRAPHICS_PORT
        )

        call_args = self.mock_mllp_send.call_args[0][0]
        self.assertEqual(call_args[0][0][0], 'MSH')
        self.assertEqual(call_args[0][3][0], 'elcid')
        self.assertEqual(call_args[0][4][0], 'UCLH')
        self.assertEqual(call_args[0][5][0], 'Unicare')
        self.assertEqual(call_args[0][6][0], 'UCLH')
        self.assertEqual(call_args[0][9][0], 'QRY^A19')
        self.assertEqual(call_args[0][10][0], 'ELC00000000000000001')
        self.assertEqual(call_args[0][12][0], '2.4')
        self.assertEqual(call_args[1][0][0], 'QRD')
        self.assertEqual(call_args[1][2][0], 'R')
        self.assertEqual(call_args[1][3][0], 'I')
        self.assertEqual(call_args[1][4][0], 'ELC00000000000000001')
        self.assertEqual(call_args[1][7][0][0], '1^RD')
        self.assertEqual(call_args[1][8][0][0], '50013000')
        self.assertEqual(call_args[1][9][0], 'DEM')

        expected = {
            "first_name": "TESTFIRSTNAME",
            "post_code": "EN7 6AR",
            "surname": "TESTSURNAME",
            "gp_practice_code": "F83043",
            "title": "MR",
            "marital_status": "Single",
            "sex": "Male",
            "date_of_birth": "15/02/1980",
            "ethnicity": "Irish"
        }
        self.assertEqual(resp["messages"]["demographics"][0], expected)
        patient = models.Patient.query_from_identifier(
            '50013000', 'uclh', self.session
        ).one()

        expected["date_of_birth"] = datetime.date(1980, 2, 15)
        for k, v in expected.iteritems():
            self.assertEqual(getattr(patient, k), v)

    def test_with_patient(self):
        self.session.add(self.create_patient('555-yeppers', 'uclh'))

        resp = api.demographics_query('555-yeppers')
        data = json.loads(resp.data)

        demographics = [{
            'first_name': 'Jane',
            'surname': 'Smith',
            'middle_name': None,
            'title': 'Ms',
            'gp_practice_code': None,
            'post_code': None,
            'ethnicity': None,
            'sex': None,
            'marital_status': None,
            'death_indicator': False,
            'date_of_birth': '12/12/1983',
            'date_of_death': None,
        }]

        self.assertEqual('success', data['status'])
        self.assertEqual(demographics, data['messages']['demographics'])
        self.assertEqual(self.mock_mllp_send.call_count, 0)


class SubscribeTestCase(GlossTestCase):
    def test_subscription(self):
        resp = api.subscribe(
            "1", "http://someOpalApplication/api"
        )
        subscription = models.Subscription.query_from_identifier(
            "1", "uclh", self.session
        ).one()
        self.assertEqual(
            subscription.end_point, "http://someOpalApplication/api"
        )
        self.assertTrue(subscription.active)
        self.assertTrue(json.loads(resp.data)["status"], "success")

        resp = api.unsubscribe("1")

        subscription = models.Subscription.query_from_identifier(
            "1", "uclh", self.session
        ).one()
        self.assertEqual(
            subscription.end_point, "http://someOpalApplication/api"
        )
        self.assertFalse(subscription.active)
        self.assertTrue(json.loads(resp.data)["status"], "success")

    def test_unsubscribe_when_no_subscription(self):
        self.assertEqual(0, self.session.query(models.Subscription).count())
        resp = api.unsubscribe("1")
        self.assertTrue(json.loads(resp.data)["status"], "success")
        self.assertEqual(0, self.session.query(models.Subscription).count())

    def test_multiple_subsciptions(self):
        api.subscribe(
            "1", "http://someOpalApplication/api"
        )
        api.subscribe(
            "1", "http://someOpalApplication/api"
        )
        subscription = models.Subscription.query_from_identifier(
            "1", "uclh", self.session
        ).one()
        self.assertEqual(
            subscription.end_point, "http://someOpalApplication/api"
        )
        self.assertTrue(subscription.active)
