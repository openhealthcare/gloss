from datetime import datetime
import logging

from models import session_scope, is_known, is_subscribed

DATETIME_FORMAT = "%Y%m%d%H%M"


def get_fields(msg):
    ''' figures out what type of message it is based on the fields
    '''
    return [i[0][0] for i in msg]


class Segment(object):
    pass


class MSH(Segment):
    def __init__(self, segment):
        self.trigger_event = segment[9][0][1][0]
        self.message_type = segment[9][0][0][0]
        # allergy information contains milli seconds, lets strip that
        # off for the time being
        self.message_datetime = datetime.strptime(segment[7][0][:12], DATETIME_FORMAT)
        self.sending_application = segment[3][0]


class MRG(Segment):
    def __init__(self, segment):
        self.duplicate_hospital_number = segment[1][0][0][0]


class ResultsPID(Segment):
    """
        the pid definition used by the WINPATH systems
    """
    def __init__(self, segment):
        self.nhs_number = segment[2][0]
        if isinstance(self.nhs_number, list):
            self.nhs_number = self.nhs_number[0][0]
        self.hospital_number = segment[3][0][0][0]
        self.surname = segment[5][0][0][0]
        self.forename = segment[5][0][1][0]
        self.date_of_birth = segment[7][0]
        self.gender = segment[8][0]


class InpatientPID(Segment):
    """
        the pid definition used by CARECAST systems
    """
    def __init__(self, segment):

        self.hospital_number = segment[3][0][0][0]

        if len(segment[3][1][0][0]):
            self.nhs_number = segment[3][1][0][0]
        else:
            self.nhs_number = None

        self.surname = segment[5][0][0][0]
        self.forename = segment[5][0][1][0]
        self.date_of_birth = segment[7][0]
        self.gender = segment[8][0]

        # this is used by spell delete
        # it seems similar to our episode id
        self.patient_account_number = segment[18][0]

        if len(segment[29][0]):
            self.date_of_death = segment[29][0]

        if len(segment[30][0]):
            self.death_indicator = segment[30][0]


class AllergiesPID(Segment):
    """
        the pid definition used by allergies
    """

    def __init__(self, segment):
        self.hospital_number = segment[3][0][0][0]
        self.surname = segment[5][0][0][0]
        self.forename = segment[5][0][1][0]
        self.date_of_birth = segment[7][0]
        self.gender = segment[8][0]

        # sample messages record 2 different types of
        # message "No Known Allergies" and
        # "Allergies Known and Recorde" we're
        # querying as to whether there are others
        self.allergy_status = segment[37][0]


class OBR(Segment):
    STATUSES = {
        'F': 'FINAL',
        'I': 'INTERIM',
        'A': 'SOME RESULTS AVAILABLE'
    }
    def __init__(self, segment):
        self.lab_number = segment[3][0]
        self.profile_code = segment[4][0][0][0]
        self.profile_description = segment[4][0][1][0]
        self.request_datetime = segment[6][0]
        self.observation_datetime = segment[7][0]
        self.last_edited = segment[22][0]
        self.result_status = OBR.STATUSES[segment[25][0]]


class OBX(Segment):
    STATUSES = {
        'F': 'FINAL',
        'I': 'INTERIM'
    }

    def __init__(self, segment):
        self.test_code = segment[3][0][0][0]
        self.test_name = segment[3][0][1][0]
        self.observation_value = segment[5][0]
        self.units = segment[6][0]
        self.reference_range = segment[7][0]
        self.result_status = OBX.STATUSES[segment[11][0]]


class EVN(Segment):
    def __init__(self, segment):
        self.event_type = segment[1][0]
        self.recorded_time = segment[2][0]
        self.event_description = segment[4][0]


class PV1(Segment):
    EPISODE_TYPES = {
        "A": "DAY CASE",
        "I": "INPATIENT",
        "E": "EMERGENCY",
    }

    def __init__(self, segment):
        self.ward_code = segment[3][0][0][0]
        self.room_code = segment[3][0][1][0]
        self.bed = segment[3][0][2][0]
        self.admission_datetime = segment[44][0]

        self.episode_type = self.EPISODE_TYPES[segment[2][0]]

        if len(segment) > 44:
            self.discharge_datetime = segment[45][0]


class NTE(Segment):
    def __init__(self, segments):
        self.comments = "\n".join(
            s[3][0] for s in segments
        )


class AL1(Segment):
    # there's a good chance we won't need
    # all these fields, but they
    # raise a lot of questions
    def __init__(self, segments):
        self.allergy_type = segments[2][0][0][0]
        self.allergy_type_description = segments[2][0][1][0]
        self.certainty_id = segments[2][0][3][0]
        self.certainty_description = segments[2][0][4][0]
        self.allergy_reference_name = segments[3][0][0][0]
        self.allergy_description = segments[3][0][1][0]
        self.allergen_reference_system = segments[3][0][2][0]
        self.allergen_reference = segments[3][0][3][0]
        self.status_id = segments[4][0][0][0]
        self.status_description = segments[4][0][1][0]
        self.diagnosis_data = segments[4][0][4][0]
        self.allergy_start_date = segments[6][0]


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

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))

    @property
    def evn(self):
        return EVN(self.raw_msg.segment("EVN"))

    @property
    def pv1(self):
        return PV1(self.raw_msg.segment("PV1"))


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
