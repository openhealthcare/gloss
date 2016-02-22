from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..models import (
    GlossolaliaReference, Subscription, PatientIdentifier,
    is_subscribed, Base
)

engine = create_engine('sqlite:///:memory:')

Base.metadata.create_all(engine)


def test_is_subscribed():
    Session = sessionmaker(bind=engine)
    session = Session()

    glossolalia_reference = GlossolaliaReference()
    session.add(glossolalia_reference)

    subscription = Subscription(
        system="elcid", gloss_reference=glossolalia_reference
    )
    session.add(subscription)

    hospital_identifier = PatientIdentifier(
        identifier="12341234",
        issuing_source="uclh",
        gloss_reference=glossolalia_reference
    )
    session.add(hospital_identifier)
    subscribed = is_subscribed("12341234", session=session)
    session.close()

    assert(subscribed)


def test_is_not_subscribed():
    Session = sessionmaker(bind=engine)
    session = Session()

    glossolalia_reference = GlossolaliaReference()
    session.add(glossolalia_reference)

    subscription = Subscription(
        system="elcid", gloss_reference=glossolalia_reference, active=False
    )
    session.add(subscription)

    hospital_identifier = PatientIdentifier(
        identifier="12341234",
        issuing_source="uclh",
        gloss_reference=glossolalia_reference
    )
    session.add(hospital_identifier)
    subscribed = is_subscribed("12341234", session=session)
    session.close()

    assert(not subscribed)
