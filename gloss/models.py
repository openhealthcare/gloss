import datetime
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Boolean, ForeignKey
)
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import relationship
from settings import engine


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
            back_populates=get_plural_name(cls)
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
        return session.query(cls, GlossolaliaReference, PatientIdentifier).\
        filter(cls.gloss_reference_id == GlossolaliaReference.id).\
        filter(PatientIdentifier.gloss_reference_id == GlossolaliaReference.id).\
        filter(PatientIdentifier.issuing_source == issuing_source).\
        filter(PatientIdentifier.identifier == identifier)


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
    death = Column(Boolean, default=False)
    birth_place = Column(String)


class InpatientEpisode(Base, GlossSubrecord):
    datetime_of_admission = Column(DateTime, nullable=False)
    datetime_of_discharge = Column(DateTime)
    ward_code = Column(String(250))
    room_code = Column(String(250))
    bed_code = Column(String(250))
    visit_number = Column(String(250), nullable=False)


class PatientIdentifier(Base, GlossSubrecord):
    identifier = Column(String(250))
    issuing_source = Column(String(250))
    active = Column(Boolean, default=True)


class Subscription(Base, GlossSubrecord):
    system = Column(String(250))
    active = Column(Boolean, default=True)


class GlossolaliaReference(Base):
    pass

for subrecord in GlossSubrecord.__subclasses__():
    r = relationship(subrecord.__name__, back_populates="gloss_reference")
    setattr(GlossolaliaReference, get_plural_name(subrecord), r)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


# we need to get subscription from hospital number
def is_subscribed(hospital_number, session=None, issuing_source="uclh"):
    subscription = Subscription.query_from_identifier(
        hospital_number, issuing_source, session
    )
    return subscription.filter(Subscription.active == True).count()

def subscribe(hospital_number, session, issuing_source):
    gloss_reference = GlossolaliaReference()
    session.add(gloss_reference)
    subscription = Subscription(
        gloss_reference=gloss_reference,
        system=issuing_source,
    )
    session.add(subscription)
    hospital_identifier = PatientIdentifier(
        identifier=hospital_number,
        issuing_source="uclh",
        gloss_reference=gloss_reference
    )
    session.add(hospital_identifier)


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
