from gloss import models, exceptions, utils
from gloss.conf import settings
from gloss.external_api import post_message_for_identifier

"""
    the information source is a data api, that by default gets
    from the database if possible, otherwise it queries an external
    service
"""

# TODO, we can just inherit this now...
if getattr(settings, "MOCK_EXTERNAL_API", None):
    post_message_for_identifier = utils.import_from_string(
        settings.MOCK_EXTERNAL_API
    )


def get_information_source():
    if hasattr(settings, "INFORMATION_SOURCE"):
        info_cls = utils.import_from_string(settings.INFORMATION_SOURCE)
        return info_cls()
    else:
        return InformationSource()


class InformationSource(object):
    def patient_exists(self, session, issuing_source, identifier):
        patient_exists = models.Patient.query_from_identifier(
            identifier, issuing_source, session
        ).count()


    def patient_information(self, issuing_source, identifier):
        with models.session_scope() as session:
            patient_exists = models.Patient.query_from_identifier(
                identifier, issuing_source, session
            ).count()

            if patient_exists:
                return models.patient_to_message_container(
                    identifier, issuing_source, session
                )
            if not patient_exists and settings.USE_EXTERNAL_LOOKUP:
                post_message_for_identifier(identifier)
                return models.patient_to_message_container(
                    identifier, issuing_source, session
                )
            else:
                raise exceptions.PatientNotFound(
                    "We can't find any patients with that identifier {}".format(
                        identifier
                    )
                )

    def demographics_query(self, issuing_source, identifier):
        get_demographics(session, issuing_source, identifier)

        try:
            messages = Merge.to_messages(
                identifier, issuing_source, session
            )
        except Exception as e:
            raise exceptions.APIError(e)

        messages.extend(Patient.to_messages(identifier, issuing_source, session))
