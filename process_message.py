def get_fields(msg):
    ''' figures out what type of message it is based on the fields
    '''
    return [i[0][0] for i in msg]


class Segment(object):
    @property
    def name(self):
        return self.__class__.__name__

    def initialise(self, msg_segments):
        pass


class MSH(Segment):
    pass


class EVN(Segment):
    pass


class PID(Segment):
    pass


class NK1(Segment):
    pass


class PD1(Segment):
    pass


class MessageType(object):
    @property
    def fields(self):
        return [i().name for i in self.segments]

    @classmethod
    def get(cls, some_message):
        message = cls()
        import ipdb; ipdb.set_trace()

        if message.fields == get_fields(some_message):
            message.initialise(some_message)
            return message

    def initialise(self, msg):
        for iterator, field in enumerate(msg):
            s = self.segments[iterator]()
            setattr(self, s.name, s.initialise(field))


class InpatientAdmit(MessageType):
    segments = (MSH, EVN, PID)


class MessageProcessor(object):
    @classmethod
    def process(cls, msg):
        for message_type in MessageType.__subclasses__():
            message = message_type.get(msg)
            if message:
                continue

        return message
