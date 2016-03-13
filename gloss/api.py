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

def json_api(fn):
    @functools.wraps(fn)
    def as_json(*args, **kwargs):
        try:
            with models.session_scope() as session:
                data = fn(session, *args, **kwargs)
                return Response(json.dumps({'status': 'success', 'data': data}))
        except exceptions.APIError as err:
            return Response(json.dumps({'status': 'error', 'data': err.msg}))
    return as_json

@app.route('/api/patient/<identifier>')
@json_api
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

@app.route('/api/demographics/', methods=['POST'])
@json_api
def demographics_create(session):
    raise exceptions.APIError("We've not implemented this yet - sorry.")

@app.route('/api/demographics/<identifier>')
@json_api
def demographics_query(session, identifier):
    patient = models.Patient.query_from_identifier(identifier, 'uclh', session).first()
    if not patient:
        raise exceptions.APIError("We can't find any patients with that identifier")
    return {'demographics': [ patient.to_dict() ] }

@app.route('/api/subscribe/<identifier>')
@json_api
def subscribe(session, identifier):
    raise exceptions.APIError("We've not implemented this yet - sorry")

@app.route('/api/unsubscribe/<identifier>')
@json_api
def unsubscribe(session, identifier):
    raise exceptions.APIError("We've not implemented this yet - sorry")

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 6767
    port = int(os.environ.get('PORT', 6767))
    app.run(host='0.0.0.0', port=port)
