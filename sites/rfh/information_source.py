from gloss.information_source import InformationSource as BaseInformationSource
from collections import defaultdict

import pytds

from gloss.conf import settings
from gloss import message_type

TABLE_NAME = "something"


class InvalidAssumption(Exception):
    pass


class InformationSource(BaseInformationSource):

    def get_or_fallback(self, row, primary_field, secondary_field):
        """ look at one field, if its empty, use a different field
        """
        # we use Cerner information if it exists, otherwise
        # we fall back to winpath demograhpics
        # these are combined in the same table
        # so we fall back to a different
        # field name in the same row
        result = row.get(primary_field)

        if not result:
            result = row.get(secondary_field, "")

        return result

    def cast_row_to_patient(self, row):
        sex_abbreviation = self.get_or_fallback(row, "CRS_SEX", "SEX")

        if sex_abbreviation == "M":
            sex = "Male"
        else:
            sex = "Female"

        dob = self.get_or_fallback(row, "CRS_DOB", "date_of_birth")
        if dob:
            dob = dob.date()

        return message_type.PatientMessage(
            surname=self.get_or_fallback(row, "CRS_Surname", "Surname"),
            first_name=self.get_or_fallback(row, "CRS_Forename1", "Firstname"),
            sex=sex,
            title=self.get_or_fallback(row, "CRS_Title", "title"),
            date_of_birth=dob
        )

    def cast_row_to_observation(self, row):
        status_abbr = row.get("OBX_Status")

        if status_abbr == 'F':
            status = "Final"
        else:
            status = "Interim"
        return message_type.ObservationMessage(
            test_code=row.get("OBX_exam_code_ID"),
            test_name=row.get("OBX_exam_code_Text"),
            observation_value=row.get("Result_Value"),
            units=row.get("Result_Units"),
            result_status=status,
            reference_range=row.get("Result_Range"),
            external_identifier=str(row.get("OBX_id")),
        )

    def cast_rows_to_result_message(self, grouped_rows):
        observations = [
            self.cast_row_to_observation(row) for row in grouped_rows
        ]
        last_row = grouped_rows[-1]
        status_abbr = row.get("OBR_Status")

        if status_abbr == 'F':
            status = "Final"
        else:
            status = "Interim"

        return message_type.ResultMessage(
            lab_number=self.get_unique_result_identifier(last_row),
            profile_code=last_row.get("OBR_exam_code_ID"),
            profile_description=last_row.get("OBR_exam_code_Text"),
            request_datetime=last_row.get("Request_Date"),
            # there's Date of observation and observation datetime
            # and they're different TODO check this
            observation_datetime=last_row.get("Date_of_the_Observation"),
            last_edited=last_row.get("last_updated"),
            observations=observations,
            result_status=status
        )

    def get_unique_result_identifier(self, row):
        return "{0}_{1}".format(row["Result_ID"], row["OBR_Sequence_ID"])

    def get_results_and_observations(self, rows):
        # going through the result_id seems to be the set id of the OBR
        # the set id is not unique as there can be multiple OBRs, even of the
        # same type, but we can use the set id and the sequence id to create a unique
        # reference...
        # TODO double check this is correct and not just a feature of the
        # test data

        grouped = defaultdict(list)
        for row in rows:
            grouped[self.get_unique_result_identifier(row)].append(row)

        for rows in grouped.values():
            only_one_test = {i["OBR_exam_code_ID"] for i in rows}
            if(not len(only_one_test) == 1):
                err_message = "we expected only one type of test for a result id"
                err_message += "for {} we received multiple".format(row["Result_ID"])
                raise InvalidAssumption(err_message)

        messages = []

        for grouped_rows in grouped.values():
            messages.append(self.cast_rows_to_result_message(grouped_rows))

        return messages

    def get_rows(self, hospital_number):
        username = settings.UPSTREAM_DB["USERNAME"]
        password = settings.UPSTREAM_DB["PASSWORD"]
        ip_address = settings.UPSTREAM_DB["IP_ADDRESS"]
        database = settings.UPSTREAM_DB["DATABASE"]
        table_name = settings.UPSTREAM_DB["TABLE_NAME"]

        # query the test view
        query = """
        select * from {0} where Patient_Number='{1}' ORDER BY Event_Date
        """.format(table_name, hospital_number)

        with pytds.connect(ip_address, database, username, password, as_dict=True) as conn:
            with conn.cursor() as cur:
                cur.execute(query.strip())
                result = cur.fetchall()

        return result

    def result_information(self, issuing_identifier, hospital_number):
        rows = self.get_rows(hospital_number)
        if len(rows):
            messages = self.get_results_and_observations(rows)
        else:
            messages = []
        return message_type.MessageContainer(
            hospital_number=hospital_number,
            issuing_source="rfh",
            messages=messages
        )

    def patient_information(self, issuing_source, hospital_number):
        rows = self.get_rows(hospital_number)
        if len(rows):
            messages = self.get_results_and_observations(rows)
            messages.append(self.cast_row_to_patient(rows[-1]))
        else:
            messages = []
        return message_type.MessageContainer(
            hospital_number=hospital_number,
            issuing_source="rfh",
            messages=messages
        )


class InformatinSourceOnTest(InformationSource):
    def get_rows(self, hospital_number):
        """
            a temporary source that essentially mocks up the external db with json
        """
        from sites.rfh.test_database_constructor.pathology_data import PATHOLOGY_DATA
        return [y for y in PATHOLOGY_DATA if y["Patient_Number"] == hospital_number]
