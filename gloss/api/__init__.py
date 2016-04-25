"""
The Public Gloss API
"""
import functools
import json
import sys
import logging
from flask import Flask, Response, request, render_template
from gloss.message_type import construct_message_container
from gloss.models import Patient, Merge
from gloss.external_api import post_message_for_identifier
from gloss.serialisers.opal import OpalJSONSerialiser
from gloss.settings import HOST, PORTS
from hl7.client import MLLPClient
from gloss.utils import import_function


sys.path.append('.')

from gloss import exceptions, models, settings




app = Flask('gloss.api')
app.debug = settings.DEBUG
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
app.logger.addHandler(stream_handler)

if getattr(settings, "MOCK_EXTERNAL_API", None):
    post_message_for_identifier = import_function(settings.MOCK_EXTERNAL_API)


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
                    app.logger.critical(data)
                    return Response(json.dumps(data, cls=OpalJSONSerialiser))

            except exceptions.APIError as err:
                data = {'status': 'error', 'data': err.msg}
                app.logger.critical(data)
                return Response(json.dumps(
                    data,
                    cls=OpalJSONSerialiser
                ))
        # Flask is full of validation for things like function names so let's fake it
        as_json.__name__ = fn.__name__
        kwargs["methods"]=["GET", "POST"]
        return app.route(route, **kwargs)(as_json)
    return wrapper


def get_demographics(session, issuing_source, identifier):
    """ a utility that fetches demographics data remotely if its not
        present locally
    """
    patient_exists = models.Patient.query_from_identifier(
        identifier, issuing_source, session
    ).count()

    if patient_exists:
        return

    if not patient_exists and settings.USE_EXTERNAL_LOOKUP:
        post_message_for_identifier(identifier)
    else:
        raise exceptions.APIError(
            "We can't find any patients with that identifier {}".format(
                identifier
            )
        )


@json_api('/api/patient/<identifier>')
def patient_query(session, issuing_source, identifier):
    get_demographics(session, issuing_source, identifier)

    result = models.patient_to_message_container(
        identifier, issuing_source, session
    )

    return result.to_dict()


@json_api('/api/demographics/', methods=['POST'])
def demographics_create(session, issuing_source):
    raise exceptions.APIError("We've not implemented this yet - sorry")


@json_api('/api/demographics/<identifier>')
def demographics_query(session, issuing_source, identifier):
    get_demographics(session, issuing_source, identifier)

    try:
        messages = Merge.to_messages(
            identifier, issuing_source, session
        )
    except Exception as e:
        raise exceptions.APIError(e)

    messages.extend(Patient.to_messages(identifier, issuing_source, session))

    container = construct_message_container(
        messages, identifier
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
        from gloss.import_message import MessageProcessor
        import hl7
        messages = {k.replace("_", " "): v.replace("\r", "\n") for k, v in MESSAGE_TYPES.iteritems()}
        fields = {}

        for k, v in MESSAGE_TYPES.iteritems():
            y = hl7.parse(v)
            message_type = MessageProcessor().get_message_type(y)
            converted_messages = message_type(y)
            fields[k.replace("_", " ")] = converted_messages.pid.hospital_number

        return render_template(
            "send_hl7.html",
            message=json.dumps(messages),
            fields=json.dumps(fields)
        )

    @json_api('/api/mllp_send/data')
    def send_mllp_to_self(session, issuing_source):
        port = PORTS[0]
        message = request.form["message"]
        messages = message.split("|", 2)
        message = "\rMSH|^~\\&|{}\r".format(messages[-1]).replace("\n", "\r")
        with MLLPClient(HOST, port) as client:
            client.send_message(message)
        return {}
