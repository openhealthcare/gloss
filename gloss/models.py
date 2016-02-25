import datetime
from contextlib import contextmanager

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Boolean, ForeignKey
)
from sqlalchemy.orm import sessionmaker
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
    def get_from_gloss_id(cls, gloss_id, session):
        result = session.query(cls, GlossolaliaReference).\
        filter(PatientIdentifier.gloss_reference_id == GlossolaliaReference.id).\
        all()
        return [i[0] for i in result]


class Patient(Base, GlossSubrecord):
    id = Column(Integer, primary_key=True)
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
    datetime_of_admission = Column(DateTime)
    datetime_of_discharge = Column(DateTime)
    ward_code = Column(String(250))
    room_code = Column(String(250))
    bed_code = Column(String(250))
    visit_number = Column(String(250))


class PatientIdentifier(Base, GlossSubrecord):
    id = Column(Integer, primary_key=True)
    identifier = Column(String(250))
    issuing_source = Column(String(250))
    active = Column(Boolean, default=True)


class Subscription(Base, GlossSubrecord):
    id = Column(Integer, primary_key=True)
    system = Column(String(250))
    active = Column(Boolean, default=True)


class GlossolaliaReference(Base):
    id = Column(Integer, primary_key=True)

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


def __is_connected(hospital_number, session, issuing_source):
    return session.query(GlossolaliaReference, Subscription, PatientIdentifier).\
    filter(Subscription.gloss_reference_id == GlossolaliaReference.id).\
    filter(PatientIdentifier.gloss_reference_id == GlossolaliaReference.id).\
    filter(PatientIdentifier.issuing_source == issuing_source).\
    filter(PatientIdentifier.identifier == hospital_number)


# we need to get subscription from hospital number
def is_subscribed(hospital_number, session=None, issuing_source="uclh"):
    is_connected = __is_connected(hospital_number, session, issuing_source)
    return is_connected.filter(Subscription.active == True).count()

def get_gloss_id(hospital_number, session, issuing_source="uclh"):
    gloss_information = session.query(GlossolaliaReference, PatientIdentifier).\
    filter(PatientIdentifier.gloss_reference_id == GlossolaliaReference.id).\
    filter(PatientIdentifier.issuing_source == issuing_source).\
    filter(PatientIdentifier.identifier == hospital_number).one_or_none()

    # we should change this to only query for gloss id rather than all 3 columns
    if gloss_information:
        return gloss_information[0].id

def save_identifier(hospital_number, session, issuing_source="uclh"):
    glossolalia_reference = GlossolaliaReference()
    session.add(glossolalia_reference)
    hospital_identifier = PatientIdentifier(
        identifier=hospital_number,
        issuing_source="uclh",
        gloss_reference=glossolalia_reference
    )
    session.add(hospital_identifier)
