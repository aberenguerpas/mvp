from dotenv import load_dotenv
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
from tqdm import tqdm
from setup_logger import logger
import os
import json
import traceback
import shutil

def extractText(data):
    res = []
    if data:
        for i in data:
            if i and i['language']:
                if i['language']=='es':
                    res.append(i['label'])
                    continue
                elif i['language']=='en':
                    res.append(i['label'])
                    continue
                else:
                    break
    return res
            
# Load environment vars from .env
r = load_dotenv('./../.env', override=True)


# Acces to environment vars
DATA_PATH = os.environ.get("DATA_PATH")
OPENSEARCH_URL = os.environ.get("OPENSEARCH_URL")
OPENSEARCH__PORT = os.environ.get("OPENSEARCH_PORT")
OPENSEARCH_USER = os.environ.get("OPENSEARCH_USER")
OPENSEARCH_PASS = os.environ.get("OPENSEARCH_PASS")
INDEX_DATA = os.environ.get("INDEX_DATA")
INDEX_UPDATES = os.environ.get("INDEX_UPDATES")

# Establish connections to OpenSearch Server
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
        logger.info(f"Connected to {OPENSEARCH_URL}")
        print("Ok")
    else:
       raise Exception("\nProblem connecting to the database")

except Exception as e:
    logger.error("Problem connection to the database")
    exit()

print("-"*40)

# Load data sources
data_sources = [name for name in os.listdir(DATA_PATH)]

for source in data_sources:
    datasets = []
    metadata_path = DATA_PATH+source+'/metadata/'
    
    print(f"Preparing {source} metadata")
    for resource in tqdm(os.listdir(metadata_path)):
        try:
            f = open(metadata_path + resource)
            resource_meta = json.load(f)
            doc = {
                "dct:identifier": resource_meta['dct:identifier'],
                "custom:identifier": resource_meta['custom:id'],
                "custom:url": resource_meta['custom:url'],
                "dct:title": extractText([resource_meta['dct:title']]),
                "dct:description": extractText([resource_meta['dct:description']]),
                "dcat:theme": extractText(resource_meta['dcat:theme']),
                "dcat:keyword": extractText(resource_meta['dcat:keyword']),
                "dcat:distribution": [],
                "dct:modified": resource_meta['dct:modified'][0:10] if resource_meta['dct:modified'] else None,
                "dct:issued": resource_meta['dct:issued'][0:10] if resource_meta['dct:issued'] else None,
                "dcat:publisher": {
                    "title": resource_meta.get('dct:publisher', {}).get('name') if resource_meta['dct:publisher'] else None,
                    "homepage": resource_meta.get('dct:publisher', {}).get('homepage') if resource_meta['dct:publisher'] else None
                },
                "dct:language": resource_meta['dct:language'],
                "dct:spatial": {
                    "country": resource_meta['custom:country'],
                    "city": None,
                    "bbox": None,
                    "centroid": None
                },
                "dct:temporal": [
                    {"startDate": None,
                    "endDate": None
                    }
                ],
                "custom:sample": None,
                "custom:indexation_date": datetime.today().strftime("%Y-%m-%d")
            }

            for r in resource_meta['dcat:distribution']:
                dist = {"dct:downloadUrl": r["dcat:downloadURL"],
                        "dct:format": r["dcat:mediaType"],
                        "dct:rights": r['dct:rights'],
                        "dct:title": extractText([r['dct:title']]),
                        "dcat:byteSize": r['dcat:byteSize']
                        }
                doc['dcat:distribution'].append(dist)

            datasets.append(doc)
        except Exception:
            print(resource_meta.get('dct:publisher'))
            traceback.print_exc() 
    
    actions = [{
        "_op_type": "update",
        "_index": INDEX_DATA,
        "_id": dataset['custom:identifier'],
        "doc": dataset,
        "doc_as_upsert": True}
        for dataset in datasets]

    # Perform the bulk index operation
    total_docs = 0
    try:
        print("Indexing...", end="")
        for success, info in helpers.parallel_bulk(client, actions, request_timeout=240):
            if not success:
                print('A document failed:', info)
                logger.error("Problem indexing document: ", info)
            else:
                total_docs += 1
                
        logger.info(f"Indexed {total_docs} datasets in {source}")
        print("Done")
    except Exception as e:
        logger.error("Problem indexing datasets: ", e)
        shutil.rmtree(DATA_PATH+source)
        exit()

    # Save indexation date
    try:
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        client.index(
            index = INDEX_UPDATES,
            body = {'data_source': source,
                    'indexation_date': now,
                    'n_docs': total_docs
                },
            refresh = True
        )
        logger.info(f"Updated {source} - {now}")
    except Exception as e:
        logger.error("Problem saving last update: ", e)
        shutil.rmtree(DATA_PATH+source)

    print("-"*40)
    print("Deleting temporal data...", end="")
    try:
        shutil.rmtree(DATA_PATH+source)
        print("ok")
        logger.info(f"Metadata from {source} deleted")
    except Exception as e:
        logger.error("Error deleting metadata", e)
    print("-"*40)