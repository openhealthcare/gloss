"""
Models for our Gloss Application
"""
from contextlib import contextmanager
import datetime
import json

from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Text
)
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import create_engine
from gloss import settings
from message_type import PatientMessage
engine = create_engine(settings.DATABASE_STRING)


def get_plural_name(cls):
    return "{}s".format(cls.__tablename__)


@as_declarative()
class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    id = Column(Integer, primary_key=True)
    updated = Column(DateTime, onupdate=datetime.datetime.utcnow)
    created = Column(DateTime, default=datetime.datetime.utcnow)


class GlossSubrecord(object):
    @declared_attr
    def gloss_reference_id(cls):
        return Column(Integer, ForeignKey('glossolaliareference.id'))

    @declared_attr
    def gloss_reference(cls):
        return relationship(
            "GlossolaliaReference",
            foreign_keys=[getattr(cls, "gloss_reference_id")]
        )

    @classmethod
    def query_by_gloss_id(cls, gloss_id, session):
        return session.query(cls).filter(cls.gloss_reference == gloss_id)

    @classmethod
    def get_from_gloss_reference(cls, gloss_reference, session):
        return cls.query_by_gloss_id(gloss_reference, session).one_or_none()

    @classmethod
    def list_from_gloss_reference(cls, gloss_reference, session):
        return cls.query_by_gloss_id(gloss_reference, session).all()

    @classmethod
    def query_from_identifier(cls, identifier, issuing_source, session):
        return session.query(cls).\
        filter(cls.gloss_reference_id == GlossolaliaReference.id).\
        filter(PatientIdentifier.gloss_reference_id == GlossolaliaReference.id).\
        filter(PatientIdentifier.issuing_source == issuing_source).\
        filter(PatientIdentifier.identifier == identifier)

    def to_dict(self):
        pass


class Error(Base):
    error = Column(Text)
    message = Column(Text)


class Patient(Base, GlossSubrecord):
    surname = Column(String(250), nullable=False)
    first_name = Column(String(250), nullable=False)
    middle_name = Column(String(250))
    title = Column(String(250))
    date_of_birth = Column(Date, nullable=False)
    birth_place = Column(String(250))
    sex = Column(String(250))
    marital_status = Column(String(250))
    religion = Column(String(250))
    date_of_death = Column(Date)
    post_code = Column(String(20))
    gp_practice_code = Column(String(20))
    ethnicity = Column(String(250))

    # I know it seems like we can calculate this from the above
    # however it comes as a seperate field in the feed and
    # therefore might be useful for data validation purposes
    # (also might give us an indicator and the max time of death)
    death_indicator = Column(Boolean, default=False)

    def to_message_type(self):
        excluding = {"id", "updated", "created"}
        kwargs = {k: v for k, v in vars(self).iteritems() if k  not in excluding}
        return PatientMessage(**kwargs)


class InpatientAdmission(Base, GlossSubrecord):
    datetime_of_admission = Column(DateTime, nullable=False)
    datetime_of_discharge = Column(DateTime)
    external_identifier = Column(String(250), nullable=False)
    admission_diagnosis = Column(String(250))


class InpatientLocation(Base):
    inpatient_admission_id = Column(Integer, ForeignKey('inpatientadmission.id'))
    inpatient_admission = relationship(
        "InpatientAdmission", foreign_keys=[inpatient_admission_id], cascade="all"
    )

    # when the patient was transferred from this location
    # null when the patient is at that location
    datetime_of_transfer = Column(DateTime)

    # when the patient was transferred from this location
    # None if the patient is currently there
    ward_code = Column(String(250))
    room_code = Column(String(250))
    bed_code = Column(String(250))

    @classmethod
    def get_location(cls, inpatient_admission, session):
        """
            get's the location of a patient
        """
        q = session.query(cls).filter(cls.datetime_of_transfer == None)
        q = q.filter(cls.inpatient_admission == inpatient_admission)
        return q.one_or_none()


class PatientIdentifier(Base, GlossSubrecord):
    identifier = Column(String(250))
    issuing_source = Column(String(250))
    active = Column(Boolean, default=True)

    @declared_attr
    def gloss_reference_id(cls):
        return Column(Integer, ForeignKey('glossolaliareference.id'))

    @declared_attr
    def gloss_reference(cls):
        return relationship(
            "GlossolaliaReference",
            foreign_keys=[getattr(cls, "gloss_reference_id")]
        )


class Merge(Base, GlossSubrecord):
    old_reference_id = Column(Integer, ForeignKey('glossolaliareference.id'))
    old_reference = relationship(
        "GlossolaliaReference", foreign_keys=[old_reference_id]
    )


class Subscription(Base, GlossSubrecord):
    system = Column(String(250))
    active = Column(Boolean, default=True)
    end_point = Column(String(250))


class Allergy(Base, GlossSubrecord):
    # ask the docs which fields they'd want
    # for the moment, lets just save allergy reference name
    allergy_type = Column(String(250))
    allergy_type_description = Column(String(250))
    certainty_id = Column(String(250))
    certainty_description = Column(String(250))
    allergy_reference_name = Column(String(250))
    allergy_description = Column(String(250))
    allergen_reference_system = Column(String(250))
    allergen_reference = Column(String(250))
    status_id = Column(String(250))
    status_description = Column(String(250))
    diagnosis_datetime = Column(DateTime)
    allergy_start_datetime = Column(DateTime)
    no_allergies = Column(Boolean, default=False)


class Result(Base, GlossSubrecord):
    lab_number = Column(String(250))
    profile_code = Column(String(250))
    profile_description = Column(String(250))
    request_datetime = Column(DateTime)
    observation_datetime = Column(DateTime)
    last_edited = Column(DateTime)
    result_status = Column(String(250))
    observations = Column(Text)


class OutgoingMessage(Base):
    pass


class GlossolaliaReference(Base):
    pass


Session = sessionmaker(bind=engine)


def get_session():
    # used by mock in unit tests
    return Session()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def atomic_method(some_fun):
    def wrap_method(*args, **kwargs):
        with session_scope() as session:
            if "session" not in kwargs:
                kwargs["session"] = session
            return some_fun(*args, **kwargs)

    return wrap_method


@atomic_method
def get_outgoing_message(session):
    outgoing_message = OutgoingMessage()
    session.add(outgoing_message)
    return outgoing_message


# we need to get subscription from hospital number
def is_subscribed(hospital_number, session=None, issuing_source="uclh"):
    subscription = Subscription.query_from_identifier(
        hospital_number, issuing_source, session
    )
    return subscription.filter(Subscription.active == True).count()


def get_subscription_endpoint(hospital_number, session=None, issuing_source="uclh"):
    subscription = Subscription.query_from_identifier(
        hospital_number, issuing_source, session
    )
    subscription = subscription.filter(Subscription.active == True)

    if subscription.count():
        return subscription.first().end_point


def is_known(hospital_number, session=None, issuing_source="uclh"):
    return Subscription.query_from_identifier(
        hospital_number, issuing_source, session
    ).count()


def subscribe(hospital_number, end_point, session, issuing_source):
    """ subscribe an issuing source and hosptial number to an end point
        don't allow multiple subscriptions
    """
    subscription = Subscription.query_from_identifier(
        hospital_number, issuing_source, session
    ).one_or_none()

    if subscription:
        if not subscription.active:
            subscription.active = True
            session.add(subscription)
    else:
        gloss_reference = get_or_create_identifier(
            hospital_number, session, issuing_source
        )
        session.add(gloss_reference)
        subscription = Subscription(
            gloss_reference=gloss_reference,
            system=issuing_source,
            end_point=end_point
        )
        session.add(subscription)


def unsubscribe(hospital_number, session, issuing_source):
    subscription = Subscription.query_from_identifier(
        hospital_number, issuing_source, session
    ).one_or_none()

    if subscription:
        subscription.active = False
        session.add(subscription)


def get_gloss_reference(hospital_number, session, issuing_source="uclh"):
    gloss_information = session.query(GlossolaliaReference, PatientIdentifier).\
    filter(PatientIdentifier.gloss_reference_id == GlossolaliaReference.id).\
    filter(PatientIdentifier.issuing_source == issuing_source).\
    filter(PatientIdentifier.identifier == hospital_number).one_or_none()

    # we should change this to only query for gloss id rather than all 3 columns
    if gloss_information:
        return gloss_information[0]

def save_identifier(hospital_number, session, issuing_source="uclh"):
    glossolalia_reference = GlossolaliaReference()
    session.add(glossolalia_reference)
    hospital_identifier = PatientIdentifier(
        identifier=hospital_number,
        issuing_source="uclh",
        gloss_reference=glossolalia_reference
    )
    session.add(hospital_identifier)
    return glossolalia_reference


def get_or_create_identifier(hospital_number, session, issuing_source="uclh"):
    gloss_reference = get_gloss_reference(hospital_number, session, issuing_source="uclh")

    if gloss_reference:
        return gloss_reference
    else:
        return save_identifier(hospital_number, session, issuing_source="uclh")


def create_or_update_inpatient_admission(message, gloss_ref, base=None):
    if base:
        inpatient_admission = base
    else:
        inpatient_admission = InpatientAdmission()

    inpatient_admission.gloss_reference = gloss_ref
    inpatient_admission.datetime_of_admission = message.datetime_of_admission
    inpatient_admission.datetime_of_discharge = message.datetime_of_discharge
    inpatient_admission.external_identifier = message.external_identifier
    inpatient_admission.admission_diagnosis = message.admission_diagnosis
    return inpatient_admission


def create_or_update_inpatient_location(message, inpatient_admission, base=None):
    if base:
        inpatient_location = base
    else:
        inpatient_location = InpatientLocation()

    inpatient_location.ward_code = message.ward_code
    inpatient_location.room_code = message.room_code
    inpatient_location.bed_code = message.bed_code
    inpatient_location.inpatient_admission = inpatient_admission
    return inpatient_location


def get_or_create_admission(message, gloss_ref, session):
    created = False
    inpatient_admission = session.query(InpatientAdmission).filter(
        InpatientAdmission.external_identifier == message.external_identifier
    ).one_or_none()

    if not inpatient_admission:
        created = True
        inpatient_admission = create_or_update_inpatient_admission(
            message, gloss_ref
        )

    return inpatient_admission, created,


def get_or_create_location(message, inpatient_admission, session):
    created = False
    inpatient_location = InpatientLocation.get_location(
        inpatient_admission, session
    )

    if not inpatient_location:
        created = True
        inpatient_location = create_or_update_inpatient_location(
            message, inpatient_admission
        )

    return inpatient_location, created,
