"""
The Public Gloss API
"""
import functools
import json
import sys
import logging
from flask import Flask, Response, request, render_template
from gloss.message_type import construct_message_container
from gloss.models import Patient
from gloss.external_api import post_message_for_identifier
from gloss.serialisers.opal import OpalJSONSerialiser
from gloss.settings import HOST, PORTS
from hl7.client import MLLPClient


sys.path.append('.')

from gloss import exceptions, models, settings


app = Flask('gloss.api')
app.debug = settings.DEBUG
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
app.logger.addHandler(stream_handler)


def json_api(route, **kwargs):
    def wrapper(fn):
        @functools.wraps(fn)
        def as_json(*args, **kwargs):
            try:
                with models.session_scope() as session:
                    # TODO this should not be hardcoded
                    issuing_source = "uclh"
                    data = fn(session, issuing_source, *args, **kwargs)
                    data["status"] = "success"
                    return Response(json.dumps(data, cls=OpalJSONSerialiser))

            except exceptions.APIError as err:
                data = {'status': 'error', 'data': err.msg}
                return Response(json.dumps(
                    data,
                    cls=OpalJSONSerialiser
                ))
        # Flask is full of validation for things like function names so let's fake it
        as_json.__name__ = fn.__name__
        kwargs["methods"]=["GET", "POST"]
        return app.route(route, **kwargs)(as_json)
    return wrapper


@json_api('/api/patient/<identifier>')
def patient_query(session, issuing_source, identifier):
    patient_exists = models.Patient.query_from_identifier(
        identifier, issuing_source, session
    ).count()
    if not patient_exists and settings.USE_EXTERNAL_LOOKUP:
        post_message_for_identifier(identifier)

    result = models.patient_to_message_container(
        identifier, issuing_source, session
    )

    if not result.messages:
        raise exceptions.APIError(
            "We can't find any patients with that identifier"
        )

    return result.to_dict()


@json_api('/api/demographics/', methods=['POST'])
def demographics_create(session, issuing_source):
    raise exceptions.APIError("We've not implemented this yet - sorry")


@json_api('/api/demographics/<identifier>')
def demographics_query(session, issuing_source, identifier):
    container = construct_message_container(
        Patient.to_messages(identifier, issuing_source, session),
        identifier
    )

    if not container.messages and settings.USE_EXTERNAL_LOOKUP:
        container = post_message_for_identifier(identifier)

    if not settings.USE_EXTERNAL_LOOKUP or not container.messages:
        raise exceptions.APIError(
            "We can't find any patients with that identifier"
        )

    return container.to_dict()


@json_api('/api/subscribe/<identifier>')
def subscribe(session, issuing_source, identifier):
    end_point = request.form["end_point"]
    models.subscribe(identifier, end_point, session, issuing_source)
    return {}


@json_api('/api/unsubscribe/<identifier>')
def unsubscribe(session, issuing_source, identifier):
    models.unsubscribe(identifier, session, issuing_source)
    return {}


if settings.SEND_MESSAGES_CONSOLE:
    @app.route("/hl7pretendomatic")
    def hl7pretendomatic():
        from gloss.tests.test_messages import MESSAGE_TYPES
        messages = {k.replace("_", " "): v for k, v in MESSAGE_TYPES.iteritems()}
        return render_template("send_hl7.html", message=json.dumps(messages))


    @json_api('/api/mllp_send/data')
    def send_mllp_to_self(session, issuing_source):
        port = PORTS[0]
        message = request.form["message"]
        messages = message.split("|", 2)
        message = "\rMSH|^~\\&|{}\r".format(messages[-1]).replace("\n", "\r")
        with MLLPClient(HOST, port) as client:
            client.send_message(message)
        return {}
