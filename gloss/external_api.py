from copy import copy
from datetime import datetime

from hl7 import client
from hl7.containers import Message
import hl7

from gloss import models, exceptions, settings
from gloss.message_segments import MSH, InpatientPID, QueryPD1, MSA, HL7Message
from gloss.message_type import (
    PatientMessage, construct_message_container
)

try:
    from flask import current_app
    logger = current_app.logger
except:
    import logging
    logger = logging


class DemographicsQueryResponse(HL7Message):
    segments = (MSH, MSA, InpatientPID, QueryPD1,)


class DemographicsErrorResponse(HL7Message):
    segments = (MSH, MSA,)


def generate_message_id():
    unique_id = models.get_next_message_id()
    unique_id_length = len(str(unique_id))
    return "ELC%s%s" % (("0" * (17 - unique_id_length)), unique_id)


def generate_demographics_query_message(identifier):
    message = Message("|")
    msh = message.create_segment([message.create_field(['MSH'])])
    qrd = message.create_segment([message.create_field(['QRD'])])

    now = datetime.now()

    message_id = generate_message_id()
    query_msg = message.create_message([msh, qrd])
    query_msg.assign_field("|", "MSH", 1, 1)
    query_msg.assign_field("^~\&", "MSH", 1, 2)
    query_msg.assign_field("elcid", "MSH", 1, 3)
    query_msg.assign_field("UCLH", "MSH", 1, 4)
    query_msg.assign_field("Unicare", "MSH", 1, 5)
    query_msg.assign_field("UCLH", "MSH", 1, 6)
    query_msg.assign_field(now.strftime("%Y%m%d%H%M"), "MSH", 1, 7)
    query_msg.assign_field("QRY^A19", "MSH", 1, 9)
    query_msg.assign_field(message_id, "MSH", 1, 10)
    query_msg.assign_field("2.4", "MSH", 1, 12)

    query_msg.assign_field(now.strftime("%Y%m%d%H%M%S"), "QRD", 1, 1)
    query_msg.assign_field("R", "QRD", 1, 2)
    query_msg.assign_field("I", "QRD", 1, 3)
    query_msg.assign_field(message_id, "QRD", 1, 4)
    query_msg.assign_field("1^RD", "QRD", 1, 7, 1)
    query_msg.assign_field(identifier, "QRD", 1, 8, 1)
    query_msg.assign_field("DEM", "QRD", 1, 9)
    return query_msg


def send_message(some_message):
    with client.MLLPClient(settings.DEMOGRAPHICS_HOST, settings.DEMOGRAPHICS_PORT) as c:
        response = c.send_message(some_message)
    return response


def post_message_for_identifier(some_identifier):
    msg = generate_demographics_query_message(some_identifier)
    try:
        response = send_message(msg)
    except Exception as err:
        logger.error(err)
        raise exceptions.APIError("Unable to reach the external system")

    unparsed_message = hl7.parse(response)
    errored = DemographicsErrorResponse(unparsed_message)

    if errored.msa.error_code:
        raise exceptions.APIError(
            "We can't find any patients with that identifier"
        )

    hl7_message = DemographicsQueryResponse(unparsed_message)
    message = construct_internal_message(hl7_message)
    save_message(message, hl7_message.pid.hospital_number)
    return construct_message_container(
        [message], hl7_message.pid.hospital_number
    )


@models.atomic_method
def save_message(demographics_message, hospital_number, session):
    gloss_ref = models.get_or_create_identifier(
        hospital_number, session, "uclh"
    )
    kwargs = copy(vars(demographics_message))
    kwargs["gloss_reference"] = gloss_ref
    patient = models.Patient(**kwargs)
    session.add(patient)



def construct_internal_message(hl7Message):
    interesting_fields = [
        "surname",
        "first_name",
        "middle_name",
        "title",
        "date_of_birth",
        "sex",
        "marital_status",
        "religion",
        "ethnicity",
        "post_code",
        "date_of_death",
        "death_indicator",
    ]

    kwargs = {
        i: getattr(hl7Message.pid, i) for i in interesting_fields if getattr(
            hl7Message.pid, i
        )
    }

    kwargs["gp_practice_code"] = hl7Message.pd1.gp_practice_code

    if hl7Message.pid.death_indicator is False:
        kwargs["date_of_death"] = None
    return PatientMessage(**kwargs)
