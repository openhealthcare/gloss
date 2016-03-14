import json

from gloss.serialisers.opal import OpalSerialiser

from gloss.models import (
    InpatientEpisode, Merge,
    get_gloss_reference, InpatientLocation, Allergy,
    Result, is_known, Patient
)
from gloss import settings
from models import atomic_method, get_or_create_identifier
from gloss.message_type import (
    AllergyMessage, InpatientEpisodeMessage, PatientMergeMessage,
    ResultMessage, InpatientEpisodeTransferMessage,
    InpatientEpisodeDeleteMessage, PatientUpdateMessage
)


def db_message_processor(some_fun):
    def add_gloss_ref(self, message_container, session=None):
        gloss_ref = get_or_create_identifier(
            message_container.hospital_number,
            session,
            issuing_source=message_container.issuing_source
        )
        return some_fun(
            self,
            message_container,
            session=session,
            gloss_ref=gloss_ref,
        )
    return atomic_method(add_gloss_ref)


class Subscription(object):
    @classmethod
    def cares_about(self, message_container):
        if message_container.gloss_message_type in cls.subscribtion_types:
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


class UclhAllergySubscription(Subscription, OpalSerialiser):
    message_type = AllergyMessage

    @db_message_processor
    def notify(self, message_container, session=None, gloss_ref=None):
        messages = message_container.messages
        session.query(Allergy).filter(
            Allergy.gloss_reference == gloss_ref
        ).delete()

        if messages:
            for message in messages:
                allergy = Allergy(**vars(message))
                allergy.gloss_reference = gloss_ref
                session.add(allergy)
        else:
            allergy = Allergy(no_allergies=True, gloss_reference=gloss_ref)
            session.add(allergy)


class UclhMergeSubscription(Subscription, OpalSerialiser):
    # TODO we should repoint all gloss subrecords
    message_type = PatientMergeMessage

    @db_message_processor
    def notify(self, message_container, session=None, gloss_ref=None):
        messages = message_container.messages
        for message in messages:
            old_gloss_ref = get_gloss_reference(
                message.old_id,
                session=session,
                issuing_source="uclh"
            )

            if old_gloss_ref:
                mrg = Merge(old_reference=old_gloss_ref, gloss_reference=gloss_ref)
                session.add(mrg)


def create_or_update_inpatient_episode(message, gloss_ref, base=None):
    if base:
        inpatient_episode = base
    else:
        inpatient_episode = InpatientEpisode()

    inpatient_episode.gloss_reference = gloss_ref
    inpatient_episode.datetime_of_admission = message.datetime_of_admission
    inpatient_episode.datetime_of_discharge = message.datetime_of_discharge
    inpatient_episode.visit_number = message.visit_number
    inpatient_episode.admission_diagnosis = message.admission_diagnosis
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
    def notify(self, message_container, session=None, gloss_ref=None):
        messages = message_container.messages
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
    def notify(self, message_container, session=None, gloss_ref=None):
        messages = message_container.messages
        for message in messages:
            session.query(InpatientEpisode).filter(
                InpatientEpisode.visit_number == message.visit_number
            ).delete()


class UclhInpatientTransferSubscription(Subscription, OpalSerialiser):
    message_type = InpatientEpisodeTransferMessage

    @db_message_processor
    def notify(self, message_container, session=None, gloss_ref=None):
        messages = message_container.messages
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
    def notify(self, message_container, session=None, gloss_ref=None):
        messages = message_container.messages
        for message in messages:
            model_kwargs = vars(message)
            model_kwargs["observations"] = json.dumps(message.observations)
            result = Result(**model_kwargs)
            result.gloss_reference = gloss_ref
            session.add(result)


class UclhPatientUpdateSubscription(Subscription, OpalSerialiser):
    message_type = PatientUpdateMessage

    @db_message_processor
    def notify(self, message_container, session=None, gloss_ref=None):
        # theoretically we don't have to query for known here, if we don't know
        # them, they won't be there so the update won't do anything
        # let's be explicit for now
        known = is_known(
            message_container.hospital_number,
            session,
            message_container.issuing_source
        )

        if known:
            for message in message_container.messages:
                q = session.query(Patient).filter_by(
                    gloss_reference=gloss_ref
                )
                q.update(
                    vars(message)
                )


class WinPathMessage(Subscription, OpalSerialiser):
    message_type = ResultMessage
    """
    We don't expect this to be a long term strategy.
    It's a placeholder class to simply pass through
    winpath stuff to an OPAL instance.
    """
    def notify(self, message_container):
        # self.send_to_opal(message_container)
        pass
