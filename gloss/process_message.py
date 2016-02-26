from gloss.message_segments import *
from gloss import notification
import logging

from models import (
    session_scope, get_gloss_reference, save_identifier, InpatientEpisode,
    is_subscribed
)


def get_inpatient_episode(gloss_reference, pid, pv1):
    return InpatientEpisode(
        gloss_reference=gloss_reference,
        datetime_of_admission=pv1.datetime_of_admission,
        datetime_of_discharge=pv1.datetime_of_admission,
        ward_code=pv1.ward_code,
        room_code=pv1.room_code,
        bed_code=pv1.bed_code,
        visit_number=pid.patient_account_number
    )


def process_demographics(pid, session):
    """ saves a gloss id to hospital number and then goes and fetches demogrphics
    """
    # save a reference to the pid and the hospital id in the db, then go fetch demographics
    fetch_demographics(pid)
    return save_identifier(pid, session)


def fetch_demographics(pid):
    # stubbed method that will make the async call to the demographics query
    # service
    pass


class MessageType(object):

    def __init__(self, msg):
        self.raw_msg = msg

    def process(self):
        with session_scope() as session:
            self.process_message(session)

    @property
    def pid(self):
        return ResultsPID(self.raw_msg.segment("PID"))

    @property
    def msh(self):
        return MSH(self.raw_msg.segment("MSH"))

    def process_message(self, session):
        pass


class PatientMerge(MessageType):
    message_type = u"ADT"
    trigger_event = u"A34"

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))

    @property
    def mrg(self):
        return MRG(self.raw_msg.segment("MRG"))


class PatientUpdate(MessageType):
    message_type = u"ADT"
    trigger_event = u"A31"
    sending_application = "CARECAST"

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))


class InpatientAdmit(MessageType):
    message_type = u"ADT"
    trigger_event = u"A01"

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))

    @property
    def evn(self):
        return EVN(self.raw_msg.segment("EVN"))

    @property
    def pv1(self):
        return PV1(self.raw_msg.segment("PV1"))

    def process_message(self, session):
        hospital_number = self.pid.hospital_number
        gloss_reference = get_gloss_reference(hospital_number, session=session)

        if gloss_reference is None:
            gloss_reference = process_demographics(self.pid.hospital_number, session)

        inpatient_episode = get_inpatient_episode(gloss_reference, self.pid, self.pv1)
        session.add(inpatient_episode)

        if is_subscribed(hospital_number, session):
            notification.notify("elcid", InpatientEpisode)


class InpatientDischarge(MessageType):
    message_type = u"ADT"
    trigger_event = "A03"

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))

    @property
    def evn(self):
        return EVN(self.raw_msg.segment("EVN"))

    @property
    def pv1(self):
        return PV1(self.raw_msg.segment("PV1"))

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
        inpatient_result = query.one_or_none()

        if inpatient_result:
            inpatient_episode = inpatient_result[0]
            inpatient_episode.datetime_of_discharge = self.pv1.datetime_of_discharge
            session.add(inpatient_episode)


class InpatientTransfer(MessageType):
    # currently untested and incomplete
    # pending us being given an example message
    message_type = "ADT"
    trigger_event = "A02"

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))

    @property
    def pv1(self):
        return PV1(self.raw_msg.segment("PV1"))

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
        inpatient_result = query.one_or_none()

        if inpatient_result:
            # we should always have an inpatient result, but for now
            # we'll just log
            inpatient_episode = inpatient_result[0]
            inpatient_episode.ward_code = self.pv1.ward_code
            inpatient_episode.room_code = self.pv1.room_code
            inpatient_episode.bed_code = self.pv1.bed_code
            session.add(inpatient_episode)

            if is_subscribed(hospital_number, session):
                notification.notify("elcid", InpatientEpisode)
        else:
            error_msg = "we were unable to find an inpatient episode for {}"
            logging.error(error_msg.format(hospital_number))


class InpatientSpellDelete(MessageType):
    message_type = "ADT"
    trigger_event = "A07"

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))

    @property
    def evn(self):
        return EVN(self.raw_msg.segment("EVN"))

    @property
    def pv1(self):
        return PV1(self.raw_msg.segment("PV1"))

    def process_message(self, session):
        hospital_number = self.pid.hospital_number

        if is_subscribed(hospital_number, session):
            query = InpatientEpisode.query_from_identifier(
                hospital_number,
                issuing_source="uclh",
                session=session
            )
            query = query.filter(
                InpatientEpisode.visit_number == self.pid.patient_account_number
            )
            inpatient_result = query.one_or_none()

            if inpatient_result:
                # we should always have an inpatient result, but for now
                # we'll just log
                inpatient_episode = inpatient_result[0]
                inpatient_episode.ward_code = self.pv1.ward_code
                inpatient_episode.room_code = self.pv1.room_code
                inpatient_episode.bed_code = self.pv1.bed_code
                session.add(inpatient_episode)
            else:
                error_msg = "we were unable to find an inpatient episode for {}"
                logging.error(error_msg.format(hospital_number))


class InpatientCancelDischarge(MessageType):
    message_type = "ADT"
    trigger_event = "A13"

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))

    @property
    def evn(self):
        return EVN(self.raw_msg.segment("EVN"))

    @property
    def pv1(self):
        return PV1(self.raw_msg.segment("PV1"))


class Allergy(MessageType):
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


class WinPathResults(MessageType):
    message_type = u"ORU"
    trigger_event = u"R01"

    @property
    def obr(self):
        return OBR(self.raw_msg.segment('OBR'))

    @property
    def obx(self):
        return [OBX(s) for s in self.raw_msg.segments('OBX')]

    @property
    def nte(self):
        return NTE(self.raw_msg.segments("NTE"))

    def process_message(self, session):
        logging.debug('Processing WinPath Results Message')
        pass


class MessageProcessor(object):
    def get_msh_for_message(self, msg):
        """
        We need this because we don't know the correct messageType subclass to
        instantiate yet.
        """
        return MSH(msg.segment("MSH"))

    def get_message_type(self, msg):
        msh = self.get_msh_for_message(msg)

        for message_type in MessageType.__subclasses__():
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
        message_type(msg).process()
