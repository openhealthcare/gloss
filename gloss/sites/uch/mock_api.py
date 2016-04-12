import random
from gloss.models import Patient
from gloss import coded_values
from datetime import datetime, date, timedelta

first_names = [
    "Jane", "James", "Chandeep", "Samantha", "Oliver", "Charlie",
    "Sophie", "Emily", "Lily", "Olivia", "Amelia", "Isabella"
]

last_names = [
    "Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Wilson",
    "Brooke", "King", "Patel", "Jameson", "Davidson", "Williams"
]

adjectives = [
    "orange", "red", "blue", "green", "pink", "purple", "gold", "silver",
    "bronze", "ruby", "azure", "copper", "forest", "silent", "loud", "dry",
    "angry"
]

nouns = [
    "cat", "dog", "eagle", "penguin", "lion", "tiger", "cheetah", "antelope",
    "chimpanzee", "gorilla", "spider", "frog", "toad", "bat", "owl", "elvis"
]

NULL_PROBABILITY = 2 # out of 10


def date_generator(*args, **kwargs):
    start_date = kwargs.get("start_date")
    end_date = kwargs.get("end_date")
    if not end_date:
        end_date = date.today()
    if not start_date:
        today = date.today()
        back = 90
        # Very occassionally we run code on Leap Day.
        if today.month == 2 and today.day == 29:
            back = 88
        start_date = date(today.year - back, today.month, today.day)

    year_diff = end_date.year - start_date.year
    year = end_date.year - random.randint(1, year_diff)

    if year == start_date.year:
        first_month = start_date.month
    else:
        first_month = 1

    if year == end_date.year:
        last_month = end_date.month
    else:
        last_month = 12
    month = random.randint(first_month, last_month)

    if month == end_date.month and year == end_date.year:
        last_day = end_date.day
    else:
        last_day = 28

    if month == start_date.month and year == start_date.year:
        first_day = start_date.day
    else:
        first_day = 1
    day = random.randint(first_day, last_day)
    return date(year, month, day)


def date_time_generator(*args, **kwargs):
    d = date_generator(*args, **kwargs)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return timezone.make_aware(datetime(d.year, d.month, d.day, hours, minutes))


def get_birth_date():
    eighteen_years_ago = date.today() - timedelta(days=18*365)
    return date_generator(start_date=date(1920, 1, 1), end_date=eighteen_years_ago)


def get_first_name():
    return random.choice(first_names)


def get_last_name():
    return random.choice(last_names)


def get_sex():
    return random.choice(coded_values.SEX_MAPPING.values())


def get_religion():
    return random.choice(coded_values.RELIGION_MAPPINGS.values())


def get_ethnicity():
    return random.choice(coded_values.ETHNICITY_MAPPING.values())


def get_marital_status():
    return random.choice(coded_values.MARITAL_STATUSES_MAPPING.values())


def get_title():
    possible = ("Mr", "Mrs", "Ms", "Dr", "Rev")
    return random.choice(possible)


def nullable(some_func):
    if random.randint(0, 10) < NULL_PROBABILITY:
        return None
    else:
        return some_func()


def get_fake_patient():
    get_post_code = lambda: "SW12 0BJ"
    get_gp_practice_code = lambda: "GPZ XY10"
    return dict(
        surname=get_last_name(),
        first_name=get_first_name(),
        middle_name=nullable(get_first_name),
        title=nullable(get_title),
        date_of_birth=get_birth_date(),
        sex=nullable(get_sex),
        marital_status=nullable(get_marital_status),
        religion=nullable(get_religion),
        date_of_death=None,
        post_code=nullable(get_post_code),
        gp_practice_code=nullable(get_gp_practice_code),
        ethnicity=nullable(get_ethnicity)
    )


def get_mock_data(cls, some_identifier, some_issuing_source, session):
    if cls == Patient:
        if some_identifier.startswith("xxx"):
            return []
        else:
            return [cls.message_type(**get_fake_patient())]
    else:
        return cls._to_messages(some_identifier, some_issuing_source, session)
