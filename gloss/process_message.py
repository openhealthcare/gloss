from gloss.message_segments import *
from gloss import notification
import logging


from gloss.models import (
    session_scope, save_identifier, InpatientEpisode,
    get_or_create_identifier, PatientIdentifier, get_gloss_reference,
    Allergy, Result
)


def get_inpatient_episode(pid, pv1, session, base=None):
    if base:
        gloss_reference = base.gloss_reference
    else:
        gloss_reference = get_or_create_identifier(
            pid.hospital_number, session, issuing_source="uclh"
        )
    if not base:
        inpatient = InpatientEpisode()
    else:
        inpatient = base

    inpatient.gloss_reference = gloss_reference
    inpatient.datetime_of_admission = pv1.datetime_of_admission
    inpatient.datetime_of_discharge = pv1.datetime_of_admission
    inpatient.ward_code = pv1.ward_code
    inpatient.room_code = pv1.room_code
    inpatient.bed_code = pv1.bed_code
    inpatient.visit_number = pid.patient_account_number
    inpatient.datetime_of_discharge = pv1.datetime_of_discharge
    return inpatient


def process_demographics(pid, session):
    """ saves a gloss id to hospital number and then goes and fetches demogrphics
    """
    # save a reference to the pid and the hospital id in the db, then go fetch demographics
    fetch_demographics(pid)
    return save_identifier(pid, session)


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

    def process_message(self, session):
        # find the identifier, mark it as inactive, send
        # send it downstream to deal with if it exists
        patient_identifier = PatientIdentifier.query_from_identifier(
            self.mrg.duplicate_hospital_number,
            issuing_source="uclh",
            session=session
        ).one_or_none()

        if patient_identifier:
            patient_identifier.merged_into_identifier = self.pid.hospital_number
            patient_identifier.active = False
            session.add(patient_identifier)
            notification.notify("elcid", patient_identifier)


class PatientUpdate(MessageType):
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
            notification.notify("elcid", gloss_reference)


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
        inpatient_episode = get_inpatient_episode(
            self.pid, self.pv1, session
        )
        session.add(inpatient_episode)
        notification.notify(self.msh.sending_application, inpatient_episode)


class InpatientAmend(MessageType):
    message_type = "ADT"
    trigger_event = "A08"

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
        possible_episode = query.one_or_none()
        inpatient_episode = get_inpatient_episode(
            self.pid, self.pv1, session, possible_episode
        )
        session.add(inpatient_episode)
        notification.notify(self.msh.sending_application, inpatient_episode)


class InpatientDischarge(InpatientAmend):
    message_type = u"ADT"
    trigger_event = "A03"


class InpatientTransfer(InpatientAmend):
    # currently untested and incomplete
    # pending us being given an example message
    message_type = "ADT"
    trigger_event = "A02"


class InpatientCancelDischarge(InpatientAmend):
    message_type = "ADT"
    trigger_event = "A13"


class InpatientSpellDelete(MessageType):
    message_type = "ADT"
    trigger_event = "A07"

    @property
    def pid(self):
        return InpatientPID(self.raw_msg.segment("PID"))

    @property
    def evn(self):
        return EVN(self.raw_msg.segment("EVN"))

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
            notification.notify(self.msh.sending_application, inpatient_episode)


class AllergyMessage(MessageType):
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

    def process_message(self, session):
        allergies = Allergy.query_from_identifier(
            self.pid.hospital_number,
            "uclh",
            session
        ).all()

        for allergy in allergies:
            session.delete(allergy)

        gloss_ref = get_or_create_identifier(
            self.pid.hospital_number,
            session,
            issuing_source="uclh"
        )
        if self.al1:
            # we need to handle allergies which we are not doing

            Allergy(
                gloss_reference=gloss_ref,
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
                gloss_reference=gloss_ref,
                no_allergies=True
            )

        notification.notify("elcid", Allergy)


class WinPathResults(MessageType):
    message_type = u"ORU"
    trigger_event = u"R01"

    @property
    def obr(self):
        return OBR(self.raw_msg.segment('OBR'))

    @property
    def obxs(self):
        return OBX.get_segments(self.raw_msg.segments('OBX'))

    @property
    def ntes(self):
        try:
            return NTE.get_segments(self.raw_msg.segments("NTE"))
        except KeyError:
            return []

    def process_message(self, session):
        # We're assuming this will definitely change in the future.
        # This basically only handles the case whereby we simply pass through
        # without hitting the database.

        gloss_ref = get_or_create_identifier(
            self.pid.hospital_number,
            session,
            issuing_source="uclh"
        )

        results = []
        set_id_to_nte = {i.set_id: i for i in self.ntes}

        for obx in self.obxs:
            nte = set_id_to_nte.get(obx.set_id, None)
            comments = None

            if nte:
                comments = nte.comments

            result = Result(
                gloss_reference=gloss_ref,
                value_type=obx.value_type,
                test_code=obx.test_code,
                test_name=obx.test_name,
                observation_value=obx.observation_value,
                units=obx.units,
                reference_range=obx.reference_range,
                observation_datetime=self.obr.observation_datetime,
                comments=comments
            )

            results.append(result)

        session.add(result)
        notification.notify(self.msh.sending_application, result)


def itersubclasses(cls, _seen=None):
    """
    Recursively iterate through subclasses
    """
    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None: _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError: # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub

class MessageProcessor(object):
    def get_msh_for_message(self, msg):
        """
        We need this because we don't know the correct messageType subclass to
        instantiate yet.
        """
        return MSH(msg.segment("MSH"))

    def get_message_type(self, msg):
        msh = self.get_msh_for_message(msg)

        for message_type in itersubclasses(MessageType):
            if msh.message_type == message_type.message_type:
                if msh.trigger_event == message_type.trigger_event:
                    if hasattr(message_type, "sending_application"):
                        if(message_type.sending_application == msh.sending_application):
                            return message_type
                    else:
                        return message_type


    def process_message(self, msg):
        message_type = self.get_message_type(msg)
        logging.error('Processing {0}'.format(message_type))
        if not message_type:
            # not necessarily an error, we ignore messages such
            # as results orders
            logging.info(
                "unable to find message type for {}".format(message_type)
            )
            return
        message_type(msg).process()
