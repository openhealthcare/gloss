"""
Subscriptions for production deployment
"""
import json

from gloss import settings
from gloss.message_type import (
    AllergyMessage, InpatientEpisodeMessage, PatientMergeMessage,
    ResultMessage, InpatientEpisodeTransferMessage,
    InpatientEpisodeDeleteMessage, PatientUpdateMessage,
)
from gloss.models import (
    InpatientEpisode, Merge,
    get_gloss_reference, InpatientLocation, Allergy,
    Result, is_known, Patient,
    create_or_update_inpatient_episode, create_or_update_inpatient_location,
    get_or_create_episode, get_or_create_location
)
from gloss.serialisers.opal import OpalSerialiser
from gloss.subscribe.subscription import Subscription, db_message_processor

class UclhAllergySubscription(Subscription, OpalSerialiser):
    message_types = [AllergyMessage]

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
    message_types = [PatientMergeMessage]

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


class UclhInpatientEpisodeSubscription(Subscription, OpalSerialiser):
    """ Handles Inpatient Admit, Discharge and Amending """
    message_types = [InpatientEpisodeMessage]

    @db_message_processor
    def notify(self, message_container, session=None, gloss_ref=None):
        messages = message_container.messages
        for message in messages:
            inpatient_episode, created = get_or_create_episode(
                message, gloss_ref, session
            )
            print inpatient_episode, created

            if not created:
                inpatient_episode = create_or_update_inpatient_episode(
                    message, gloss_ref, base=inpatient_episode
                )

            session.add(inpatient_episode)
            print 'added', inpatient_episode
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
                print 'added', inpatient_location


class UclhInpatientEpisodeDeleteSubscription(Subscription, OpalSerialiser):
    message_types = [InpatientEpisodeDeleteMessage]

    @db_message_processor
    def notify(self, message_container, session=None, gloss_ref=None):
        messages = message_container.messages
        for message in messages:
            session.query(InpatientEpisode).filter(
                InpatientEpisode.visit_number == message.visit_number
            ).delete()


class UclhInpatientTransferSubscription(Subscription, OpalSerialiser):
    message_types = [InpatientEpisodeTransferMessage]

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
    message_types = [ResultMessage]

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
    message_types = [PatientUpdateMessage]

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
