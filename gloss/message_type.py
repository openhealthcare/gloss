from subscriptions import *


class MessageType(object):
    def __init__(self, hospital_number=None, issuing_source=None, **kwargs):
        if not hospital_number or not issuing_source:
            raise ValueError(
                "hospital number or issuing source need to be implemented"
            )
        self.hospital_number = hospital_number
        self.issuing_source = issuing_source

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
        super(PatientMergeMessage, self).__init__(**kwargs)


class AllergyMessage(MessageType):
    def __init__(
        self, allergies=None, no_allergies=False, **kwargs
    ):
        if not allergies and not no_allergies:
            raise ValueError(
                "we either need allergies or a reference that there are no allergies"
            )
        self.allergies = allergies
        self.no_allergies = no_allergies
        super(self, **kwargs).__init__(**kwargs)


class ResultMessage(MessageType):
    def __init__(self, **kwargs):
        self.lab_number = kwargs.pop("lab_number")
        self.profile_code = kwargs.pop("profile_code")
        self.request_datetime = kwargs.pop("request_datetime")
        self.observation_datetime = kwargs.pop("observation_datetime")
        self.last_edited = kwargs.pop("last_edited")
        self.result_status = kwargs.pop("result_status")
        self.observations = kwargs.pop("observations")
        super(ResultMessage, self).__init__(**kwargs)


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
        super(InpatientEpisodeMessage, self).__init__(**kwargs)


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
        super(InpatientEpisodeDeleteMessage, self).__init__(**kwargs)


class PatientIdentifierMessage(MessageType):
    pass
