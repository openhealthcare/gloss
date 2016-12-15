from sites.rfh.test_database_constructor.database import get_connection, create_database
from sites.rfh.test_database_constructor.pathology_data import PATHOLOGY_DATA
import datetime

TABLE_NAME = 'tQuest_Pathology_Result_View'

VARCHAR_50 = "VARCHAR(50)"
VARCHAR_255 = "VARCHAR(255)"
VARCHAR_10 = "VARCHAR(10)"
VARCHAR_100 = "VARCHAR(100)"
VARCHAR_1 = "VARCHAR(1)"
VARCHAR_MAX = "VARCHAR"
INT = "INT"
DATETIME = "TIMESTAMP"


PATHOLOGY_TABLE = {
    "id": INT,
    "crs_patient_masterfile_id": INT,
    "Event_Date": DATETIME,
    "MSH_Control_ID": VARCHAR_50,
    "Patient_Number": VARCHAR_50,
    "Patient_ID_External": VARCHAR_50,
    "Surname": VARCHAR_50,
    "Firstname": VARCHAR_50,
    "DOB": DATETIME,
    "SEX": VARCHAR_1,
    "Order_Number": VARCHAR_50,
    "Result_ID": VARCHAR_50,
    "Visit_Number": VARCHAR_50,
    "Accession_number": VARCHAR_50,
    "Department": VARCHAR_50,
    "OBR_Sequence_ID": VARCHAR_50,
    "OBR_exam_code_ID": VARCHAR_50,
    "OBR_exam_code_Text": VARCHAR_50,
    "Request_Date": DATETIME,
    "Observation_date": DATETIME,
    "Reported_date": DATETIME,
    "Requesting_Clinician": VARCHAR_50, # Clinician on Cerner to send result back to on Message Centre
    "Encounter_Consultant_Code": VARCHAR_255,
    "Encounter_Consultant_Name": VARCHAR_255,  # Can be encounter consultant from Cerner or GP or external clinician e.g. RNOH
    "Encounter_Consultant_Type": VARCHAR_50,
    "Encounter_Location_Code": VARCHAR_50,  # H29 split into component parts
    "Encounter_Location_Name": VARCHAR_50,  # H29 split into component parts
    "Encounter_Location_Type": VARCHAR_50,  # H29 split into component parts
    "Patient_Class": VARCHAR_50,  # Patient Category eg NHS
    "OBR-5_Priority": VARCHAR_50,
    "OBR_Status": VARCHAR_50, # Final (F) or interim (I)
    "Specimen_Site": VARCHAR_50,
    "ORC-9_Datetime_of_Transaction": DATETIME,
    "Relevant_Clinical_Info": VARCHAR_MAX,
    "visible": VARCHAR_1,  # Local flat to exclude results (ie errors) Y if result is valid
    "date_inserted": DATETIME,  # Date result inserted in SQL Server
    "last_updated": DATETIME,  # No longer used
    "OBX_Sequence_ID": VARCHAR_10,  # Display ordering of result elements
    "OBX_exam_code_ID": VARCHAR_50,  # Individual exam codes
    "OBX_exam_code_Text": VARCHAR_50,  # Individual exam code description
    "Result_Value": VARCHAR_MAX,  # Result can be numeric or text, multiple text lines serpated by '~' to signify carriage return
    "Result_Units": VARCHAR_100,
    "Result_Range": VARCHAR_100,
    "Abnormal_Flag": VARCHAR_50,  # High or Low
    "OBX_Status": VARCHAR_100,  # Final(F) or Interim (I)
    "Date_Last_Obs_Normal": DATETIME,
    "Date_of_the_Observation": DATETIME,
    "OBX_id": INT,
}


def create_table():
    columns = ", ".join('"{0}" {1}'.format(k, v) for k, v in PATHOLOGY_TABLE.iteritems())
    command = "CREATE TABLE IF NOT EXISTS {0} ( {1} );".format(TABLE_NAME, columns)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(command)


def drop_table():
    command = "DROP TABLE {}".format(TABLE_NAME)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(command)


def insert_data():
    with get_connection() as conn:
        cur = conn.cursor()
        for row in PATHOLOGY_DATA:
            column_names = row.keys()
            sql_column_names = ", ".join('"{}"'.format(k) for k in column_names)
            values = []

            for column in column_names:
                value = row[column]
                if value is None:
                    value = 'NULL'
                elif isinstance(value, datetime.datetime):
                    value = "'%s'" % value
                else:
                    if isinstance(value, int):
                        value = str(value)
                    elif not len(value):
                        value = ""
                    value = "'{}'".format(value)

                values.append(value)

            value_strings = ", ".join(values)

            insert_statement = "INSERT INTO {0} ({1}) VALUES ({2})".format(
                TABLE_NAME, sql_column_names, value_strings
            )
            cur.execute(insert_statement)

def setup():
    create_database()
    drop_table()
    create_table()
    insert_data()
