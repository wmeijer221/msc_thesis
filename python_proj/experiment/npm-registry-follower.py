
# import requests
# import json

db: str = "https://replicate.npmjs.com"



# r: requests.Response = requests.get(db)

# a = r.json()

# print(json.dumps(a, indent=4))


import os
import pymongo
from bson.json_util import dumps
client = pymongo.MongoClient(db)
change_stream = client.changestream.collection.watch()
for change in change_stream:
    print(dumps(change))

