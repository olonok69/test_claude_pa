import os
import pyodbc, struct
from azure import identity

from typing import Union
from pydantic import BaseModel
from IPython import embed

import logging
from dotenv import load_dotenv
from dotenv import dotenv_values
status = load_dotenv(".env")
config = dotenv_values(".env")
logging.info(f"Load Environment {status}")
    
connection_string = os.environ["AZURE_SQL_CONNECTIONSTRING"]
def get_conn():
    credential = identity.DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
    conn = pyodbc.connect(config.get("AZURE_SQL_CONNECTIONSTRING"), attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    return conn


conn = get_conn()
cursor = conn.cursor()
# Registration_demographicdata_csm

cursor.execute("SELECT * FROM Registration_demographicdata_csm")
embed()