"""
gloss.message_type contains the core Gloss Archetypes
"""
from subscriptions import *


def to_dict(some_obj):
    def to_dict_or_not_to_dict(child_obj):
        if hasattr(child_obj, "__name__"):
            return child_obj.__name__
        if hasattr(child_obj, "to_dict"):
            return child_obj.to_dict()
        else:
            return to_dict(child_obj)

    if isinstance(some_obj, dict):
        return {
            field: to_dict_or_not_to_dict(value) for field, value in some_obj.iteritems()
        }
    if hasattr(some_obj, "__dict__"):
        fields = vars(some_obj)
        return {
            field: to_dict_or_not_to_dict(value) for field, value in fields.iteritems()
        }
    if hasattr(some_obj, "__iter__"):
        return [to_dict_or_not_to_dict(i) for i in some_obj]
    else:
        # presumably this is nothing complicated
        return some_obj


class MessageContainer(object):
    def __init__(
        self, messages, hospital_number, issuing_source, message_type
    ):
        self.messages = messages
        self.hospital_number = hospital_number
        self.issuing_source = issuing_source
        self.message_type = message_type

    def to_dict(self):
        return to_dict(self)


class MessageType(object):
    def to_dict(self):
        return to_dict(self)

class PatientMergeMessage(MessageType):
    def __init__(self, **kwargs):
        self.old_id = kwargs.pop("old_id")


class PatientUpdateMessage(MessageType):
    def __init__(self, **kwargs):
        fields = [
            "surname", "first_name", "middle_name", "title",
            "date_of_birth", "sex", "marital_status", "religsion", "ethnicity",
            "date_of_death", "death_indicator", "post_code", "gp_practice_code"
        ]

        for field in fields:
            if field in kwargs:
                setattr(self, field, kwargs[field])


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
        self.result_status = kwargs.pop("result_status", None)
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
        self.admission_diagnosis = kwargs.pop("admission_diagnosis")


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
