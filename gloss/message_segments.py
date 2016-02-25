from datetime import datetime

DATETIME_FORMAT = "%Y%m%d%H%M"
DATE_FORMAT = "%Y%m%d"

class Segment(object):
    pass

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


class ResultsPID(Segment):
    """
        the pid definition used by the WINPATH systems
    """
    def __init__(self, segment):
        self.nhs_number = segment[2][0]
        if isinstance(self.nhs_number, list):
            self.nhs_number = self.nhs_number[0][0]
        self.hospital_number = segment[3][0][0][0]
        self.surname = segment[5][0][0][0]
        self.forename = segment[5][0][1][0]
        self.date_of_birth = datetime.strptime(
            segment[7][0][:8], DATE_FORMAT
        ).date()
        self.gender = segment[8][0]


class InpatientPID(Segment):
    """
        the pid definition used by CARECAST systems
    """
    def __init__(self, segment):

        self.hospital_number = segment[3][0][0][0]

        if len(segment[3][1][0][0]):
            self.nhs_number = segment[3][1][0][0]
        else:
            self.nhs_number = None

        self.surname = segment[5][0][0][0]
        self.forename = segment[5][0][1][0]
        self.date_of_birth = datetime.strptime(
            segment[7][0][:8], DATE_FORMAT
        ).date()
        self.gender = segment[8][0]

        # this is used by spell delete
        # it seems similar to our episode id
        self.patient_account_number = segment[18][0]

        if len(segment[29][0]):
            self.date_of_death = datetime.strptime(
                segment[29][0], DATE_FORMAT
            ).date()

        if len(segment[30][0]):
            self.death_indicator = segment[30][0]


class AllergiesPID(Segment):
    """
        the pid definition used by allergies
    """

    def __init__(self, segment):
        self.hospital_number = segment[3][0][0][0]
        self.surname = segment[5][0][0][0]
        self.forename = segment[5][0][1][0]
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
    STATUSES = {
        'F': 'FINAL',
        'I': 'INTERIM',
        'A': 'SOME RESULTS AVAILABLE'
    }
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

        self.result_status = OBR.STATUSES[segment[25][0]]


class OBX(Segment):
    STATUSES = {
        'F': 'FINAL',
        'I': 'INTERIM'
    }

    def __init__(self, segment):
        self.test_code = segment[3][0][0][0]
        self.test_name = segment[3][0][1][0]
        self.observation_value = segment[5][0]
        self.units = segment[6][0]
        self.reference_range = segment[7][0]
        self.result_status = OBX.STATUSES[segment[11][0]]


class EVN(Segment):
    def __init__(self, segment):
        self.event_type = segment[1][0]
        self.recorded_datetime = datetime.strptime(
            segment[2][0][:12], DATETIME_FORMAT
        )

        self.event_description = segment[4][0]


class PV1(Segment):
    EPISODE_TYPES = {
        "A": "DAY CASE",
        "I": "INPATIENT",
        "E": "EMERGENCY",
    }

    def __init__(self, segment):
        self.ward_code = segment[3][0][0][0]
        self.room_code = segment[3][0][1][0]
        self.bed_code = segment[3][0][2][0]
        self.datetime_of_admission = datetime.strptime(
            segment[44][0], DATETIME_FORMAT
        )

        self.episode_type = self.EPISODE_TYPES[segment[2][0]]

        if len(segment) > 44 and len(segment[45][0]):
            self.datetime_of_discharge = datetime.strptime(
                segment[45][0], DATETIME_FORMAT
            )


class NTE(Segment):
    def __init__(self, segments):
        self.comments = "\n".join(
            s[3][0] for s in segments
        )


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
