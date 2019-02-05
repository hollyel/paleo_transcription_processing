import csv
import re
import os

FP_WORKING = 'NMNH-PALEO-20180126_AC_OpenRefine.csv'
FP_REF = r"C:\Users\littleh\Dropbox (Smithsonian)\EPICC Transcription\2. Scripts\Master_Skeleton_Records_EPICC_v4.csv"
FP_OUTPUT = FP_WORKING.rsplit('_', 1)[0] + '_openrefineirn.csv'


assert FP_WORKING != FP_REF
assert FP_WORKING != FP_OUTPUT

ref_records = {}
with open(FP_REF, 'r') as gainput:
    rows = csv.reader(gainput, dialect='excel')
    keys = next(rows)
    for row in rows:
        row = [s.strip() for s in row]
        data = dict(zip(keys, row))
# input the name of the matching column from the reference file
        matchcol = data['CatNumber']
        try:
            ref_rec = ref_records[matchcol]
        except KeyError:
            ref_records[matchcol] = data
        else:
            # This checks if the same catalog number occurs twice
            if ref_rec != data:
                _keys = []
                _keys.extend(loc_rec.keys())
                _keys.extend(data.keys())


output = []
errors = []
with open(FP_WORKING, 'r') as f:
    rows = csv.reader(f, dialect='excel')
    keys = next(rows)
    for row in rows:
        row = [s.strip() for s in row]
        data = dict(zip(keys, row))
        data['CatNumber'] = data['Filename'].split('_')[2].lstrip('0')
# input the name of the matching column from the working file
        try:
            data.update(ref_records[data['CatNumber']])
        except KeyError:
            try:
                data['irn'] += ' | Catalog number not found'
                data['irn'] = data['irn'].lstrip('| ')
            except KeyError:
                data['irn'] = 'Catalog number not found'
        finally:
            output.append(data)

# output pulls all fields from FP_WORKING file. Enter keys.append for any column names needed from FP_REF reference file
    with open(FP_OUTPUT, 'w', encoding='utf-8', newline='') as f:
#If the file already has a column of the same name it will fill data into that pre-existing column
#        keys.append('irn')
        keys.append('BioEventSiteRef.irn')
        keys.append('LocSiteStationNumber')
        keys.append('LocSiteNumberSource')
        keys.append('LocPreciseLocation')
        keys.append('AdmDateModified')
#        keys.append('AdmDateInserted')
        keys.append('Metadata Note')
        writer = csv.writer(f, dialect='excel')
        writer.writerow(keys)
        for row in output:
            writer.writerow([row.get(key, '') for key in keys])
