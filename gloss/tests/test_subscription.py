from gloss.process_message import MessageProcessor, InpatientAdmit
from gloss.tests.core import GlossTestCase
from gloss.tests.test_messages import (
    INPATIENT_ADMISSION, read_message, PATIENT_MERGE, COMPLEX_WINPATH_RESULT,
    RESULTS_MESSAGE, INPATIENT_TRANSFER, INPATIENT_DISCHARGE, INPATIENT_AMEND,
    INPATIENT_SPELL_DELETE, INPATIENT_CANCEL_DISCHARGE
)
from gloss.models import (
    Merge, get_or_create_identifier, InpatientEpisode, get_gloss_reference,
    InpatientLocation, subscribe)
from mock import patch
from datetime import datetime


class TestInpatientAdmissionFlow(GlossTestCase):
    @patch("gloss.models.get_session")
    def test_flow(self, get_session):
        get_session.return_value = self.session
        subscribe('50099878', self.session, "uclh")
        message_processor = MessageProcessor()
        message_processor.process_message(read_message(INPATIENT_ADMISSION))
        gloss_reference = get_gloss_reference('50099878', self.session)
        self.assertTrue(gloss_reference is not None)
        admission = InpatientEpisode.get_from_gloss_reference(
            gloss_reference, self.session
        )
        self.assertEqual(
            datetime(2015, 11, 18, 17, 56), admission.datetime_of_admission
        )
        location = self.session.query(InpatientLocation).one()
        self.assertEqual(location.inpatient_episode, admission)
        self.assertEqual(location.ward_code, "BBNU")
        self.assertEqual(location.room_code, "BCOT")
        self.assertEqual(location.bed_code, "BCOT-02B")
        self.assertIsNone(location.datetime_of_transfer)


class TestInpatientDischarge(GlossTestCase):
    hospital_number = "50099886"
    visit_number = "940347"

    def setUp(self):
        self.message = read_message(INPATIENT_DISCHARGE)
        self.message_processor = MessageProcessor()
        super(TestInpatientDischarge, self).setUp()

    @patch("gloss.models.get_session")
    def test_with_existing_inpatient_episode(self, get_session):
        get_session.return_value = self.session
        old_inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        old_inpatient_episode.visit_number = self.visit_number
        old_inpatient_episode.datetime_of_discharge = None
        old_inpatient_episode.datetime_of_admission = datetime(
            2014, 11, 18, 16, 15
        )

        old_inpatient_location = self.get_inpatient_location(
            old_inpatient_episode
        )
        self.session.add(old_inpatient_episode)
        self.session.add(old_inpatient_location)
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_discharge,
            datetime(2015, 11, 18, 16, 15)
        )
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2015, 11, 18, 12, 17)
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            inpatient_location.inpatient_episode, inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "F3NU")
        self.assertEqual(inpatient_location.room_code, "F3SR")
        self.assertEqual(inpatient_location.bed_code, "F3SR-36")

    @patch("gloss.models.get_session")
    def test_without_existing_inpatient_episode(self, get_session):
        get_session.return_value = self.session
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_discharge,
            datetime(2015, 11, 18, 16, 15)
        )
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2015, 11, 18, 12, 17)
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            inpatient_location.inpatient_episode, inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "F3NU")
        self.assertEqual(inpatient_location.room_code, "F3SR")
        self.assertEqual(inpatient_location.bed_code, "F3SR-36")


class TestInpatientAmend(GlossTestCase):
    hospital_number = "50030204"
    visit_number = "930882"

    def setUp(self):
        self.message = read_message(INPATIENT_AMEND)
        self.message_processor = MessageProcessor()
        super(TestInpatientAmend, self).setUp()

    @patch("gloss.models.get_session")
    def test_with_existing_inpatient_episode(self, get_session):
        get_session.return_value = self.session
        self.inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        self.inpatient_episode.datetime_of_admission = datetime(
            2012, 10, 10, 10, 10
        )
        self.inpatient_episode.datetime_of_discharge = datetime(
            2013, 10, 10, 10, 10
        )
        self.inpatient_episode.visit_number = self.visit_number
        self.inpatient_location = self.get_inpatient_location(
            self.inpatient_episode
        )
        self.inpatient_location.ward_code = "A03"
        self.inpatient_location.room_code = "A03"
        self.inpatient_location.bed_code = "A03"
        self.session.add(self.inpatient_episode)
        self.session.add(self.inpatient_location)
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2012, 9, 19, 18, 22)
        )
        self.assertEqual(
            inpatient_episode.datetime_of_discharge,
            datetime(2012, 12, 8, 14, 30)
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            inpatient_episode, inpatient_location.inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "T03")
        self.assertEqual(inpatient_location.room_code, "T03A")
        self.assertEqual(inpatient_location.bed_code, "T03-14")

    @patch("gloss.models.get_session")
    def test_without_existing_inpatient_episode(self, get_session):
        get_session.return_value = self.session
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2012, 9, 19, 18, 22)
        )
        self.assertEqual(
            inpatient_episode.datetime_of_discharge,
            datetime(2012, 12, 8, 14, 30)
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            inpatient_episode, inpatient_location.inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "T03")
        self.assertEqual(inpatient_location.room_code, "T03A")
        self.assertEqual(inpatient_location.bed_code, "T03-14")


class TestInpatientCancelDischarge(GlossTestCase):
    hospital_number = "40716752"
    visit_number = "4449234"

    def setUp(self):
        self.message = read_message(INPATIENT_CANCEL_DISCHARGE)
        self.message_processor = MessageProcessor()
        super(TestInpatientCancelDischarge, self).setUp()

    @patch("gloss.models.get_session")
    def test_with_existing_inpatient_episode(self, get_session):
        get_session.return_value = self.session
        self.inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        self.inpatient_episode.datetime_of_admission = datetime(
            2012, 10, 10, 10, 10
        )
        self.inpatient_episode.datetime_of_discharge = datetime(
            2013, 10, 10, 10, 10
        )
        self.inpatient_location = self.get_inpatient_location(
            self.inpatient_episode
        )
        self.inpatient_location.ward_code = "A03"
        self.inpatient_location.room_code = "A03"
        self.inpatient_location.bed_code = "A03"
        self.session.add(self.inpatient_episode)
        self.session.add(self.inpatient_location)
        self.message_processor.process_message(self.message)
        inpatient_episode = self.session.query(InpatientEpisode).one()
        self.assertEqual(
            inpatient_episode.datetime_of_admission,
            datetime(2015, 11, 18, 12, 17)
        )
        self.assertIsNone(
            inpatient_episode.datetime_of_discharge,
        )
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertEqual(
            inpatient_episode, inpatient_location.inpatient_episode
        )
        self.assertEqual(inpatient_location.ward_code, "F3NU")
        self.assertEqual(inpatient_location.room_code, "F3SR")
        self.assertEqual(inpatient_location.bed_code, "F3SR-36")


class TestInpatientDeleteSpell(GlossTestCase):
    hospital_number = "40716752"
    visit_number = "4449234"

    def setUp(self):
        self.message = read_message(INPATIENT_SPELL_DELETE)
        self.message_processor = MessageProcessor()
        super(TestInpatientDeleteSpell, self).setUp()

    @patch("gloss.models.get_session")
    def test_without_existing_inpatient_episode(self, get_session):
        get_session.return_value = self.session
        self.inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        self.inpatient_episode.datetime_of_admission = datetime(
            2012, 10, 10, 10, 10
        )
        self.inpatient_episode.datetime_of_discharge = datetime(
            2013, 10, 10, 10, 10
        )
        self.inpatient_episode.visit_number = self.visit_number
        self.inpatient_location = self.get_inpatient_location(
            self.inpatient_episode
        )
        self.inpatient_location.ward_code = "A03"
        self.inpatient_location.room_code = "A03"
        self.inpatient_location.bed_code = "A03"
        self.session.add(self.inpatient_episode)
        self.session.add(self.inpatient_location)
        self.message_processor.process_message(self.message)
        num_inpatients = self.session.query(InpatientEpisode).count()
        self.assertEqual(num_inpatients, 0)
        num_locations = self.session.query(InpatientEpisode).count()
        self.assertEqual(num_locations, 0)


    @patch("gloss.models.get_session")
    def test_with(self, get_session):
        get_session.return_value = self.session
        self.message_processor.process_message(self.message)
        num_inpatients = self.session.query(InpatientEpisode).count()
        self.assertEqual(num_inpatients, 0)
        num_locations = self.session.query(InpatientEpisode).count()
        self.assertEqual(num_locations, 0)


class TestInpatientTransfer(GlossTestCase):
    hospital_number = "50099878"

    def setUp(self):
        super(TestInpatientTransfer, self).setUp()
        self.inpatient_episode = self.get_inpatient_episode(
            self.hospital_number, "uclh"
        )
        self.inpatient_episode.visit_number = '930375'
        self.inpatient_location = self.get_inpatient_location(
            self.inpatient_episode
        )
        self.message = read_message(INPATIENT_TRANSFER)
        self.message_processor = MessageProcessor()

    @patch("gloss.models.get_session")
    def test_flow_if_with_previous(self, get_session):
        get_session.return_value = self.session
        transfer_time = datetime(2012, 12, 14, 11, 0)
        self.session.add(self.inpatient_episode)
        self.session.add(self.inpatient_location)
        self.message_processor.process_message(self.message)

        # make sure we're not creating multiple episodes
        self.session.query(InpatientEpisode).one()

        # we should have 2 locations, the old and the new
        inpatient_locations = self.session.query(InpatientLocation).all()

        old_location = inpatient_locations[0]
        self.assertEqual(old_location.datetime_of_transfer, transfer_time)
        self.assertEqual(
            old_location.inpatient_episode, self.inpatient_episode
        )
        self.assertEqual(
            old_location.room_code, self.inpatient_location.room_code
        )
        self.assertEqual(
            old_location.ward_code, self.inpatient_location.ward_code
        )
        self.assertEqual(
            old_location.bed_code, self.inpatient_location.bed_code
        )

        new_location = inpatient_locations[1]
        self.assertIsNone(new_location.datetime_of_transfer)
        self.assertEqual("T06", new_location.ward_code)
        self.assertEqual("T06A", new_location.room_code)
        self.assertEqual("T06-04", new_location.bed_code)

    @patch("gloss.models.get_session")
    def test_flow_if_no_previous(self, get_session):
        get_session.return_value = self.session
        self.message_processor.process_message(self.message)
        self.session.query(InpatientEpisode).one()
        inpatient_location = self.session.query(InpatientLocation).one()
        self.assertIsNone(inpatient_location.datetime_of_transfer)
        self.assertEqual("T06", inpatient_location.ward_code)
        self.assertEqual("T06A", inpatient_location.room_code)
        self.assertEqual("T06-04", inpatient_location.bed_code)


class TestMergeFlow(GlossTestCase):
    @patch("gloss.models.get_session")
    def test_complete_flow(self, get_session):
        get_session.return_value = self.session
        old_hospital_id = "50028000"
        old_gloss_reference = get_or_create_identifier(
            hospital_number=old_hospital_id,
            session=self.session,
            issuing_source="uclh"
        )
        message_processor = MessageProcessor()
        message_processor.process_message(read_message(PATIENT_MERGE))
        session = self.session
        result = session.query(Merge).one()
        old_gloss_id = result.old_reference_id
        self.assertEqual(old_gloss_reference.id, old_gloss_id)


class TestResultsFlow(GlossTestCase):
    """
        currently a shell of a test that makes sure we get no errors
        from repeating fields
    """
    @patch("gloss.models.get_session")
    def test_complex_message(self, get_session):
        get_session.return_value = self.session
        message_processor = MessageProcessor()
        message_processor.process_message(read_message(COMPLEX_WINPATH_RESULT))

    @patch("gloss.models.get_session")
    def test_message_with_notes(self, get_session):
        get_session.return_value = self.session
        message_processor = MessageProcessor()
        message_processor.process_message(read_message(RESULTS_MESSAGE))
