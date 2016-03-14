"""
The Public Gloss API
"""
import functools
import json
import os
import sys

from flask import Flask, Response, request

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
                    data = fn(session, *args, **kwargs)
                    return Response(json.dumps({'status': 'success', 'data': data}))
            except exceptions.APIError as err:
                return Response(json.dumps({'status': 'error', 'data': err.msg}))
        # Flask is full of validation for things like function names so let's fake it
        as_json.__name__ = fn.__name__
        return app.route(route, **kwargs)(as_json)
    return wrapper

@json_api('/api/patient/<identifier>')
def patient_query(session, identifier):
    patient = models.Patient.query_from_identifier(identifier, 'uclh', session).first()
    if not patient:
        raise exceptions.APIError("We can't find any patients with that identifier")
    return {
        'demographics': [
            models.Patient.get_from_gloss_reference(patient.gloss_reference, session).to_dict()
        ],
        'results': [
            r.to_dict() for r in
            session.query(models.Result).filter(
                models.Result.gloss_reference_id==patient.gloss_reference_id).all()
        ]
    }

@json_api('/api/demographics/', methods=['POST'])
def demographics_create(session):
    raise exceptions.APIError("We've not implemented this yet - sorry")

@json_api('/api/demographics/<identifier>')
def demographics_query(session, identifier):
    patient = models.Patient.query_from_identifier(identifier, 'uclh', session).first()
    if not patient:
        raise exceptions.APIError("We can't find any patients with that identifier")
    return {'demographics': [ patient.to_dict() ] }

@json_api('/api/subscribe/<identifier>')
def subscribe(session, identifier):
    raise exceptions.APIError("We've not implemented this yet - sorry")

@json_api('/api/unsubscribe/<identifier>')
def unsubscribe(session, identifier):
    raise exceptions.APIError("We've not implemented this yet - sorry")
