"""
The Public Gloss API
"""
import functools
import json
import sys
from flask import Flask, Response
from gloss.message_type import construct_message_container
from gloss.external_api import post_message_for_identifier
from gloss.serialisers.opal import OpalJSONSerialiser


sys.path.append('.')

from gloss import exceptions, models, settings

app = Flask('gloss.api')
app.debug = settings.DEBUG


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
        return app.route(route, **kwargs)(as_json)
    return wrapper


@json_api('/api/patient/<identifier>')
def patient_query(session, issuing_source, identifier):
    patient = models.Patient.query_from_identifier(identifier, issuing_source, session).first()
    if not patient:
        raise exceptions.APIError("We can't find any patients with that identifier")
    return {
        'demographics': [
            models.Patient.get_from_gloss_reference(patient.gloss_reference, session).to_dict()
        ],
        'results': [
            r.to_dict() for r in
            models.Result.list_from_gloss_reference(
                patient.gloss_reference, session
            )
        ]
    }


@json_api('/api/demographics/', methods=['POST'])
def demographics_create(session, issuing_source):
    raise exceptions.APIError("We've not implemented this yet - sorry")


@json_api('/api/demographics/<identifier>')
def demographics_query(session, issuing_source, identifier):
    patient = models.Patient.query_from_identifier(
        identifier, issuing_source, session
    ).one_or_none()

    if not patient:
        container = post_message_for_identifier(identifier)
    else:
        container = construct_message_container(
            [patient.to_message_type(session)], identifier
        )

    return container.to_dict()


@json_api('/api/subscribe/<identifier>')
def subscribe(session, issuing_source, identifier, end_point):
    models.subscribe(identifier, end_point, session, issuing_source)
    return {}


@json_api('/api/unsubscribe/<identifier>')
def unsubscribe(session, issuing_source, identifier):
    models.unsubscribe(identifier, session, issuing_source)
    return {}
