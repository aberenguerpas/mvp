import os
import json
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection

# Load environment vars from .env
load_dotenv('./../.env')

# Load env vars
OPENSEARCH_URL = os.environ.get("OPENSEARCH_URL")
OPENSEARCH__PORT = os.environ.get("OPENSEARCH_PORT")
OPENSEARCH_USER = os.environ.get("OPENSEARCH_USER")
OPENSEARCH_PASS = os.environ.get("OPENSEARCH_PASS")
INDEX_DATA = os.environ.get("INDEX_DATA")
INDEX_LOGS = os.environ.get("INDEX_LOGS")
INDEX_UPDATES = os.environ.get("INDEX_UPDATES")

# Connect to database
print("-"*40)
print("Connecting to opensearch database...", end="")
try:
    client = OpenSearch(
            hosts=[{'host': OPENSEARCH_URL, 'port': OPENSEARCH__PORT}],
            http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
    )
    if client.ping():
        print("ok")
    else:
       raise Exception("\nProblem connecting to the database")
except Exception as e:
    print(e)
    exit()

print("-"*40)


if not client.indices.exists(INDEX_DATA):
    f = open('schemas/schema_data.json')
    body = json.load(f)
    response = client.indices.create(INDEX_DATA, body=body)
    print(f'Index {INDEX_DATA} created')
    f.close()
else:
    print(f'Index {INDEX_DATA} already exist!')
    
if not client.indices.exists(INDEX_UPDATES):
    f = open('schemas/schema_updates.json')
    body = json.load(f)
    response = client.indices.create(INDEX_UPDATES, body=body)
    print(f'Index {INDEX_UPDATES} created')
    f.close()
else:
    print(f'Index {INDEX_UPDATES} already exist!')
    
#if not client.indices.exists(INDEX_LOGS):
#    f = open('schemas/schema_logs.json')
#    body = json.load(f)
#    response = client.indices.create(INDEX_LOGS, body=body)
#    print(f'Index {INDEX_LOGS} created')
#    f.close()
#else:
#    print(f'Index {INDEX_LOGS} already exist!')


print("-"*40)