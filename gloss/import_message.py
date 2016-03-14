from twisted.logger import Logger
from gloss.message_segments import *
from gloss import notification
from gloss.models import session_scope, Error
from utils import itersubclasses
from message_type import (
    InpatientEpisodeMessage, PatientMergeMessage, ResultMessage,
    InpatientEpisodeTransferMessage, InpatientEpisodeDeleteMessage,
    PatientUpdateMessage, AllergyMessage, MessageContainer
)
from collections import defaultdict


class MessageImporter(HL7Message):
    @property
    def gloss_message_type(self):
        raise NotImplementedError("we need a gloss message type")

    def construct_container(self):
        msgs = self.process_message()
        message_container = MessageContainer(
            messages=msgs,
            hospital_number=self.pid.hospital_number,
            issuing_source="uclh",
            message_type=self.gloss_message_type
        )
        return message_container

    def process(self):
        message_container = self.construct_container()
        notification.notify(message_container)

    def process_message(self, session=None):
        pass


class PatientMerge(MessageImporter):
    message_type = u"ADT"
    trigger_event = u"A34"
    gloss_message_type = PatientMergeMessage

    segments = (
        MSH, InpatientPID, MRG
    )

    def process_message(self, session=None):
        return [self.gloss_message_type(
            old_id=self.mrg.duplicate_hospital_number,
            hospital_number=self.pid.hospital_number,
            issuing_source="uclh"
        )]


class PatientUpdate(MessageImporter):
    message_type = u"ADT"
    trigger_event = u"A31"
    sending_application = "CARECAST"
    segments = (InpatientPID, PD1)
    gloss_message_type = PatientUpdateMessage

    def process_message(self):
        interesting_fields = [
            "surname",
            "first_name",
            "middle_name",
            "title",
            "date_of_birth",
            "sex",
            "marital_status",
            "religion",
            "ethnicity",
            "post_code",
            "date_of_death",
            "death_indicator",
        ]

        # if we get an empty field the way the message formatting is, we can
        # ignore it, unless its if the patient death has turned to negative
        # in which case we need to null out the date of death
        kwargs = {
            i: getattr(self.pid, i) for i in interesting_fields if getattr(self.pid, i)
        }

        kwargs["gp_practice_code"] = self.pd1.gp_practice_code

        if self.pid.death_indicator == False:
            kwargs["date_of_death"] = None

        return [
            PatientUpdateMessage(**kwargs)
        ]


class InpatientAdmit(MessageImporter):
    message_type = u"ADT"
    trigger_event = u"A01"
    segments = (EVN, InpatientPID, PV1, PV2,)
    gloss_message_type = InpatientEpisodeMessage

    def process_message(self):
        return [self.gloss_message_type(
            datetime_of_admission=self.pv1.datetime_of_admission,
            ward_code=self.pv1.ward_code,
            room_code=self.pv1.room_code,
            bed_code=self.pv1.bed_code,
            visit_number=self.pid.patient_account_number,
            hospital_number=self.pid.hospital_number,
            issuing_source="uclh",
            datetime_of_discharge=self.pv1.datetime_of_discharge,
            admission_diagnosis=self.pv2.admission_diagnosis,
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


class InpatientTransfer(MessageImporter):
    # currently untested and incomplete
    # pending us being given an example message
    message_type = "ADT"
    trigger_event = "A02"
    segments = (EVN, InpatientPID, PV1, PV2,)
    gloss_message_type = InpatientEpisodeTransferMessage

    def process_message(self):
        message = self.gloss_message_type(
            datetime_of_admission=self.pv1.datetime_of_admission,
            ward_code=self.pv1.ward_code,
            room_code=self.pv1.room_code,
            bed_code=self.pv1.bed_code,
            visit_number=self.pid.patient_account_number,
            hospital_number=self.pid.hospital_number,
            issuing_source="uclh",
            datetime_of_discharge=self.pv1.datetime_of_discharge,
            datetime_of_transfer=self.evn.planned_datetime,
            admission_diagnosis=self.pv2.admission_diagnosis
        )
        return [message]


class InpatientSpellDelete(MessageImporter):
    message_type = "ADT"
    trigger_event = "A07"
    segments = (EVN, InpatientPID, PV1,)
    gloss_message_type = InpatientEpisodeDeleteMessage

    def process_message(self):
        return [self.gloss_message_type(
            visit_number=self.pid.patient_account_number,
            datetime_of_deletion=self.evn.recorded_datetime,
            hospital_number=self.pid.hospital_number,
            issuing_source="uclh"
        )]


class AllergyMessage(MessageImporter):
    message_type = "ADT"
    trigger_event = "A31"
    sending_application = "ePMA"
    segments = (AllergiesPID, RepeatingField(AL1, section_name="allergies"),)
    gloss_message_type = AllergyMessage

    def process_message(self):
        all_allergies = []
        for allergy in self.allergies:
            all_allergies.append(self.gloss_message_type(
                allergy_type=allergy.al1.allergy_type,
                allergy_type_description=allergy.al1.allergy_type_description,
                certainty_id=allergy.al1.certainty_id,
                certainty_description=allergy.al1.certainty_description,
                allergy_reference_name=allergy.al1.allergy_reference_name,
                allergy_description=allergy.al1.allergy_description,
                allergen_reference_system=allergy.al1.allergen_reference_system,
                allergen_reference=allergy.al1.allergen_reference,
                status_id=allergy.al1.status_id,
                status_description=allergy.al1.status_description,
                diagnosis_datetime=allergy.al1.diagnosis_datetime,
                allergy_start_datetime=allergy.al1.allergy_start_datetime,
                hospital_number=self.pid.hospital_number,
                issuing_source="uclh"
            ))
        return all_allergies



class WinPathResults(MessageImporter):
    message_type = u"ORU"
    trigger_event = u"R01"
    gloss_message_type = ResultMessage

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
            units = obxs.obx.units
            if units:
                units = units.replace("\\S\\", "^")
            return dict(
                value_type=obxs.obx.value_type,
                test_code=obxs.obx.test_code,
                test_name=obxs.obx.test_name,
                observation_value=obxs.obx.observation_value,
                units=units,
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
                self.gloss_message_type(
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
    log = Logger(namespace="processor")

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
            self.log.info(
                "unable to find message type for {}".format(message_type)
            )
            return
        try:
            message_type(msg).process()
        except Exception as e:
            self.log.error("failed to parse")
            self.log.error(str(msg).replace("\r", "\n"))
            self.log.error("with %s" % e)
            try:
                with session_scope() as session:
                    err = Error(
                        error=str(e),
                        message=str(msg)
                    )
                    session.add(err)
            except Exception as e:
                self.log.error("failed to save error to database")
                self.log.error("with %s" % e)
