import json

from gloss import settings
from gloss.message_type import (
    AllergyMessage, InpatientAdmissionMessage, PatientMergeMessage,
    ResultMessage, InpatientAdmissionTransferMessage,
    InpatientAdmissionDeleteMessage, PatientUpdateMessage,
)
from gloss.models import (
    InpatientAdmission, Merge,
    get_gloss_reference, InpatientLocation, Allergy,
    Result, is_known, Patient,
    create_or_update_inpatient_admission, create_or_update_inpatient_location,
    get_or_create_admission, get_or_create_location
)
from gloss.serialisers.opal import OpalSerialiser
from gloss.subscribe.subscription import Subscription, db_message_processor
import requests


class TestDownstreamSubscription(Subscription, OpalSerialiser):
    def cares_about(cls, message_container):
        return True

    @db_message_processor
    def notify(self, message_container, session=None, gloss_ref=None):
        serialised = message_container.to_dict()
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
