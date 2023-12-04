from getpass import getpass
from dbcon import get_db_connector, insert
from  werkzeug.security import generate_password_hash
import uuid

username = getpass("Enter Username ")
password = getpass("Enter Password ")
public_id_str = str(uuid.uuid4())

password = generate_password_hash(password)

table, engine = get_db_connector('admin_login')

query = insert(table).values(user_name=username, password_hash=password, public_id=public_id_str)

engine.execute(query)