from datetime import datetime
from models import session_scope, is_known, is_subscribed

DATETIME_FORMAT = "YYYYMMDDHHMM"



def get_fields(msg):
    ''' figures out what type of message it is based on the fields
    '''
    return [i[0][0] for i in msg]



class Segment(object):
    pass


class MSH(Segment):
    def __init__(self, segment):
        self.message_type, self.trigger_event = segment[9][0]
        self.message_datetime = datetime.strptime(segment[7][0], DATETIME_FORMAT)


class EVN(Segment):
    pass


class PID(Segment):
    pass


class NK1(Segment):
    pass


class PD1(Segment):
    def __init__(self, segment):
        identifiers = segment["3"]
        self.hospital_number = identifiers[0][0]
        if identifiers[1][0]:
            self.nhs_number = identifiers[1][0]


class MessageType(object):
    def process(self):
        with session_scope() as session:
            self.process_message(session)


class InpatientAdmit(MessageType):
    message_type = "ADT"
    trigger_event = "A31"

    def process_message(self, session):
        # shouldn't this be is known?
        if is_subscribed():
            pass


class MessageProcessor(object):
    def get_msh_for_message(self, msg):
        return MSH(msg.segment("MSH"))

    def get_message_type(self, msg):
        msh = self.get_msh_for_message(msg)

        for message_type in MessageType.__subclasses__():
            if msh.message_type == message_type.message_type:
                if msh.trigger_event == message_type.trigger_event:
                    return message_type


    def process_message(self, msg):
        message_type = self.get_message_type(msg)
        if not message_type:
            raise ValueError("unable to find message type for {}".format(message_type))
        message_type(msg).process()
