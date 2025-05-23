import os
import pyodbc, struct
from azure import identity
from os import environ
from typing import Union
from pydantic import BaseModel
from IPython import embed
import struct
import adal
import logging
from dotenv import load_dotenv
from dotenv import dotenv_values
status = load_dotenv(".env")
config = dotenv_values(".env")
logging.info(f"Load Environment {status}")

clientSecret = environ.get('clientSecret')
clientID = environ.get('clientID')
tenantID =  environ.get('tenantID')
authorityHostUrl = "https://login.microsoftonline.com"
authority_url = authorityHostUrl + '/' + tenantID
resource = "https://database.windows.net/"
context = adal.AuthenticationContext(authority_url, api_version=None)
   
driver = "Driver={ODBC Driver 17 for SQL Server}"
server = ";SERVER={0}".format(environ.get('server'))
database = ";DATABASE={0}".format(environ.get('database'))

token = context.acquire_token_with_client_credentials(
    resource,
    clientID,
    clientSecret)


tokenb = bytes(token["accessToken"], "UTF-8")
exptoken = b''

for i in tokenb:
    exptoken += bytes({i})
    exptoken += bytes(1)

tokenstruct = struct.pack("=i", len(exptoken)) + exptoken

connString = driver + server + database

SQL_COPT_SS_ACCESS_TOKEN = 1256
conn = pyodbc.connect(connString, attrs_before={SQL_COPT_SS_ACCESS_TOKEN:tokenstruct})

cursor = conn.cursor()

cursor.execute("SELECT * FROM Registration_demographicdata_csm")
embed()