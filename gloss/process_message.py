from gloss.message_segments import *
import logging

from models import session_scope, get_gloss_id, save_identifier, InpatientEpisode


def get_inpatient_episode(gloss_id, pid, pv1):
    return InpatientEpisode(
        gloss_reference_id=gloss_id,
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
    save_identifier(pid, session)
    fetch_demographics(pid)


# stubbed method that will make the async call to the demographics query
# service
def fetch_demographics(pid): pass



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
        gloss_id = get_gloss_id(hospital_number, session=session)

        if gloss_id is None:
            gloss_id = process_demographics(self.pid.hospital_number, session)

        inpatient_episode = get_inpatient_episode(gloss_id, self.pid, self.pv1)
        session.add(inpatient_episode)


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


class InpatientTransfer(MessageType):
    # currently untested and incomplete
    # pending us being given an example message
    message_type = "ADT"
    trigger_event = "A02"


class InpatientSpellDelete(MessageType):
    # currently untested and incomplete
    # pending us being given an example message
    message_type = "ADT"
    trigger_event = "A07"

    # We know it will have these segments, but we can't
    # really test them yet - see above.

    # @property
    # def pid(self):
    #     return InpatientPID(self.raw_msg.segment("PID"))

    # @property
    # def evn(self):
    #     return EVN(self.raw_msg.segment("EVN"))

    # @property
    # def pv1(self):
    #     return PV1(self.raw_msg.segment("PV1"))


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

    def process_message(self, session): pass


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
            return
        message_type(msg).process()
