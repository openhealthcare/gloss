import json
import datetime

from gloss.models import (
    InpatientEpisode, PatientIdentifier, Merge,
    session_scope, get_gloss_reference, InpatientLocation
)
from gloss import settings
from models import atomic_method, get_or_create_identifier
from gloss.message_type import (
    AllergyMessage, InpatientEpisodeMessage, PatientMergeMessage, ResultMessage,
    InpatientEpisodeTransferMessage, InpatientEpisodeDeleteMessage
)


def db_message_processor(some_fun):
    def add_gloss_ref(self, messages, session=None, **kwargs):
        gloss_ref = get_or_create_identifier(
            messages[0].hospital_number,
            session,
            issuing_source="uclh"
        )
        return some_fun(self, messages, session=session, gloss_ref=gloss_ref, **kwargs)
    return atomic_method(add_gloss_ref)


class OpalJSONSerializer(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return format(o, settings.DATETIME_FORMAT)
        elif isinstance(o, datetime.date):
            return format(
                datetime.datetime.combine(
                    o, datetime.datetime.min.time()
                ), settings.DATE_FORMAT
            )
        elif isinstance(o, datetime.datetime):
            return format(
                datetime.datetime.combine(
                    o, datetime.datetime.min.time()
                ), settings.DATETIME_FORMAT
            )
        super(OpalJSONSerializer, self).default(o)


class Subscription(object):
    @classmethod
    def cares_about(self, message_type):
        if message_type in cls.subscribtion_types:
            return True
        return False

    @property
    def issuing_source(self):
        raise NotImplementedError("you need to implement 'issuing source'")

    def serialise(self):
        raise NotImplementedError("you need to implement 'serialise'")

    def process_data(self):
        raise NotImplementedError("you need to implement 'post data'")

    def notify(self, message, *args, **kwargs):
        pass


class OpalSerialiser(object):
    def serialise(self, *models):
        if not len(models):
            raise ValueError("models should be passed into the serialise method")

        patient_identifier = None

        for model in models:
            if model.__class__ == PatientIdentifier:
                if model.issuing_source == self.issuing_source:
                    patient_identifier = model

        if patient_identifier is None:
            with session_scope() as session:
                patient_identifier = session.query(PatientIdentifier).filter(
                    PatientIdentifier.issuing_source == self.issuing_source,
                    PatientIdentifier.gloss_reference == models[0].gloss_reference
                ).one()

        as_dict = dict(
            identifier=patient_identifier.identifier,
            data=[i.to_dict() for i in models]
        )

        return json.dumps(as_dict, cls=OpalJSONSerializer)


class UclhAllergySubscription(Subscription, OpalSerialiser):
    message_type = AllergyMessage

    def __init__(self, message):
        pass

    @db_message_processor
    def notify(self, message, session=None, gloss_ref=None):
        if message.allergies:
            for i in message.allergies:
                pass
                # save allergies
        elif message.no_allergies:
            pass
            # save no allergies

        # post downstream


class UclhMergeSubscription(Subscription, OpalSerialiser):
    # TODO we should repoint all gloss subrecords
    message_type = PatientMergeMessage

    def post_downstream(self, message):
        import logging
        logging.critical("this is working then")
        print "is this working"

    @db_message_processor
    def notify(self, messages, session=None, gloss_ref=None):
        for message in messages:
            old_gloss_ref = get_gloss_reference(
                message.old_id,
                session=session,
                issuing_source="uclh"
            )

            if old_gloss_ref:
                mrg = Merge(old_reference=old_gloss_ref, gloss_reference=gloss_ref)
                session.add(mrg)

            self.post_downstream(message)


def create_or_update_inpatient_episode(message, gloss_ref, base=None):
    if base:
        inpatient_episode = base
    else:
        inpatient_episode = InpatientEpisode()

    inpatient_episode.gloss_reference = gloss_ref
    inpatient_episode.datetime_of_admission = message.datetime_of_admission
    inpatient_episode.datetime_of_discharge = message.datetime_of_discharge
    inpatient_episode.visit_number = message.visit_number
    return inpatient_episode


def create_or_update_inpatient_location(message, inpatient_episode, base=None):
    if base:
        inpatient_location = base
    else:
        inpatient_location = InpatientLocation()

    inpatient_location.ward_code = message.ward_code
    inpatient_location.room_code = message.room_code
    inpatient_location.bed_code = message.bed_code
    inpatient_location.inpatient_episode = inpatient_episode
    return inpatient_location


def get_or_create_episode(message, gloss_ref, session):
    created = False
    inpatient_episode = session.query(InpatientEpisode).filter(
        InpatientEpisode.visit_number == message.visit_number
    ).one_or_none()

    if not inpatient_episode:
        created = True
        inpatient_episode = create_or_update_inpatient_episode(
            message, gloss_ref
        )

    return inpatient_episode, created,


def get_or_create_location(message, inpatient_episode, session):
    created = False
    inpatient_location = InpatientLocation.get_location(
        inpatient_episode, session
    )

    if not inpatient_location:
        created = True
        inpatient_location = create_or_update_inpatient_location(
            message, inpatient_episode
        )

    return inpatient_location, created,


class UclhInpatientSubscription(Subscription, OpalSerialiser):
    """ Handles Inpatient Admit, Discharge and Amending """
    message_type = InpatientEpisodeMessage

    def get_or_create_inpatient_episode(self, message, session, gloss_ref):
        self.session.query()

    @db_message_processor
    def notify(self, messages, session=None, gloss_ref=None):
        for message in messages:
            inpatient_episode, created = get_or_create_episode(
                message, gloss_ref, session
            )

            if not created:
                inpatient_episode = create_or_update_inpatient_episode(
                    message, gloss_ref, base=inpatient_episode
                )

            session.add(inpatient_episode)

            if settings.SAVE_LOCATION:
                inpatient_location, created = get_or_create_location(
                    message, inpatient_episode, session
                )

                if not created:
                    inpatient_location = create_or_update_inpatient_location(
                        message,
                        inpatient_episode,
                        base=inpatient_location
                    )
                session.add(inpatient_location)


class UclhInpatientEpisodeDeleteSubscription(Subscription, OpalSerialiser):
    message_type = InpatientEpisodeDeleteMessage

    @db_message_processor
    def notify(self, messages, session=None, gloss_ref=None):
        for message in messages:
            session.query(InpatientEpisode).filter(
                InpatientEpisode.visit_number == message.visit_number
            ).delete()


class UclhInpatientTransferSubscription(Subscription, OpalSerialiser):
    message_type = InpatientEpisodeTransferMessage

    @db_message_processor
    def notify(self, messages, session=None, gloss_ref=None):
        for message in messages:
            inpatient_episode, created = get_or_create_episode(
                message, gloss_ref, session
            )
            if not created:
                inpatient_episode = create_or_update_inpatient_location(
                    message, inpatient_episode, base=inpatient_episode
                )

            if settings.SAVE_LOCATION:
                last_location, created = get_or_create_location(
                    message, inpatient_episode, session
                )

                if not created:
                    last_location.datetime_of_transfer = message.datetime_of_transfer
                    session.add(last_location)

                inpatient_location = create_or_update_inpatient_location(
                    message,
                    inpatient_episode,
                )
                inpatient_location.datetime_of_transfer_to = message.datetime_of_transfer
                session.add(inpatient_location)



class UclhWinPathResultSubscription(Subscription, OpalSerialiser):
    message_type = ResultMessage

    @db_message_processor
    def notify(self, messages, session=None, gloss_ref=None):
        pass
