from collections import defaultdict
import six
import itertools


class Field(object):
    def __init__(self, required=False):
        self.required = required


class GlossMessageMeta(type):
    def __new__(cls, name, bases, attrs):
        omf = set()
        rmf = set()
        # get all fields from parent classes
        parents = [b for b in bases if isinstance(b, GlossMessageMeta)]
        for kls in parents:
            omf.update(kls._optional_message_fields)
            rmf.update(kls._required_message_fields)

        # Get all the fields from this class.
        for field_name, val in attrs.items():
            if isinstance(val, Field):
                if val.required:
                    omf.discard(field_name)
                    rmf.add(field_name)
                else:
                    rmf.discard(field_name)
                    omf.add(field_name)
        attrs["_optional_message_fields"] = omf
        attrs["_required_message_fields"] = rmf

        return super(GlossMessageMeta, cls).__new__(cls, name, bases, attrs)



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


def construct_message_container(
    someMessages, hospital_number, issuing_source="uclh"
):
    message_container = MessageContainer(
        messages=someMessages,
        hospital_number=hospital_number,
        issuing_source=issuing_source,
    )
    return message_container


class MessageType(six.with_metaclass(GlossMessageMeta)):
    message_name = "name me Larry"

    def __init__(self, **kwargs):
        key_names = kwargs.keys()
        missing_required_fields = self._required_message_fields - set(key_names)

        if len(missing_required_fields):
            raise ValueError(
                "We are missing the fields %s" % missing_required_fields
            )
        all_fields = itertools.chain(
            self._optional_message_fields,
            self._required_message_fields
        )

        for field in all_fields:
            setattr(self, field, kwargs.get(field))

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

    surname = Field()
    first_name = Field()
    middle_name = Field()
    title = Field()
    date_of_birth = Field()
    sex = Field()
    marital_status = Field()
    religion = Field()
    ethnicity = Field()
    date_of_death = Field()
    death_indicator = Field()
    post_code = Field()
    gp_practice_code = Field()


class PatientMergeMessage(MessageType):
    message_name = "duplicate_patient"
    new_id = Field()


class AllergyMessage(MessageType):
    message_name = "allergies"

    def __init__(
        self, **kwargs
    ):
        # Note a special case, does not call super
        self.no_allergies = kwargs.pop("no_allergies")

        if not self.no_allergies:
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


class ObservationMessage(MessageType):
    message_name = "observation"
    value_type = Field()
    test_code = Field()
    test_name = Field()
    observation_value = Field()
    units = Field()
    reference_range = Field()
    result_status = Field()
    comments = Field()
    external_identifier = Field(required=True)


class ResultMessage(MessageType):
    message_name = "result"

    lab_number = Field()
    profile_code = Field()
    profile_description = Field()
    request_datetime = Field()
    observation_datetime = Field()
    last_edited = Field()
    result_status = Field()
    observations = Field(required=True)

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
        pass


class InpatientAdmissionMessage(MessageType):
    message_name = "inpatient_admission"

    ward_code = Field()
    room_code = Field()
    bed_code = Field()
    external_identifier = Field()
    datetime_of_admission = Field()
    datetime_of_discharge = Field()
    admission_diagnosis = Field()


class InpatientAdmissionTransferMessage(InpatientAdmissionMessage):
    datetime_of_transfer = Field()


class InpatientAdmissionDeleteMessage(MessageType):
    # not correct, we need to work out how this will work
    message_name = "inpatient_locations"

    external_identifier = Field()
    datetime_of_deletion = Field()
