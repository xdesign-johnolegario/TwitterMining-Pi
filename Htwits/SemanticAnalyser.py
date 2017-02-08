# semantic analysis for tweets

from sys import argv
#from io import BytesIO
import json
#reading csv file
def readChunks():

    import csv
    import pandas as pd
    from pprint import pprint

    with open("tweet_raw.csv") as csvfile:
        colnames =['created_at', 'id', 'idstr', 'text1']
        rdr = pd.read_csv(csvfile, header=None,
                          names=colnames,
                          usecols=["created_at", "id", "idstr", 'text1']).set_index('created_at')['text1'].to_dict()
        pprint(rdr)

        """
        rdr = pd.read_csv(csvfile, header=None,
                          names=colnames,
                          usecols=["created_at", "id", "idstr","text1"]).to_dict()""""""

        #del rdr['idstr']
        #rdr.iloc[:,(0,3)]


def values(q):
    p_t = {}

    for key, value in q.items():
        p_t[key] = value[0], value[1]
    return p_t

def display(data):
    presults = {'created_at': [],'id': []}
    for i in range(0, 2):
        p = values(data)
        for i, value in p:
            presults[value].append(i+1)
        print(presults)"""
readChunks()

