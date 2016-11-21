import mock
from gloss.tests.core import GlossTestCase
from gloss.tests import test_messages
from gloss.importers import hl7_importer
from gloss import message_type as messages


class BasicImportTestCase(object):
    hl7_message = None
    gloss_message = None

    def setUp(self):
        super(BasicImportTestCase, self).setUp()
        service = mock.MagicMock()
        service.issuing_source = "uclh"
        self.importer = hl7_importer.HL7Importer()
        self.result = self.importer.import_message(
            test_messages.read_message(self.hl7_message),
            service
        )

    def test_correct_message_type(self):
        """ super basic sanity check that makes sure that the
            message is processed and converted to the correct class
        """
        self.assertIsInstance(self.result, messages.MessageContainer)
        self.assertIsInstance(self.result.messages, list)
        self.assertTrue(isinstance(self.result.messages[0], self.gloss_message))


class TestPatientMerge(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.PATIENT_MERGE
    gloss_message = messages.PatientMergeMessage


class TestPatientUpdate(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.PATIENT_UPDATE
    gloss_message = messages.PatientMessage


class TestInpatientAdmit(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.INPATIENT_ADMISSION
    gloss_message = messages.InpatientAdmissionMessage


class TestInpatientDischarge(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.INPATIENT_DISCHARGE
    gloss_message = messages.InpatientAdmissionMessage


class TestInpatientAmend(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.INPATIENT_AMEND
    gloss_message = messages.InpatientAdmissionMessage


class TestInpatientCancelDischarge(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.INPATIENT_CANCEL_DISCHARGE
    gloss_message = messages.InpatientAdmissionMessage


class TestInpatientTransfer(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.INPATIENT_TRANSFER
    gloss_message = messages.InpatientAdmissionTransferMessage


class TestInpatientSpellDelete(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.INPATIENT_SPELL_DELETE
    gloss_message = messages.InpatientAdmissionDeleteMessage


class TestAllergy(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.ALLERGY
    gloss_message = messages.AllergyMessage


class TestWinPathResults(BasicImportTestCase, GlossTestCase):
    hl7_message = test_messages.RESULTS_MESSAGE
    gloss_message = messages.ResultMessage
