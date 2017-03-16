import json
from pprint import pprint

def readfile():
    thetweets = []
    with open('htweetings1.json') as json_data:
        d = json.load(json_data)
        json_data.close()
        for k in d:
            thetweet = {
                'id': k["id"],
                'created': k["created_at"],
                'tweets': k["score"]
            }
            thetweets.append(thetweet)

    with open('converted.json', 'w') as out:
        json.dump(thetweets, out, sort_keys = True, indent = 4)

readfile()