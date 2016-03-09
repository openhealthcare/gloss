from subscriptions import *


class MessageContainer(object):
    def __init__(
        self, messages, hospital_number, issuing_source, message_type
    ):
        self.messages = messages
        self.hospital_number = hospital_number
        self.issuing_source = issuing_source
        self.message_type = message_type


class MessageType(object):
    def subscribers(self):
        for subscription_class in classes:
            if subscription_class.message_type == message_type.__class__:
                yield subscription_class

    def notify(self):
        for subscription_class in self.subscribers:
            subscription = subscription_class(message)
            subscription.notify()

    def to_dict(self):
        pass


class PatientMergeMessage(MessageType):
    def __init__(self, **kwargs):
        self.old_id = kwargs.pop("old_id")


class AllergyMessage(MessageType):
    def __init__(
        self, **kwargs
    ):
        self.allergy_type = kwargs.pop("allergy_type")
        self.allergy_type_description = kwargs.pop("allergy_type_description")
        self.certainty_id = kwargs.pop("certainty_id")
        self.certainty_description = kwargs.pop("certainty_description")
        self.allergy_reference_name = kwargs.pop("allergy_reference_name")
        self.allergy_description = kwargs.pop("allergy_description")
        self.allergen_reference_system = kwargs.pop("allergen_reference_system")
        self.allergen_reference = kwargs.pop("allergen_reference")
        self.status_id = kwargs.pop("status_id")
        self.status_description = kwargs.pop("status_description")
        self.diagnosis_datetime = kwargs.pop("diagnosis_datetime")
        self.allergy_start_datetime = kwargs.pop("allergy_start_datetime")


class ResultMessage(MessageType):
    def __init__(self, **kwargs):
        self.lab_number = kwargs.pop("lab_number")
        self.profile_code = kwargs.pop("profile_code")
        self.request_datetime = kwargs.pop("request_datetime")
        self.observation_datetime = kwargs.pop("observation_datetime")
        self.last_edited = kwargs.pop("last_edited")
        self.result_status = kwargs.pop("result_status")
        self.observations = kwargs.pop("observations")


class InpatientEpisodeMessage(MessageType):
    def __init__(
        self,
        **kwargs
    ):
        self.ward_code = kwargs.pop("ward_code")
        self.room_code = kwargs.pop("room_code")
        self.bed_code = kwargs.pop("bed_code")
        self.visit_number = kwargs.pop("visit_number")
        self.datetime_of_admission = kwargs.pop("datetime_of_admission")
        self.datetime_of_discharge = kwargs.pop("datetime_of_discharge")


class InpatientEpisodeTransferMessage(InpatientEpisodeMessage):
    def __init__(
        self,
        **kwargs
    ):
        self.datetime_of_transfer = kwargs.pop("datetime_of_transfer")
        super(InpatientEpisodeTransferMessage, self).__init__(**kwargs)


class InpatientEpisodeDeleteMessage(MessageType):
    def __init__(
        self,
        **kwargs
    ):
        self.visit_number = kwargs.pop("visit_number")
        self.datetime_of_deletion = kwargs.pop("datetime_of_deletion")


class PatientIdentifierMessage(MessageType):
    pass
