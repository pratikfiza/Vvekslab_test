from sqlalchemy import create_engine, MetaData, Table, insert, select
from sqlalchemy.engine import URL


db_engine_url = URL.create(
    'mysql+mysqlconnector',
    username='root',
    password='pratik12345',
    host='localhost',
    port='3306',
    database='webpage_data')


def get_db_connector(table_name):
    engine = create_engine(db_engine_url)
    metadata = MetaData()
    table = Table(table_name, metadata, autoload = True, autoload_with=engine)
    return table, engine