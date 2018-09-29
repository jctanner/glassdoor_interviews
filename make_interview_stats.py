#!/opt/anaconda3/bin/python

import glob
import json
import os
import shutil
from pprint import pprint

import pandas as pd

from get_interviews import get_firms


def get_interviews_records(filter=None):

    records = {}

    firms = get_firms(filter=filter)
    firms = [x.lower() for x in firms]

    datafiles = glob.glob('data/interviews/*.json')
    for df in datafiles:
        coname = os.path.basename(df).replace('.json', '')
        with open(df, 'r') as f:
            jdata = json.loads(f.read())

        if firms and coname.lower() not in firms:
            continue

        for k,v in jdata.items():
            if not isinstance(v, (float, int)):
                if v == '--':
                    jdata[k] = 0
                elif v.endswith('k'):
                    v = v.replace('k', '')
                    v = float(v) * 1000
                try:
                    jdata[k] = float(v)
                except:
                    pass

        records[coname] = jdata
    #import epdb; epdb.st()
    return records


def records_to_frame(records):
    df_records = []
    unique_keys = []
    for k,v in records.items():
        for k2,v2 in v.items():
            if k2 == 'total':
                continue
            if k2 not in unique_keys:
                unique_keys.append(k2)
            df_records.append((k2, v2))

    df = pd.DataFrame.from_records(df_records)
    return (unique_keys, df_records, df)

if __name__ == "__main__":

    records = get_interviews_records()
    (keys, df_records, df) = records_to_frame(records)
