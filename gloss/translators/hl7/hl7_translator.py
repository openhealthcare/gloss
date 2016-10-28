from gloss.translators.hl7.segments import *
from gloss.utils import itersubclasses
from gloss.exceptions import TranslatorError

# HL7 messages are defined as single or repeating segments
# The below messages are generic HL7 messages
# if you want to implement your own
# inherit from theHL7Translator


class HL7Translator(HL7Base):
    def __init__(self, raw_message):
        message = copy(raw_message)

        for field in self.segments:
            if field.__class__ == RepeatingField:
                found_repeaters, message = field.get(message)
                setattr(self, field.section_name, found_repeaters)
            else:
                mthd = self.get_method_for_field(field.name())
                try:
                    setattr(self, field.name().lower(), mthd(message.segment(field.name())))
                except KeyError:
                    raise TranslatorError("unable to find {0} for {1}".format(field.name(), raw_message))
                message = clean_until(message, field.name())

    @classmethod
    def translate(cls, msg):
        msh = cls.get_msh(msg)
        for message_type in itersubclasses(cls):
            if msh.message_type == message_type.message_type:
                if msh.trigger_event == message_type.trigger_event:
                    if hasattr(message_type, "sending_application"):
                        if(message_type.sending_application == msh.sending_application):
                            return message_type(msg)
                    else:
                        return message_type(msg)

    @classmethod
    def get_msh(self, msg):
        return MSH(msg.segment("MSH"))


class PatientMerge(HL7Translator):
    message_type = u"ADT"
    trigger_event = u"A34"
    segments = (MSH, InpatientPID, MRG)


class PatientUpdate(HL7Translator):
    message_type = u"ADT"
    trigger_event = u"A31"
    segments = (InpatientPID, UpdatePD1)
    sending_application = "CARECAST"


class InpatientAdmit(HL7Translator):
    message_type = u"ADT"
    trigger_event = u"A01"
    segments = (EVN, InpatientPID, PV1, PV2,)


class InpatientDischarge(InpatientAdmit):
    message_type = u"ADT"
    trigger_event = "A03"


class InpatientAmend(InpatientAdmit):
    message_type = "ADT"
    trigger_event = "A08"


class InpatientCancelDischarge(InpatientAdmit):
    message_type = "ADT"
    trigger_event = "A13"


class InpatientTransfer(InpatientAdmit):
    message_type = "ADT"
    trigger_event = "A02"
    segments = (EVN, InpatientPID, PV1, PV2,)


class InpatientSpellDelete(HL7Translator):
    message_type = "ADT"
    trigger_event = "A07"
    segments = (EVN, InpatientPID, PV1,)


class AllergyMessage(HL7Translator):
    message_type = "ADT"
    trigger_event = "A31"
    sending_application = "ePMA"
    segments = (AllergiesPID, RepeatingField(AL1, section_name="allergies"),)


class WinPathResultsOrder(HL7Translator):
    message_type = u"ORM"
    trigger_event = "O01"

    segments = (MSH, ResultsPID)


class WinPathResults(HL7Translator):
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
