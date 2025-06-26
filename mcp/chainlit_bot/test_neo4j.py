
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv()

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USERNAME') 
password = os.getenv('NEO4J_PASSWORD')

print(f'Testing connection to: {uri}')
try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run('RETURN 1 as test')
        print('✅ Connection successful!')
        print(f'Result: {result.single()[0]}')
    driver.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
