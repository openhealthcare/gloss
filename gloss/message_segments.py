from datetime import datetime
from twisted.python import log
import exceptions
from collections import namedtuple
from coded_values import (
    RELIGION_MAPPINGS, SEX_MAPPING, MARITAL_STATUSES_MAPPING,
    TEST_STATUS_MAPPING, EPISODE_TYPES, OBX_STATUSES,
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


class MSH(Segment):
    def __init__(self, segment):
        self.trigger_event = segment[9][0][1][0]
        self.message_type = segment[9][0][0][0]
        # allergy information contains milli seconds, lets strip that
        # off for the time being
        self.message_datetime = datetime.strptime(segment[7][0][:12], DATETIME_FORMAT)
        self.sending_application = segment[3][0]
        self.sending_facility = segment[4][0]


class MRG(Segment):
    def __init__(self, segment):
        self.duplicate_hospital_number = segment[1][0][0][0]


class ORC(Segment):
    def __init__(self, segment):
        pass


class PD1(Segment):
    def __init__(self, segment):
        self.gp_practice_code = segment[4][1][0][0]


class ResultsPID(Segment):
    """
        the pid definition used by the WINPATH systems
    """
    @classmethod
    def name(cls):
        return "PID"

    def __init__(self, segment):
        self.nhs_number = segment[2][0]
        if isinstance(self.nhs_number, list):
            self.nhs_number = self.nhs_number[0][0]
        self.hospital_number = segment[3][0][0][0]
        self.surname = segment[5][0][0][0]
        self.first_name = segment[5][0][1][0]

        self.date_of_birth = datetime.strptime(
            segment[7][0][:8], DATE_FORMAT
        ).date()
        self.gender = segment[8][0]

class InpatientPID(Segment):
    """
        the pid definition used by CARECAST systems
    """

    @classmethod
    def name(cls):
        return "PID"

    def __init__(self, segment):

        self.hospital_number = segment[3][0][0][0]

        if len(segment[3][1][0][0]):
            self.nhs_number = segment[3][1][0][0]
        else:
            self.nhs_number = None

        self.surname = segment[5][0][0][0]
        self.first_name = segment[5][0][1][0]
        self.middle_name = segment[5][0][2][0]
        self.title = segment[5][0][4][0]
        self.date_of_birth = datetime.strptime(
            segment[7][0][:8], DATE_FORMAT
        ).date()

        self.sex = SEX_MAPPING.get(segment[8][0], None)

        self.religion = RELIGION_MAPPINGS.get(segment[17][0], None)

        # this is used by spell delete
        # it seems similar to our episode id
        self.patient_account_number = segment[18][0]
        self.marital_status = MARITAL_STATUSES_MAPPING.get(
            segment[16][0], None
        )
        self.ethnicity = ETHNICITY_MAPPING.get(
            segment[22][0], None
        )

        self.post_code = segment[11][0][4][0]

        if len(segment[29][0]):
            self.date_of_death = datetime.strptime(
                segment[29][0], DATE_FORMAT
            ).date()
        else:
            self.date_of_death = None

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

    def __init__(self, segment):
        self.hospital_number = segment[3][0][0][0]
        self.surname = segment[5][0][0][0]
        self.first_name = segment[5][0][1][0]
        self.date_of_birth = datetime.strptime(
            segment[7][0][:8], DATE_FORMAT
        ).date()
        self.gender = segment[8][0]

        # sample messages record 2 different types of
        # message "No Known Allergies" and
        # "Allergies Known and Recorde" we're
        # querying as to whether there are others
        self.allergy_status = segment[37][0]


class OBR(Segment):

    def __init__(self, segment):
        self.lab_number = segment[3][0]
        self.profile_code = segment[4][0][0][0]
        self.profile_description = segment[4][0][1][0]
        self.request_datetime = datetime.strptime(
            segment[6][0][:12], DATETIME_FORMAT
        )
        self.observation_datetime = datetime.strptime(
            segment[7][0][:12], DATETIME_FORMAT
        )

        self.last_edited = datetime.strptime(
            segment[22][0], DATETIME_FORMAT
        )

        self.result_status = TEST_STATUS_MAPPING[segment[25][0]]



class OBX(Segment):
    def __init__(self, segment):
        self.value_type = segment[2][0]
        self.set_id = segment[1][0]
        self.test_code = segment[3][0][0][0].replace("\\S\\", "^")
        self.test_name = segment[3][0][1][0]
        self.observation_value = segment[5][0]

        if segment[6][0]:
            self.units = segment[6][0]
        else:
            self.units = None

        if len(segment) > 8 and segment[7][0]:
            reference_range = segment[7][0]
            self.reference_range = reference_range
        else:
            self.reference_range = None

        if len(segment) > 12 and segment[11][0]:
            self.result_status = OBX_STATUSES[segment[11][0]]
        else:
            self.result_status = None

    @classmethod
    def get_segments(cls, segments):
        return [cls(segment) for segment in segments]


class EVN(Segment):
    def __init__(self, segment):
        self.event_type = segment[1][0]
        self.recorded_datetime = datetime.strptime(
            segment[2][0][:12], DATETIME_FORMAT
        )
        planned_datetime = segment[3][0]

        if planned_datetime:
            self.planned_datetime = datetime.strptime(
                planned_datetime[:12], DATETIME_FORMAT
            )

        self.event_description = segment[4][0]


class ResultsPV1(Segment):
    @classmethod
    def name(cls):
        return "PV1"

    def __init__(self, segment):
        pass


class PV1(Segment):
    def __init__(self, segment):
        try:
            self.ward_code = segment[3][0][0][0]
        except IndexError:
            self.ward_code = None
        try:
            self.room_code = segment[3][0][1][0]
        except IndexError:
            self.room_code = None

        try:
            self.bed_code = segment[3][0][2][0]
        except IndexError:
            self.bed_code = None

        self.datetime_of_admission = datetime.strptime(
            segment[44][0][:12], DATETIME_FORMAT
        )

        try:
            self.episode_type = EPISODE_TYPES[segment[2][0]]
        except:
            self.episode_types = None

        if len(segment) > 45 and segment[45] and segment[45][0]:
            self.datetime_of_discharge = datetime.strptime(
                segment[45][0][:12], DATETIME_FORMAT
            )
        else:
            self.datetime_of_discharge = None


class PV2(Segment):
    def __init__(self, segment):
        self.admission_diagnosis = segment[3][0]


class NTE(Segment):
    def __init__(self, segment):
        self.comments = segment[3][0]
        self.set_id = segment[1][0]


class AL1(Segment):
    # there's a good chance we won't need
    # all these fields, but they
    # raise a lot of questions
    def __init__(self, segments):
        self.allergy_type = segments[2][0][0][0]
        self.allergy_type_description = segments[2][0][1][0]
        self.certainty_id = segments[2][0][3][0]
        self.certainty_description = segments[2][0][4][0]
        self.allergy_reference_name = segments[3][0][0][0]
        self.allergy_description = segments[3][0][1][0]
        self.allergen_reference_system = segments[3][0][2][0]
        self.allergen_reference = segments[3][0][3][0]
        self.status_id = segments[4][0][0][0]
        self.status_description = segments[4][0][1][0]
        self.diagnosis_datetime = datetime.strptime(
            segments[4][0][4][0], DATETIME_FORMAT
        )
        self.allergy_start_datetime = datetime.strptime(
            segments[6][0], DATETIME_FORMAT
        )


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
                except exceptions.KeyError:
                    log.msg("unable to find {0} for {1}".format(field.name(), raw_message))
                    raise
                message = clean_until(message, field.name())
