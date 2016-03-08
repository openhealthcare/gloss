from gloss.message_segments import *
from gloss import notification
from utils import itersubclasses
from message_type import (
    InpatientEpisodeMessage, PatientMergeMessage, ResultMessage,
    InpatientEpisodeTransferMessage
)
import logging
from collections import defaultdict


from gloss.models import (
    save_identifier, InpatientEpisode,
    get_or_create_identifier, PatientIdentifier, get_gloss_reference,
    Allergy, Result
)


def get_inpatient_message(pid, pv1):
    return InpatientEpisodeMessage(
        pv1.datetime_of_admission,
        pv1.ward_code,
        pv1.room_code,
        pv1.bed_code,
        pid.patient_account_number,
        hospital_identifier=pid.hospital_number,
        issuing_source="uclh",
        datetime_of_discharge=pv1.datetime_of_discharge,
    )


def process_demographics(pid, session):
    """ saves a gloss id to hospital number and then goes and fetches demogrphics
    """
    # save a reference to the pid and the hospital id in the db, then go fetch demographics
    fetch_demographics(pid)
    return save_identifier(pid, session)


# stubbed method that will make the async call to the demographics query
# service
def fetch_demographics(pid): pass


class MessageImporter(object):
    def process(self):
        msgs = self.process_message()
        notification.notify(msgs)

    def process_message(self, session=None):
        pass


class PatientMerge(MessageImporter, HL7Message):
    message_type = u"ADT"
    trigger_event = u"A34"

    segments = (
        MSH, InpatientPID, MRG
    )

    def process_message(self, session=None):
        return [PatientMergeMessage(
            old_id=self.mrg.duplicate_hospital_number,
            hospital_number=self.pid.hospital_number,
            issuing_source="uclh"
        )]


class PatientUpdate(MessageImporter):
    message_type = u"ADT"
    trigger_event = u"A31"
    sending_application = "CARECAST"

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))

    def process_message(self, session):
        # if we have no gloss reference we won't be interested
        # if we are, punt the gloss reference down stream
        # and go and fetch the details
        gloss_reference = get_gloss_reference(
            self.pid.hospital_number, session, "uclh"
        )

        if gloss_reference:
            pass
            # notification.notify(gloss_reference, SubscriptionTypes.PATIENT_IDENTIFIER)


class InpatientAdmit(MessageImporter, HL7Message):
    message_type = u"ADT"
    trigger_event = u"A01"
    segments = (EVN, InpatientPID, PV1,)

    def process_message(self):
        return [InpatientEpisodeMessage(
            datetime_of_admission=self.pv1.datetime_of_admission,
            ward_code=self.pv1.ward_code,
            room_code=self.pv1.room_code,
            bed_code=self.pv1.bed_code,
            visit_number=self.pid.patient_account_number,
            hospital_number=self.pid.hospital_number,
            issuing_source="uclh",
            datetime_of_discharge=self.pv1.datetime_of_discharge,
        )]


class InpatientDischarge(InpatientAdmit):
    message_type = u"ADT"
    trigger_event = "A03"


class InpatientAmend(InpatientAdmit):
    message_type = "ADT"
    trigger_event = "A08"


class InpatientCancelDischarge(InpatientAdmit):
    message_type = "ADT"
    trigger_event = "A13"


class InpatientTransfer(MessageImporter, HL7Message):
    # currently untested and incomplete
    # pending us being given an example message
    message_type = "ADT"
    trigger_event = "A02"
    segments = (EVN, InpatientPID, PV1,)

    def process_message(self):
        message = InpatientEpisodeTransferMessage(
            datetime_of_admission=self.pv1.datetime_of_admission,
            ward_code=self.pv1.ward_code,
            room_code=self.pv1.room_code,
            bed_code=self.pv1.bed_code,
            visit_number=self.pid.patient_account_number,
            hospital_number=self.pid.hospital_number,
            issuing_source="uclh",
            datetime_of_discharge=self.pv1.datetime_of_discharge,
            datetime_of_transfer=self.evn.planned_datetime,
        )
        return [message]


class InpatientSpellDelete(MessageImporter, HL7Message):
    message_type = "ADT"
    trigger_event = "A07"
    segments = (EVN, InpatientPID, PV1,)

    def process_message(self, session):
        hospital_number = self.pid.hospital_number
        query = InpatientEpisode.query_from_identifier(
            hospital_number,
            issuing_source="uclh",
            session=session
        )
        query = query.filter(
            InpatientEpisode.visit_number == self.pid.patient_account_number
        )
        inpatient_episode = query.one_or_none()
        if inpatient_episode:
            # I think what we actually want to do is store a deleted field
            # that way we can pass the object nicely down stream
            inpatient_episode.datetime_of_deletion = self.evn.recorded_datetime
            session.add(inpatient_episode)
            # notification.notify(self.msh.sending_application, inpatient_episode)


class AllergyMessage(MessageImporter):
    message_type = "ADT"
    trigger_event = "A31"
    sending_application = "ePMA"

    @property
    def pid(self):
        return AllergiesPID(self.raw_msg.segment("PID"))

    @property
    def al1(self):
        try:
            return AL1(self.raw_msg.segment("AL1"))
        except KeyError:
            return None

    def process_message(self):
        if self.al1:
            Allergy(
                allergy_type=self.al1.allergy_type,
                allergy_type_description=self.al1.allergy_type_description,
                certainty_id=self.al1.certainty_id,
                certainty_description=self.al1.certainty_description,
                allergy_reference_name=self.al1.allergy_reference_name,
                allergy_description=self.al1.allergy_description,
                allergen_reference_system=self.al1.allergen_reference_system,
                allergen_reference=self.al1.allergen_reference,
                status_id=self.al1.status_id,
                status_description=self.al1.status_description,
                diagnosis_datetime=self.al1.diagnosis_datetime,
                allergy_start_datetime=self.al1.allergy_start_datetime
            )
        else:
            Allergy(
                no_allergies=True
            )


class WinPathResults(MessageImporter, HL7Message):
    message_type = u"ORU"
    trigger_event = u"R01"

    segments = (
        MSH, ResultsPID, ResultsPV1, ORC, RepeatingField(
            OBR,
            RepeatingField(OBX, section_name="obxs"),
            RepeatingField(NTE, section_name="ntes"),
            section_name="results"
            )
    )

    def process_message(self):
        # we still need to add NTEs to this
        def get_obx_dict(obxs, comments):
            return dict(
                value_type=obxs.obx.value_type,
                test_code=obxs.obx.test_code,
                test_name=obxs.obx.test_name,
                observation_value=obxs.obx.observation_value,
                units=obxs.obx.units,
                reference_range=obxs.obx.reference_range,
                result_status=obxs.obx.result_status,
                comments=comments.get(obxs.obx.set_id, None)
            )

        def get_comments(ntes):
            set_id_to_comment = defaultdict(list)
            for nte_package in ntes:
                set_id_to_comment[nte_package.nte.set_id].append(
                    nte_package.nte.comments
                )

            return {
                set_id: " ".join(comments) for set_id, comments in set_id_to_comment.iteritems()
            }

        messages = []

        for result in self.results:
            set_id_to_comments = get_comments(result.ntes)
            messages.append(
                ResultMessage(
                    hospital_number=self.pid.hospital_number,
                    issuing_source="uclh",
                    lab_number=result.obr.lab_number,
                    profile_code=result.obr.profile_code,
                    request_datetime=result.obr.request_datetime,
                    observation_datetime=result.obr.observation_datetime,
                    last_edited=result.obr.last_edited,
                    result_status=result.obr.result_status,
                    observations=[get_obx_dict(i, set_id_to_comments) for i in result.obxs],
                )
            )
        return messages


class MessageProcessor(object):
    def get_msh_for_message(self, msg):
        """
        We need this because we don't know the correct messageType subclass to
        instantiate yet.
        """
        return MSH(msg.segment("MSH"))

    def get_message_type(self, msg):
        msh = self.get_msh_for_message(msg)

        for message_type in itersubclasses(MessageImporter):
            if msh.message_type == message_type.message_type:
                if msh.trigger_event == message_type.trigger_event:
                    if hasattr(message_type, "sending_application"):
                        if(message_type.sending_application == msh.sending_application):
                            return message_type
                    else:
                        return message_type


    def process_message(self, msg):
        message_type = self.get_message_type(msg)
        if not message_type:
            # not necessarily an error, we ignore messages such
            # as results orders
            logging.info(
                "unable to find message type for {}".format(message_type)
            )
            return
        message_type(msg).process()
