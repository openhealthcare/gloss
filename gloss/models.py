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
from gloss.settings import DATABASE_STRING, COMMIT
engine = create_engine(DATABASE_STRING)


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


class Serialisable(object):
    def get_fieldnames_to_serialize(self):
        attributes = vars(self.__class__)
        field_names = []
        for name, class_type in attributes.iteritems():
            if class_type == InstrumentedAttribute:
                field_names.append(name)

        return field_names

    def to_dict(self):
        field_names = self.get_fieldnames_to_serialize()

        return {
            field_name: getattr(self, field_name) for field_name in field_names
        }


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
        return cls.query_by_gloss_reference(gloss_reference, session).all()

    @classmethod
    def query_from_identifier(cls, identifier, issuing_source, session):
        return session.query(cls).\
        filter(cls.gloss_reference_id == GlossolaliaReference.id).\
        filter(PatientIdentifier.gloss_reference_id == GlossolaliaReference.id).\
        filter(PatientIdentifier.issuing_source == issuing_source).\
        filter(PatientIdentifier.identifier == identifier)

    def to_dict(self):
        pass


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

    # I know it seems like we can calculate this from the above
    # however it comes as a seperate field in the feed and
    # therefore might be useful for data validation purposes
    # (also might give us an indicator and the max time of death)
    death_indicator = Column(Boolean, default=False)
    birth_place = Column(String)


class InpatientEpisode(Base, GlossSubrecord):
    datetime_of_admission = Column(DateTime, nullable=False)
    datetime_of_discharge = Column(DateTime)
    visit_number = Column(String(250), nullable=False)


class InpatientLocation(Base):
    inpatient_episode_id = Column(Integer, ForeignKey('inpatientepisode.id'))
    inpatient_episode = relationship(
        "InpatientEpisode", foreign_keys=[inpatient_episode_id], cascade="all"
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
    def get_location(cls, inpatient_episode, session):
        """
            get's the location of a patient
        """
        q = session.query(cls).filter(cls.datetime_of_transfer == None)
        q = q.filter(cls.inpatient_episode == inpatient_episode)
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
    request_datetime = Column(DateTime)
    observation_datetime = Column(DateTime)
    last_edited = Column(DateTime)
    result_status = Column(String(250))
    observations = Column(Text)


class GlossolaliaReference(Base):
    pass


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def get_session():
    return Session()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
        if COMMIT:
            session.commit()
    except:
        session.rollback()
        raise
    finally:
        if COMMIT:
            session.close()

def atomic_method(some_fun):
    def wrap_method(*args, **kwargs):
        with session_scope() as session:
            if "session" not in kwargs:
                kwargs["session"] = session
            some_fun(*args, **kwargs)

    return wrap_method


# we need to get subscription from hospital number
def is_subscribed(hospital_number, session=None, issuing_source="uclh"):
    subscription = Subscription.query_from_identifier(
        hospital_number, issuing_source, session
    )
    return subscription.filter(Subscription.active == True).count()


def subscribe(hospital_number, session, issuing_source):
    gloss_reference = get_or_create_identifier(
        hospital_number, session, issuing_source
    )
    session.add(gloss_reference)
    subscription = Subscription(
        gloss_reference=gloss_reference,
        system=issuing_source,
    )
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



class WinPathMessage(object):
    """
    We don't expect this to be a long term strategy.
    It's a placeholder class to simply pass through
    winpath stuff to an OPAL instance.
    """
    def __init__(self, msg):
        self.msg = msg

    def to_OPAL(self):
        return dict(
                identifier=self.msg.pid.hospital_number,
                data=dict(
                    lab_number=self.msg.obr.lab_number,
                    profile_code=self.msg.obr.profile_code,
                    profile_description=self.msg.obr.profile_description,
                    request_datetime=self.msg.obr.request_datetime.strftime('%Y/%m/%d %H:%M'),
                    observation_datetime=self.msg.obr.observation_datetime.strftime('%Y/%m/%d %H:%M'),
                    last_edited=self.msg.obr.last_edited.strftime('%Y/%m/%d %H:%M'),
                    result_status=self.msg.obr.result_status,
                    observations=json.dumps([
                        dict(
                            value_type=obx.value_type,
                            test_code=obx.test_code,
                            test_name=obx.test_name,
                            observation_value=obx.observation_value,
                            units=obx.units,
                            reference_range=obx.reference_range,
                            result_status=obx.result_status
                        ) for obx in self.msg.obxs
                    ])
                )
            )
