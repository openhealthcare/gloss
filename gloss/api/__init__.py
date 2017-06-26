"""
The Public Gloss API
"""
import functools
import json
import sys
import logging
from time import time
from flask import Flask, Response, request, render_template
from hl7.client import MLLPClient
from gloss.serialisers.opal import OpalJSONSerialiser
from gloss.core.settings_utils import set_settings_env
sys.path.append('.')

#TODO change this to use parser
set_settings_env(sys.argv[-1])
from gloss.conf import settings
from gloss import exceptions, models
from gloss.information_source import get_information_source

app = Flask('gloss.api')
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
app.logger.addHandler(stream_handler)
app.debug = settings.DEBUG


def json_api(route, with_session=True, **kwargs):
    def wrapper(fn):
        @functools.wraps(fn)
        def as_json(*args, **kwargs):
            issuing_source = settings.ISSUING_SOURCE
            ts = time()
            try:
                if with_session:
                    with models.session_scope() as session:
                        data = fn(session, issuing_source, *args, **kwargs)
                else:
                    data = fn(issuing_source, *args, **kwargs)

                data["status"] = "success"
                app.logger.info("%s in %2.4fs" % (route, ts))
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


@json_api('/api/patient/<identifier>', with_session=False)
def patient_query(issuing_source, identifier):
    result = get_information_source().patient_information(
        issuing_source, identifier
    )
    return result.to_dict()


@json_api('/api/result/<identifier>', with_session=False)
def result_query(issuing_source, identifier):
    """ Returns all results for a patient
    """
    result = get_information_source().result_information(
        issuing_source, identifier
    )
    return result.to_dict()


@json_api('/api/demographics/', methods=['POST'])
def demographics_create(session, issuing_source):
    raise exceptions.APIError("We've not implemented this yet - sorry")


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
        from gloss.translators.hl7 import hl7_translator
        import hl7
        messages = {k.replace("_", " "): v.replace("\r", "\n") for k, v in MESSAGE_TYPES.iteritems()}
        fields = {}

        for k, v in MESSAGE_TYPES.iteritems():
            y = hl7.parse(v)
            converted_messages = hl7_translator.HL7Translator.translate(y)
            fields[k.replace("_", " ")] = converted_messages.pid.hospital_number

        return render_template(
            "send_hl7.html",
            message=json.dumps(messages),
            fields=json.dumps(fields)
        )

    @json_api('/api/mllp_send/data')
    def send_mllp_to_self(session, issuing_source):
        port = settings.PORTS[0]
        message = request.form["message"]
        messages = message.split("|", 2)
        message = "\rMSH|^~\\&|{}\r".format(messages[-1]).replace("\n", "\r")
        with MLLPClient(settings.HOST, port) as client:
            client.send_message(message)
        return {}
