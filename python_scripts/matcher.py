import csv
import re
import os

FP_GEOAGE = 'geologic_age2.csv'
FP_PARTIES = 'parties.csv'
FP_INPUT = 'NMNH-PALEO-20180202_AL_openrefine.csv'
#FP_INPUT = r"C:\Users\littleh\Dropbox (Smithsonian)\EPICC Transcription\3. OpenRefine\NMNH-PALEO-20171120_AL-HL_openrefine.csv"
#FP_INPUT = r"D:\Dropbox\Dropbox (Smithsonian)\EPICC Transcription\3. OpenRefine\NMNH-PALEO-20171120_AL_openrefine.csv"
FP_OUTPUT = os.path.basename(FP_INPUT).rsplit('_', 1)[0] + '_emuprep.csv'


def standardize(val):
    """Standardizes the format of the string to improve matching"""
    return val.strip().replace('.', '').replace(' ', '').lower()


def match_ages(records, errors=None):
    """Matches new data to geologic ages already in EMu"""
    if errors is None:
        errors = []
    # Read geologic age info from geologic_age2.csv
    ages = {}
    with open(FP_GEOAGE, 'r', encoding='utf-8') as gainput:
        rows = csv.reader(gainput, dialect='excel')
        keys = next(rows)
        for row in rows:
            row = [s.strip() for s in row]
            data = dict(zip(keys, row))
            matchcol = data['Match column']
            try:
                geoage_rec = ages[matchcol]
            except KeyError:
                ages[matchcol] = data
            else:
                # This checks if the same catalog number occurs twice
                if geoage_rec != data:
                    _keys = []
                    _keys.extend(geoage_rec.keys())
                    _keys.extend(data.keys())
    # Match rows to age
    output = []
    for rec in records:
        try:
            rec.update(ages[rec['Geologic Age']])
        except KeyError:
            if rec['Geologic Age']:
                errors.append(rec['Geologic Age'])
                print('No match: {}'.format(rec['Geologic Age']))
        finally:
            output.append(rec)
    return output, errors


def match_parties(records, errors=None):
    """Matches parties new data to records already in EMu"""
    if errors is None:
        errors = []
    # Read file of parties in EMu
    parties = {}
    with open(FP_PARTIES, 'r', encoding='utf-8') as f:
        rows = csv.reader(f, dialect='excel')
        keys = next(rows)
        for row in rows:
            row = [s.strip() for s in row]
            data = dict(zip(keys, row))
            matchcol = standardize(data['Full'])
            try:
                party = parties[matchcol]
            except KeyError:
                parties[matchcol] = data
            else:
                # This checks if the same party occurs twice
                if party != data:
                    raise ValueError(party)
    # Match parties in rows
#    cols = ['Collector 1', 'Collector 2', 'Collector 3', 'Collector 4', 'Identifier']
    cols = ['Collector 1', 'Collector 2', 'Collector 3', 'Identifier']
    output = []
    for rec in records:
        for col in cols:
            name = standardize(rec[col])
            if name:
                irn = parties.get(name, {}).get('Parties IRN', 'create parties record')
                rec[col + ' IRN'] = irn
        output.append(rec)
    return output, errors



# Prevent overwriting of source files by checking in/out paths
assert FP_INPUT != FP_PARTIES
assert FP_INPUT != FP_OUTPUT


if __name__ == '__main__':
    records = []
    # Read data from the input file
    with open(FP_INPUT, 'r') as f:
        rows = csv.reader(f, dialect='excel')
        keys = next(rows)
        for row in rows:
            row = [s.strip() for s in row]
            records.append(dict(zip(keys, row)))
    # Match records to data from EMu
    output, errors = match_ages(records)
    output, errors = match_parties(records, errors)
    # Add new keys to the end of the file
    keys.extend([
        'AgeGeologicAgeEra_tab(1)',
        'AgeGeologicAgeSystem_tab(1)',
        'AgeGeologicAgeSeries_tab(1)',
        'AgeGeologicAgeStage_tab(1)',
        'AgeGeologicAgeEra_tab(2)',
        'AgeGeologicAgeSystem_tab(2)',
        'AgeGeologicAgeSeries_tab(2)',
        'AgeGeologicAgeStage_tab(2)',
        "NotNmnhText0(+group='chrono')",
        "NotNmnhType_tab(+group='chrono')",
        "NotNmnhWeb_tab(+group='chrono')",
        "NotNmnhAttributedToRef_nesttab(+ group='chrono':1).irn",
        "NotNmnhDate0(+group='chrono')",
        'Collector 1 IRN',
        'Collector 2 IRN',
        'Collector 3 IRN',
        'Collector 4 IRN',
        'Identifier IRN'
    ])
    if errors:
        print('\n'.join(sorted(list(set(errors)))))
    # Write updated records
    with open(FP_OUTPUT, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, dialect='excel')
        writer.writerow(keys)
        for row in output:
            writer.writerow([row.get(key, '') for key in keys])
