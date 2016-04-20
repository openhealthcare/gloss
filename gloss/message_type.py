from collections import defaultdict


"""
gloss.message_type contains the core Gloss Archetypes
"""
class MessageContainer(object):
    def __init__(self, messages, hospital_number, issuing_source):
        self.messages = messages
        self.hospital_number = hospital_number
        self.issuing_source = issuing_source

    def to_dict(self):
        serialised_messages = defaultdict(list)

        for message in self.messages:
            serialised_messages[message.message_name].append(message.to_dict())

        result = {"issuing_source": self.issuing_source}
        result["hospital_number"] = self.hospital_number
        result["messages"] = serialised_messages
        return result


def construct_message_container(someMessages, hospital_number):
    message_container = MessageContainer(
        messages=someMessages,
        hospital_number=hospital_number,
        issuing_source="uclh",
    )
    return message_container


class MessageType(object):
    message_name = "name me Larry"

    def to_dict(self):
        result = {}

        def to_dict_or_not_to_dict(some_value):
            if hasattr(some_value, "to_dict"):
                return some_value.to_dict()
            else:
                return some_value

        if hasattr(self, "__name__"):
            return self.__name__

        for key, value in vars(self).iteritems():
            if isinstance(value, dict):
                result[key] = {
                    i: to_dict_or_not_to_dict(v) for i, v in value.iteritems()
                }
            elif hasattr(value, "__iter__"):
                result[key] = []
                result[key] = [to_dict_or_not_to_dict(i) for i in value]
            else:
                result[key] = to_dict_or_not_to_dict(value)

        return result


class PatientMessage(MessageType):
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


class PatientMergeMessage(PatientMessage):
    message_name = "duplicate_patient"

    def __init__(self, **kwargs):
        self.new_id = kwargs.pop("new_id")


class AllergyMessage(MessageType):
    message_name = "allergies"

    def __init__(
        self, **kwargs
    ):
        self.no_allergies = kwargs.pop("no_allergies")

        if not self.no_allergies:
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

    def to_dict(self):
        as_dict = super(ResultMessage, self).to_dict()
        as_dict["external_identifier"] = "{0}.{1}".format(
            self.lab_number,
            self.profile_code
        )
        return as_dict


class OrderMessage(MessageType):
    message_name = "orders"

    def __init__(self, **kw):
        """
        Even though we don't currently deal with these, e.g.
        Message Processors expect one to exist.
        """


class InpatientAdmissionMessage(MessageType):
    message_name = "inpatient_admission"

    def __init__(
        self,
        **kwargs
    ):
        self.ward_code = kwargs.pop("ward_code")
        self.room_code = kwargs.pop("room_code")
        self.bed_code = kwargs.pop("bed_code")
        self.external_identifier = kwargs.pop("external_identifier")
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
        self.external_identifier = kwargs.pop("external_identifier")
        self.datetime_of_deletion = kwargs.pop("datetime_of_deletion")
