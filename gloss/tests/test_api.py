"""
Unittests for gloss.api
"""
import json
from mock import patch, MagicMock

from gloss import models
from gloss.tests import test_messages
from gloss.tests.core import GlossTestCase
from gloss import api, message_type
from gloss.information_source import InformationSource


NOPE = '{"status": "error", "data": "We\'ve not implemented this yet - sorry"}'


class JsonApiTestCase(GlossTestCase):

    def test_wrapper_logging(self):
        with patch.object(api.app.logger, "info") as info:
            some_route = MagicMock(name="mock route")
            some_route.__name__ = "mock_route"
            some_route.return_value = {"some": "result"}
            some_fun = api.json_api("/somewhere")(some_route)
            some_fun("hello")
            self.assertTrue(info.called)
            log_call_args = info.call_args[0][0]
            self.assertIn("/somewhere", log_call_args)


@patch("gloss.api.get_information_source")
class ResultQueryTestCase(GlossTestCase):
    def test_result_query(self, get_information_source):
        get_information_source.return_value = InformationSource()
        self.session.add(self.create_patient('555-yeppers', 'uclh'))
        self.session.add(self.get_result('555-yeppers', 'uclh'))
        resp = api.result_query('555-yeppers')
        data = json.loads(resp.data)
        self.assertEqual(data["status"], 'success')
        self.assertEqual(data["hospital_number"], '555-yeppers')
        expected_message = self.get_result_dict()
        expected_message["external_identifier"] = "None.ELU"
        self.assertEqual(data["messages"]["result"][0], expected_message)

    def test_not_found(self, get_information_source):
        get_information_source.return_value = InformationSource()
        self.mock_mllp_send.return_value = test_messages.PATIENT_NOT_FOUND
        msg = '{"status": "error", "data": "We can\'t find any patients with that identifier"}'
        resp = api.result_query('not-found')
        self.assertEqual(msg, resp.data)


@patch("gloss.api.get_information_source")
class PatientQueryTestCase(GlossTestCase):
    def test_not_found(self, get_information_source):
        get_information_source.return_value = InformationSource()
        self.mock_mllp_send.return_value = test_messages.PATIENT_NOT_FOUND
        msg = '{"status": "error", "data": "We can\'t find any patients with that identifier"}'
        resp = api.patient_query('not-found')
        self.assertEqual(msg, resp.data)

    def test_found_with_a_merge(self, get_information_source):
        get_information_source.return_value = InformationSource()
        patient = self.create_patient('555-yeppers', 'uclh')
        new_patient = self.create_patient('556-yeppers', 'uclh')
        self.session.add(patient)
        self.session.add(new_patient)
        merge = self.create_subrecord_with_id(
            models.Merge, '555-yeppers', 'uclh'
        )
        merge.new_reference = new_patient.gloss_reference
        self.session.add(merge)
        resp = api.patient_query('555-yeppers')
        data = json.loads(resp.data)
        expected = {
            "new_id": '556-yeppers'
        }
        self.assertEqual(data["messages"]["duplicate_patient"], [expected])

    def test_with_allergies(self, get_information_source):
        get_information_source.return_value = InformationSource()
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
