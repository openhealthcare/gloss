from datetime import datetime
from twisted.python import log
from collections import namedtuple
from coded_values import (
    RELIGION_MAPPINGS, SEX_MAPPING, MARITAL_STATUSES_MAPPING,
    TEST_STATUS_MAPPING, ADMISSION_TYPES, OBX_STATUSES,
    ETHNICITY_MAPPING,
)
from copy import copy

DATETIME_FORMAT = "%Y%m%d%H%M"
DATE_FORMAT = "%Y%m%d"


def get_field_name(message_row):
    return message_row[0][0].upper()


def clean_until(message, field):
    for index, row in enumerate(message):
        if get_field_name(row) == field:
            return message[index+1:]


class Segment(object):
    @classmethod
    def name(cls):
        return cls.__name__.upper()

    def __init__(self, segment):
        self.segment = segment


class Hl7Field(object):
    def __init__(self, *indexes, **kwargs):
        self.indexes = indexes
        self.required = kwargs.pop("required", True)

    def __get__(self, obj, cls):
        result = obj.segment

        for i in self.indexes:
            if not self.required:
                if len(result) <= i or not result[i]:
                    return None

            result = result[i]

        return result


class DateTimeHl7Field(Hl7Field):
    def __get__(self, *args):
        result = super(DateTimeHl7Field, self).__get__(*args)

        if not self.required and not result:
            return result

        return datetime.strptime(result, DATETIME_FORMAT)


class DateHl7Field(Hl7Field):
    def __get__(self, *args):
        result = super(DateHl7Field, self).__get__(*args)

        if not self.required and not result:
            return result

        return datetime.strptime(result, DATE_FORMAT).date()


class MSH(Segment):
    trigger_event = Hl7Field(9, 0, 1, 0)
    message_type = Hl7Field(9, 0, 0, 0)
    message_datetime = DateTimeHl7Field(7, 0)
    sending_application = Hl7Field(3, 0)
    sending_facility = Hl7Field(4, 0)


class MsaField(Hl7Field):
    def __get__(self, *args):
        result = super(MsaField, self).__get__(*args)
        if result == "Call Successful":
            return None
        else:
            return result


class MSA(Segment):
    error_code = MsaField(3, 0)


class MRG(Segment):
    duplicate_hospital_number = Hl7Field(1, 0, 0, 0)


class ORC(Segment):
    pass


class UpdatePD1(Segment):

    @classmethod
    def name(cls):
        return "PD1"

    gp_practice_code = Hl7Field(4, 1, 0, 0)


class QueryPD1(Segment):
    @classmethod
    def name(cls):
        return "PD1"

    gp_practice_code = Hl7Field(3, 0, 2, 0)


class ResultsPID(Segment):
    """
        the pid definition used by the WINPATH systems
    """
    @classmethod
    def name(cls):
        return "PID"

    hospital_number = Hl7Field(3, 0, 0, 0)
    surname = Hl7Field(5, 0, 0, 0)
    first_name = Hl7Field(5, 0, 1, 0)
    date_of_birth = DateHl7Field(7, 0, required=False)
    gender = Hl7Field(8, 0)

    def __init__(self, segment):
        super(ResultsPID, self).__init__(segment)
        self.nhs_number = segment[2][0]
        if isinstance(self.nhs_number, list):
            self.nhs_number = self.nhs_number[0][0]


class InpatientPID(Segment):
    """
        the pid definition used by CARECAST systems
    """
    hospital_number = Hl7Field(3, 0, 0, 0)
    nhs_number = Hl7Field(3, 1, 0, 0, required=False)
    surname = Hl7Field(5, 0, 0, 0)
    first_name = Hl7Field(5, 0, 1, 0)
    middle_name = Hl7Field(5, 0, 2, 0)
    title = Hl7Field(5, 0, 4, 0)
    date_of_birth = DateHl7Field(7, 0)

    # this is used by spell delete
    # it seems similar to our admission id
    patient_account_number = Hl7Field(18, 0)
    post_code = Hl7Field(11, 0, 4, 0)
    date_of_death = DateHl7Field(29, 0, required=False)

    @classmethod
    def name(cls):
        return "PID"

    def __init__(self, segment):
        super(InpatientPID, self).__init__(segment)
        self.sex = SEX_MAPPING.get(segment[8][0], None)
        self.religion = RELIGION_MAPPINGS.get(segment[17][0], None)
        self.marital_status = MARITAL_STATUSES_MAPPING.get(
            segment[16][0], None
        )
        self.ethnicity = ETHNICITY_MAPPING.get(
            segment[22][0], None
        )

        self.death_indicator = None
        if len(segment[30][0]):
            if segment[30][0] == "Y":
                self.death_indicator = True
            elif segment[30][0] == "N":
                self.death_indicator = False


class AllergiesPID(Segment):
    """
        the pid definition used by allergies
    """
    @classmethod
    def name(cls):
        return "PID"

    hospital_number = Hl7Field(3, 0, 0, 0)
    surname = Hl7Field(5, 0, 0, 0)
    first_name = Hl7Field(5, 0, 1, 0)
    date_of_birth = DateHl7Field(7, 0, required=False)

    # sample messages record 2 different types of
    # message "No Known Allergies" and
    # "Allergies Known and Recorde" we're
    # querying as to whether there are others
    allergy_status = Hl7Field(37, 0)


    def __init__(self, segment):
        super(AllergiesPID, self).__init__(segment)
        # TODO this is wrong, it should probably be looking up the answer
        self.gender = segment[8][0]


class OBR(Segment):
    lab_number = Hl7Field(3, 0)
    profile_code = Hl7Field(4, 0, 0, 0)
    profile_description = Hl7Field(4, 0, 1, 0)
    request_datetime = DateTimeHl7Field(6, 0)
    observation_datetime = DateTimeHl7Field(7, 0)
    last_edited = DateTimeHl7Field(22, 0)

    def __init__(self, segment):
        super(OBR, self).__init__(segment)
        self.result_status = TEST_STATUS_MAPPING[segment[25][0]]



class OBX(Segment):
    value_type = Hl7Field(2, 0)
    set_id = Hl7Field(1, 0)
    test_name = Hl7Field(3, 0, 1, 0)
    observation_value = Hl7Field(5, 0)
    units = Hl7Field(6, 0, required=False)
    reference_range = Hl7Field(7, 0, required=False)

    def __init__(self, segment):
        super(OBX, self).__init__(segment)
        self.test_code = segment[3][0][0][0].replace("\\S\\", "^")

        if len(segment) > 12 and segment[11][0]:
            self.result_status = OBX_STATUSES[segment[11][0]]
        else:
            self.result_status = None

    @classmethod
    def get_segments(cls, segments):
        return [cls(segment) for segment in segments]


class EVN(Segment):
    event_type = Hl7Field(1, 0)
    recorded_datetime = DateTimeHl7Field(2, 0)
    planned_datetime = DateTimeHl7Field(3, 0)
    event_description = Hl7Field(4, 0)


class ResultsPV1(Segment):
    @classmethod
    def name(cls):
        return "PV1"


class PV1(Segment):
    ward_code = Hl7Field(3, 0, 0, 0, required=False)
    room_code = Hl7Field(3, 0, 1, 0, required=False)
    bed_code = Hl7Field(3, 0, 2, 0, required=False)
    datetime_of_admission = DateTimeHl7Field(44, 0)
    datetime_of_discharge = DateTimeHl7Field(45, 0, required=False)

    def __init__(self, segment):
        super(PV1, self).__init__(segment)
        try:
            self.admission_type = ADMISSION_TYPES[segment[2][0]]
        except:
            self.admission_types = None


class PV2(Segment):
    admission_diagnosis = Hl7Field(3, 0)


class NTE(Segment):
    comments = Hl7Field(3, 0)
    set_id = Hl7Field(1, 0)


class AL1(Segment):

    # there's a good chance we won't need
    # all these fields, but they
    # raise a lot of questions
    allergy_type = Hl7Field(2, 0, 0, 0)
    allergy_type_description = Hl7Field(2, 0, 1, 0)
    certainty_id = Hl7Field(2, 0, 3, 0)
    certainty_description = Hl7Field(2, 0, 4, 0)
    allergy_reference_name = Hl7Field(3, 0, 0, 0)
    allergy_description = Hl7Field(3, 0, 1, 0)
    allergen_reference_system = Hl7Field(3, 0, 2, 0, required=False)
    allergen_reference = Hl7Field(3, 0, 3, 0, required=False)
    status_id = Hl7Field(4, 0, 0, 0)
    status_description = Hl7Field(4, 0, 1, 0)
    diagnosis_datetime = DateTimeHl7Field(4, 0, 4, 0)
    allergy_start_datetime = DateTimeHl7Field(6, 0)


class HL7Base(object):
    def get_method_for_field(self, field):
        for i in self.segments:
            if not i.__class__ == RepeatingField:
                if i.name() == field:
                    return i
        raise ValueError("unable to find a setter for {}".format(field))


class RepeatingField(HL7Base):
    def __init__(self, *segments, **kwargs):
        self.segments = segments
        self.section_name = kwargs.pop("section_name")
        self.repeated_class = namedtuple(
            self.section_name, self.get_segment_names()
        )
        self.required = kwargs.pop("required", True)

    def get_segment_names(self):
        result = []
        for segment in self.segments:
            if segment.__class__.__name__ == "RepeatingField":
                result.append(segment.section_name)
            else:
                result.append(segment.name().lower())
        return result

    def get(self, passed_message):
        found_repeaters = []
        kwargs = {}
        message = copy(passed_message)
        found = True

        while len(message) and found:
            for index, segment in enumerate(self.segments):
                if segment.__class__.__name__ == "RepeatingField":
                    repeated_fields, stripped_message = segment.get(
                        message
                    )

                    message = stripped_message
                    kwargs[segment.section_name] = repeated_fields
                else:
                    msg_segment = message[0]
                    if get_field_name(msg_segment) == segment.name():
                        mthd = self.get_method_for_field(segment.name())
                        kwargs[segment.name().lower()] = mthd(msg_segment)
                        message = clean_until(message, segment.name())

                if index == len(self.segments) - 1:
                    # we haven't found the response if we can't fulfill
                    # all the segments, this means that
                    # the non repeating field kwargs aren't there
                    # and the repeating fields are empty
                    if any(kwargs.itervalues()):
                        found_repeaters.append(self.repeated_class(**kwargs))
                        kwargs = {}
                    else:
                        found = False

        if found_repeaters:
            return (found_repeaters, message,)
        else:
            return (found_repeaters, passed_message,)


class HL7Message(HL7Base):
    def __init__(self, raw_message):
        message = copy(raw_message)

        for field in self.segments:
            if field.__class__ == RepeatingField:
                found_repeaters, message = field.get(message)
                setattr(self, field.section_name, found_repeaters)
            else:
                mthd = self.get_method_for_field(field.name())
                try:
                    setattr(self, field.name().lower(), mthd(message.segment(field.name())))
                except KeyError:
                    log.msg("unable to find {0} for {1}".format(field.name(), raw_message))
                    raise
                message = clean_until(message, field.name())
