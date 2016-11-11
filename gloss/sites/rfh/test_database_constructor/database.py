import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DATABASE_USER = "ohc"
DATABASE_NAME = "central_rfh"


def get_connection(
    database_name=DATABASE_NAME,
    database_user=DATABASE_USER
):
    return psycopg2.connect("dbname={0} user={1}".format(
        database_name, database_user
    ))


def create_database():
    with get_connection("postgres") as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("CREATE DATABASE {}".format(DATABASE_NAME))
        cur.execute(
            "GRANT ALL PRIVILEGES ON DATABASE {0} TO {1}".format(
                DATABASE_NAME, DATABASE_USER
            )
        )
