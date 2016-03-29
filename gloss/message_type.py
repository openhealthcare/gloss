"""
gloss.message_type contains the core Gloss Archetypes
"""

def to_dict(some_obj):
    if hasattr(some_obj, "__name__"):
        return some_obj.__name__

    if hasattr(some_obj, "to_dict"):
        return some_obj.to_dict()

    if isinstance(some_obj, dict):
        return {
            field: to_dict(value) for field, value in some_obj.iteritems()
        }
    if hasattr(some_obj, "__dict__"):
        fields = vars(some_obj)
        return {
            field: to_dict(value) for field, value in fields.iteritems()
        }
    if hasattr(some_obj, "__iter__"):
        return [to_dict(i) for i in some_obj]
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
        result = {"issuing_source": self.issuing_source}
        result["hospital_number"] = self.hospital_number
        result["messages"] = {
            self.message_type.message_name: to_dict(self.messages)
        }
        return result


class MessageType(object):
    message_name = "name me Larry"


class PatientMergeMessage(MessageType):
    message_name = "duplicate_patient"

    def __init__(self, **kwargs):
        self.old_id = kwargs.pop("old_id")


class PatientUpdateMessage(MessageType):
    message_name = "demographics"

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
    message_name = "allergies"

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
    message_name = "result"

    def __init__(self, **kwargs):
        self.lab_number = kwargs.pop("lab_number")
        self.profile_code = kwargs.pop("profile_code")
        self.profile_description = kwargs.pop("profile_description")
        self.request_datetime = kwargs.pop("request_datetime")
        self.observation_datetime = kwargs.pop("observation_datetime")
        self.last_edited = kwargs.pop("last_edited")
        self.result_status = kwargs.pop("result_status", None)
        self.observations = kwargs.pop("observations")


class OrderMessage(MessageType):
    message_name = "orders"

    def __init__(self, **kw):
        """
        Even though we don't currently deal with these, e.g.
        Message Processors expect one to exist.
        """

class InpatientAdmissionMessage(MessageType):
    message_name = "inpatient_locations"

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


class InpatientAdmissionTransferMessage(InpatientAdmissionMessage):
    def __init__(
        self,
        **kwargs
    ):
        self.datetime_of_transfer = kwargs.pop("datetime_of_transfer")
        super(InpatientAdmissionTransferMessage, self).__init__(**kwargs)


class InpatientAdmissionDeleteMessage(MessageType):
    # not correct, we need to work out how this will work
    message_name = "inpatient_locations"

    def __init__(
        self,
        **kwargs
    ):
        self.visit_number = kwargs.pop("visit_number")
        self.datetime_of_deletion = kwargs.pop("datetime_of_deletion")
