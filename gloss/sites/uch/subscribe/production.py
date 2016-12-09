"""
Subscriptions for production deployment
"""
from gloss.models import (
    atomic_method, get_or_create_identifier
)
from gloss.serialisers.opal import send_to_opal
from gloss import settings
from twisted.logger import Logger
from gloss.utils import AbstractClass
import json
from copy import copy
from gloss.subscribers.base_subscriber import BaseSubscriber

from gloss import settings
from gloss.message_type import (
    AllergyMessage, InpatientAdmissionMessage, PatientMergeMessage,
    ResultMessage, InpatientAdmissionDeleteMessage, PatientMessage,
    InpatientAdmissionTransferMessage
)
from gloss.models import (
    InpatientAdmission, Merge, Allergy, Result, is_known, Patient,
    create_or_update_inpatient_admission, create_or_update_inpatient_location,
    get_or_create_admission, get_or_create_location, get_or_create_identifier
)
from gloss.utils import itersubclasses


def db_message_processor(some_fun):
    def add_gloss_ref(self, message_container, service, session=None):
        gloss_ref = get_or_create_identifier(
            message_container.hospital_number,
            session,
            issuing_source=message_container.issuing_source
        )
        return some_fun(
            self,
            message_container,
            service,
            session=session,
            gloss_ref=gloss_ref,
        )
    return atomic_method(add_gloss_ref)


class NotifyOpalWhenSubscribed(BaseSubscriber):
    """ checks whether we're subscribed, sends a message to an opal
        application if so
    """
    def notify(self, message_container, gloss_service):
        sub_classes = itersubclasses(self.__class__)
        message_classes = set(i.__class__ for i in message_container.messages)

        for sub_class in sub_classes:
            cares_about = getattr(sub_class, "message_types", [])
            relevent = message_classes.intersection(set(cares_about))
            if relevent:
                sc = sub_class()
                sc.notify(message_container, gloss_service)


class UclhAllergySubscription(NotifyOpalWhenSubscribed):
    message_types = [AllergyMessage]

    @db_message_processor
    def notify(self, message_container, gloss_service, session=None, gloss_ref=None):
        messages = message_container.messages
        session.query(Allergy).filter(
            Allergy.gloss_reference == gloss_ref
        ).delete()

        if messages:
            for message in messages:
                kwargs = vars(message)
                allergy = Allergy(**kwargs)
                allergy.gloss_reference = gloss_ref
                session.add(allergy)


class UclhMergeSubscription(NotifyOpalWhenSubscribed):
    # TODO we should repoint all gloss subrecords
    message_types = [PatientMergeMessage]

    @db_message_processor
    def notify(self, message_container, gloss_service, session=None, gloss_ref=None):
        # we're storing all merges, in theory we shouldn't have to
        # if we don't know about the gloss reference already, why
        # record a merge?
        # Given we have multiple systems bringing in messages however
        # we can't be sure about the consistency of when something is merged
        # accross all systems
        messages = message_container.messages
        for message in messages:
            new_gloss_ref = get_or_create_identifier(
                message.new_id,
                session=session,
                issuing_source="uclh"
            )

            mrg = Merge(
                new_reference=new_gloss_ref, gloss_reference=gloss_ref
            )
            session.add(mrg)


class UclhInpatientAdmissionSubscription(NotifyOpalWhenSubscribed):
    """ Handles Inpatient Admit, Discharge and Amending """
    message_types = [InpatientAdmissionMessage]

    @db_message_processor
    def notify(self, message_container, gloss_service, session=None, gloss_ref=None):
        messages = message_container.messages
        for message in messages:
            inpatient_admission, created = get_or_create_admission(
                message, gloss_ref, session
            )

            if not created:
                inpatient_admission = create_or_update_inpatient_admission(
                    message, gloss_ref, base=inpatient_admission
                )

            session.add(inpatient_admission)
            if settings.SAVE_LOCATION:
                inpatient_location, created = get_or_create_location(
                    message, inpatient_admission, session
                )

                if not created:
                    inpatient_location = create_or_update_inpatient_location(
                        message,
                        inpatient_admission,
                        base=inpatient_location
                    )
                session.add(inpatient_location)


class UclhInpatientAdmissionDeleteSubscription(NotifyOpalWhenSubscribed):
    message_types = [InpatientAdmissionDeleteMessage]

    @db_message_processor
    def notify(self, message_container, gloss_service, session=None, gloss_ref=None):
        messages = message_container.messages
        for message in messages:
            session.query(InpatientAdmission).filter(
                InpatientAdmission.external_identifier == message.external_identifier
            ).delete()


class UclhInpatientTransferSubscription(NotifyOpalWhenSubscribed):
    message_types = [InpatientAdmissionTransferMessage]

    @db_message_processor
    def notify(self, message_container, gloss_service, session=None, gloss_ref=None):
        messages = message_container.messages
        for message in messages:
            inpatient_admission, created = get_or_create_admission(
                message, gloss_ref, session
            )
            if not created:
                inpatient_admission = create_or_update_inpatient_location(
                    message, inpatient_admission, base=inpatient_admission
                )

            if settings.SAVE_LOCATION:
                last_location, created = get_or_create_location(
                    message, inpatient_admission, session
                )

                if not created:
                    last_location.datetime_of_transfer = message.datetime_of_transfer
                    session.add(last_location)

                inpatient_location = create_or_update_inpatient_location(
                    message,
                    inpatient_admission,
                )
                inpatient_location.datetime_of_transfer_to = message.datetime_of_transfer
                session.add(inpatient_location)


class UclhWinPathResultSubscription(NotifyOpalWhenSubscribed):
    message_types = [ResultMessage]

    @db_message_processor
    def notify(self, message_container, gloss_service, session=None, gloss_ref=None):
        messages = message_container.messages
        for message in messages:
            model_kwargs = copy(vars(message))
            model_kwargs["observations"] = json.dumps(message.observations)
            result = Result(**model_kwargs)
            result.gloss_reference = gloss_ref
            session.add(result)


class UclhPatientUpdateSubscription(NotifyOpalWhenSubscribed):
    message_types = [PatientMessage]

    @db_message_processor
    def notify(self, message_container, gloss_service, session=None, gloss_ref=None):
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
                kwargs = vars(message)
                q = session.query(Patient).filter_by(
                    gloss_reference=gloss_ref
                )
                q.update(
                    kwargs
                )
