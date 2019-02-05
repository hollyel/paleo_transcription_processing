import csv
import re
import os

#checker = input("Initials: ")
#setNum = input("Transcription set date: ")


FP_EMU = 'Master_Skeleton_Records_EPICC_v6.csv'
#FP_TRANSCRIPTIONS = 'NMNH-Paleo-' + setNum + '_' + checker + '_accepted.csv'
FP_TRANSCRIPTIONS = r"C:\Users\littleh\Dropbox (Smithsonian)\EPICC Transcription\1. Initial Review\NMNH-PALEO-20171208_AL_accepted.csv"
FP_OUTPUT = FP_TRANSCRIPTIONS.rsplit('_', 1)[0] + '_merged.csv'

KEYS = [
    'Collector',
    'Date',
    'Ident By',
    'Formation',
    'Locality',
    'Memoranda',
    'No',
    'Notebook',
    'Pages',
    'Field',
    'Survey of the'
]

KEYMAP = {
    'ident': 'Ident By',
    'in charge': 'Collector',
    #'name': 'Collector',
    'note book': 'Notebook',
    'page': 'Pages'
}


RE_KEY = re.compile('(' + '|'.join(KEYS) + ')$')


def format_key(key):
    return '{} (Parsed)'.format(key)


# Confirm that output path is not the same as one of the inputs
assert FP_TRANSCRIPTIONS != FP_EMU
assert FP_TRANSCRIPTIONS != FP_OUTPUT


# Read the EMu data into a dict keyed to CatNumber
emu_records = {}
with open(FP_EMU, 'r', encoding='utf-8') as f:
    rows = csv.reader(f, dialect='excel')
    keys = next(rows)
    for row in rows:
        row = [s.strip() for s in row]
        data = dict(zip(keys, row))
        catnum = data['CatNumber']
        try:
            emu_rec = emu_records[catnum]
        except KeyError:
            emu_records[catnum] = data
        else:
            # This checks if the same catalog number occurs twice
            if emu_rec != data:
                _keys = []
                _keys.extend(emu_rec.keys())
                _keys.extend(data.keys())
                for key in set(_keys):
                    if emu_rec[key] != data[key]:
                        if key in ['LocBarcode']:
                            emu_rec[key] += ' | ' + data[key]
                        else:
                            raise ValueError('{} repeats with different values in {}'.format(catnum, FP_EMU))


# Clean up and merge the transcription data with the data from EMu
output = []
emu_keys = keys
parsed_keys = []
with open(FP_TRANSCRIPTIONS, 'r') as f:
    rows = csv.reader(f, dialect='excel')
    keys = next(rows)
    for row in rows:
        row = [s.strip() for s in row]
        data = dict(zip(keys, row))
        data['CatNumber'] = data['Filename'].split('_')[2].lstrip('0')
        # Match on CatNumber to update with data from EMu
        try:
            data.update(emu_records.get(data['CatNumber']))
        except KeyError:
            # Add a note if the catalog number is not found
            try:
                data['NMNH Notes'] += ' | Catalog number not found'
                data['NMNH Notes'] = data['NMNH Notes'].lstrip('| ')
            except KeyError:
                data['NMNH Notes'] = 'Catalog number not found'
            #raise ValueError('CatNumber not found: {}'.format(data['CatNumber']))
        except TypeError:
            # Add a note if the catalog number is not found
            try:
                data['NMNH Notes'] += ' | Catalog number not found'
                data['NMNH Notes'] = data['NMNH Notes'].lstrip('| ')
            except KeyError:
                data['NMNH Notes'] = 'Catalog number not found'
            #raise ValueError('CatNumber not unique: {}'.format(data['CatNumber']))
        # Parse out the labeled data from the Additional Info column
        labeled = {}
        unlabeled = []
        addl_info = data['Additional Information']
        data['Additional Information Orig'] = addl_info
        addl_info = re.sub(r'No\.? ', 'No.: ', addl_info)
        for val in [s.strip() for s in addl_info.split('|')]:
            try:
                key, val = [s.strip() for s in val.split(':', 1)]
            except ValueError:
                unlabeled.append(val)
            else:
                key = KEYMAP.get(key.lower().strip('. '), key).rstrip('.')
                matches = RE_KEY.search(key)
                if key.lower() in keys:
                    parsed_keys.append(key)
                    labeled.setdefault(key, []).append(val.rstrip('. '))
                elif matches is not None:
                    match = matches.group(0)
                    labeled.setdefault(match, []).append(val.rstrip('. '))
                    val = key.replace(match, '').strip()
                    if val:
                        unlabeled.append(val.rstrip('. '))
                #elif (re.search('\d', key) is not None
                #    or re.search('[a-z]', key) is None
                #    or len(key) > 16):
                #    print('{}: Malformatted key: {}'.format(data['CatNumber'], key))
                #    unlabeled.append(val)
                else:
                    print('{}: Unrecognized key: {}'.format(data['CatNumber'], key))
                    parsed_keys.append(key)
                    unlabeled.append(val)
        labeled = {k: ' | '.join(v) for k, v in labeled.items()}
        data['Additional Information'] = ' | '.join(unlabeled)
        mask = '{}: {} already populated (exists={}, parsed={})'
        for key, val in labeled.items():
            try:
                data[key]
            except KeyError:
                pass #data[key] = val
            else:
                # Warn if field already exists and value does not match
                if data[key] != labeled[key]:
                    print(mask.format(data['CatNumber'], key, data[key], labeled[key]))
            data[format_key(key)] = val
        # Add row to output
        output.append(data)

# Get the unique list of keys (maintaining order and including keys parsed
# of of additional notes)
if parsed_keys:
    print('The following keys were found in Additional Notes:\n+ ' +
          '\n+ '.join(sorted(list(set(parsed_keys)))))
keys = emu_keys + keys + [format_key(key) for key in KEYS]
keys.insert(keys.index('Additional Information'), 'Additional Information Orig')
keys = [k for i, k in enumerate(keys) if k not in keys[:i]]
keys.append('CollEvent_change')
while True:
    try:
        with open(FP_OUTPUT, 'w', encoding='utf-16-be', newline='') as f:
            writer = csv.writer(f, dialect='excel')
            writer.writerow(keys)
            for row in output:
                writer.writerow([row.get(key, '') for key in keys])
            break
    except PermissionError as e:
        input('Please close {} and hit ENTER'.format(FP_OUTPUT))
