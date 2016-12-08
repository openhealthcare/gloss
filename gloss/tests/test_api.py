"""
Unittests for gloss.api
"""
import json, datetime
from mock import patch, MagicMock

from gloss import models
from gloss.tests import test_messages
from gloss.tests.core import GlossTestCase
from gloss import api, settings, message_type


NOPE = '{"status": "error", "data": "We\'ve not implemented this yet - sorry"}'


class PatientQueryTestCase(GlossTestCase):
    def test_not_found(self):
        self.mock_mllp_send.return_value = test_messages.PATIENT_NOT_FOUND
        msg = '{"status": "error", "data": "We can\'t find any patients with that identifier"}'
        resp = api.patient_query('555-nope')
        self.assertEqual(msg, resp.data)

    # def test_with_patient(self):
    #     self.session.add(self.create_patient('555-yeppers', 'uclh'))
    #     resp = api.patient_query('555-yeppers')
    #     data = json.loads(resp.data)
    #
    #     demographics = [{
    #         'first_name': 'Jane',
    #         'surname': 'Smith',
    #         'middle_name': None,
    #         'title': 'Ms',
    #         'gp_practice_code': None,
    #         'post_code': None,
    #         'ethnicity': None,
    #         'sex': None,
    #         'marital_status': None,
    #         'religion': None,
    #         'death_indicator': False,
    #         'date_of_birth': '12/12/1983',
    #         'date_of_death': None,
    #     }]
    #
    #     self.assertEqual('success', data['status'])
    #     self.assertEqual(len(data['messages']), 1)
    #     self.assertEqual(demographics, data['messages']['demographics'])

    def test_with_allergies(self):
        self.session.add(self.create_patient('555-yeppers', 'uclh'))
        self.session.add(self.get_allergy('555-yeppers', 'uclh'))
        resp = api.patient_query('555-yeppers')
        data = json.loads(resp.data)
        allergies = [dict(
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


    @patch('gloss.api.get_information_source')
    def test_get_patient_information(self, get_information_source):
        information_source = MagicMock()
        information_source.patient_information.return_value = message_type.MessageContainer(
            messages=[],
            hospital_number='555-yeppers',
            issuing_source='uclh'
        )
        get_information_source.return_value = information_source
        resp = api.patient_query('555-yeppers')
        data = json.loads(resp.data)
        self.assertEqual(data["hospital_number"], '555-yeppers')


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

    @patch("gloss.api.settings")
    def test_dont_use_external_lookup(self, settings_mock):
        settings_mock.USE_EXTERNAL_LOOKUP = False

        response = api.demographics_query('50013000')
        msg = '{"status": "error", "data": "We can\'t find any patients with that identifier 50013000"}'
        self.assertFalse(self.mock_mllp_send.called)
        self.assertEqual(msg, response.data)
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
            "date_of_death": None,
            "ethnicity": "Irish",
            "death_indicator": False,
            "middle_name": None,
            "religion": None
        }
        patient = models.Patient.query_from_identifier(
            '50013000', 'uclh', self.session
        ).one()

        expected["date_of_birth"] = datetime.date(1980, 2, 15)
        for k, v in expected.iteritems():
            self.assertEqual(getattr(patient, k), v)

    def test_found_with_a_merge(self):
        patient = self.create_patient('555-yeppers', 'uclh')
        new_patient = self.create_patient('556-yeppers', 'uclh')
        self.session.add(patient)
        self.session.add(new_patient)
        merge = self.create_subrecord_with_id(
            models.Merge, '555-yeppers', 'uclh'
        )
        merge.new_reference = new_patient.gloss_reference
        self.session.add(merge)
        data = json.loads(api.demographics_query('555-yeppers').data)
        expected = {
            "new_id": '556-yeppers'
        }
        self.assertEqual(data["messages"]["duplicate_patient"], [expected])

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
            'religion': None,
            'marital_status': None,
            'death_indicator': False,
            'date_of_birth': '12/12/1983',
            'date_of_death': None,
        }]

        self.assertEqual('success', data['status'])
        self.assertEqual(demographics, data['messages']['demographics'])
        self.assertEqual(self.mock_mllp_send.call_count, 0)


class SubscribeTestCase(GlossTestCase):
    @patch("gloss.api.request")
    def test_subscription(self, mock_request):
        mock_request.form = dict(
            end_point="http://someOpalApplication/api"
        )
        resp = api.subscribe("1")
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

    @patch("gloss.api.request")
    def test_multiple_subsciptions(self, mock_request):
        mock_request.form = dict(
            end_point="http://someOpalApplication/api"
        )
        api.subscribe("1")
        api.subscribe("1")
        subscription = models.Subscription.query_from_identifier(
            "1", "uclh", self.session
        ).one()
        self.assertEqual(
            subscription.end_point, "http://someOpalApplication/api"
        )
        self.assertTrue(subscription.active)


class HL7TemplateView(GlossTestCase):
    @patch("gloss.api.render_template")
    def test_hl7_send_template_view(self, mock_render_template):
        api.hl7pretendomatic()
        self.assertTrue(mock_render_template.called)
        call_args = mock_render_template.call_args
        self.assertTrue(call_args[0], "send_hl7.html")

        for i in json.loads(call_args[1]["message"]).iterkeys():
            self.assertTrue("_" not in i)


class HL7PostApiView(GlossTestCase):
    @patch("gloss.api.request")
    def test_hl7_message_send(self, mock_request):
        mock_hl7 = """MSH|^~&amp|CARECAST|UCLH|ELCID||201412061201||ADT^A31|PLW21228462730556545|P|2.2|||AL|NE
        EVN|A31|201412061201||CREG|U440208^KHATRI^BHAVIN|
        PID|||50092915^^^^UID~^^^^NHS||TESTING MEDCHART^MEDHCART FIRSTNAME^MEDCHART JONES^^MR||19870612|M|||12 THE DUNTINGDON ROAD,&^SECOND STREET, ADDRESS&^LINE 3, FORTH^ADDRESS, LONDON^N2 9DU^^^^EAST FINCHLEY^~12 THE DUNTINGDON ROAD&SECOND STREET^ADDRESS LINE 3&FORTH ADDRESS^LONDON^^N2 9DU^^^^EAST FINCHLEY^||020811128383~07000111122~EMAI@MEDCHART.COM|02048817722|F1^^^I|M|1A|||||A||||||||
        PD1|||NU^^^^^&&^^&&|375883^CURZON^RN^^^DR^^^&&^^^^^G8903132&&~P816881^43 DERBE ROAD^ST.ANNES-ON-SEA^LANCASHIRE^^^^FY8 1NJ^^01253 725811^^^^P81688&1&~410605^PATEL^A^^^^^^^^^^^D2639749&&~V263972^234 DENTAL CARE^234 EDGEWARE ROAD^LONDON^^^^W2  1DW^^^^^^V26397&2||9||||||
        NK1|1|MEDCHART BROTHERNOK^NOK FIRST NAME^NOK SECONDNAME^^|BROTHER|65 ADDRESS ONE, ADDRESS&^TWO, NOK ADDRESS THREE,&^NOK ADDRESS FOUR,^LONDON,^N2 9DU^^^^MIDDLESEX^~65 ADDRESS ONE&ADDRESS TWO^NOK ADDRESS THREE&NOK ADDRESS FOUR^LONDON^^N2 9DU^^^^MIDDLESEX^|0809282822|0899282727|"""
        mock_request.form = dict(
            message=mock_hl7
        )
        expected_hl7 = """\rMSH|^~\\&|CARECAST|UCLH|ELCID||201412061201||ADT^A31|PLW21228462730556545|P|2.2|||AL|NE
        EVN|A31|201412061201||CREG|U440208^KHATRI^BHAVIN|
        PID|||50092915^^^^UID~^^^^NHS||TESTING MEDCHART^MEDHCART FIRSTNAME^MEDCHART JONES^^MR||19870612|M|||12 THE DUNTINGDON ROAD,&^SECOND STREET, ADDRESS&^LINE 3, FORTH^ADDRESS, LONDON^N2 9DU^^^^EAST FINCHLEY^~12 THE DUNTINGDON ROAD&SECOND STREET^ADDRESS LINE 3&FORTH ADDRESS^LONDON^^N2 9DU^^^^EAST FINCHLEY^||020811128383~07000111122~EMAI@MEDCHART.COM|02048817722|F1^^^I|M|1A|||||A||||||||
        PD1|||NU^^^^^&&^^&&|375883^CURZON^RN^^^DR^^^&&^^^^^G8903132&&~P816881^43 DERBE ROAD^ST.ANNES-ON-SEA^LANCASHIRE^^^^FY8 1NJ^^01253 725811^^^^P81688&1&~410605^PATEL^A^^^^^^^^^^^D2639749&&~V263972^234 DENTAL CARE^234 EDGEWARE ROAD^LONDON^^^^W2  1DW^^^^^^V26397&2||9||||||
        NK1|1|MEDCHART BROTHERNOK^NOK FIRST NAME^NOK SECONDNAME^^|BROTHER|65 ADDRESS ONE, ADDRESS&^TWO, NOK ADDRESS THREE,&^NOK ADDRESS FOUR,^LONDON,^N2 9DU^^^^MIDDLESEX^~65 ADDRESS ONE&ADDRESS TWO^NOK ADDRESS THREE&NOK ADDRESS FOUR^LONDON^^N2 9DU^^^^MIDDLESEX^|0809282822|0899282727|\r"""

        expected_hl7 = expected_hl7.replace("\n", "\r")

        with patch("gloss.api.MLLPClient") as mllp_client:
            mllp_client.return_value = self.mllp_api_client_instance
            api.send_mllp_to_self()
        self.mock_mllp_send.assert_called_once_with(expected_hl7)
