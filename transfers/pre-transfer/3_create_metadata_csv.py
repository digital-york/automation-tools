#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import pwd
import grp
import json
import csv
import codecs

md_csv = {}
MAPPING = {
    'title': 'dc.title',
    'description': 'dc.description',
    'uuid': 'dc.identifier',
    'doi': 'dc.identifier',
    'created': 'dc.date',
    'modified': 'dc.date',
    'access': 'dc.rights',
    'available': 'dc.date',
    'geographical': 'dc.coverage',
    'keyword': 'dc.subject',
    'link': 'dc.relation',
    'organisation': 'dc.contributor',
    'person': 'dc.contributor',
    'creator': 'dc.creator',
    'project': 'dc.related',
    'production': 'dc.date',
    'publication': 'dc.related',
    'publisher': 'dc.publisher',
    'temporal': 'dc.coverage'
}

def main(transfer_path):
    # path for metadata.json
    md_json = os.path.join(transfer_path, os.path.join('metadata', os.path.join('submissionDocumentation','metadata.json')))

    with open(md_json) as file:
        metadata = json.load(file)

        for x in metadata:
            y = has_value(metadata[x])
            if y is not None:
                if isinstance(y,dict):
                    process_dict(x,y)
                elif isinstance(y,list):
                    for l in y:
                        process_dict(x,l)
                else:
                    mp = MAPPING[x]
                    if mp in md_csv:
                        md_csv[mp].append(y)
                    else:
                        md_csv[mp] = [y]


    # path for metadata.csv
    md_csv_name = os.path.join(transfer_path, os.path.join('metadata','metadata.csv'))
    f = open(md_csv_name,'w')
    f.write(codecs.BOM_UTF8)
    ids = transfer_path.split('/')
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    csv_row = []
    csv_row.append('parts')
    for m in md_csv:
        for i in md_csv[m]:
            if i != None:
                csv_row.append(unicode(m).encode('utf8'))
    writer.writerow(csv_row)
    csv_row = []
    csv_row.append('objects/' + ids[len(ids) - 2])
    for m in md_csv:
        for i in md_csv[m]:
            if i != None:
                csv_row.append(unicode(i.replace('"','\'')).encode('utf8'))
    writer.writerow(csv_row)
    f.close

    print('Reset file permissions to archivematica:archivematica')

    uid = pwd.getpwnam("archivematica").pw_uid
    gid = grp.getgrnam("archivematica").gr_gid
    os.chown(md_csv_name, uid,gid)


# Check for empty strings, lists and dicts
def has_value(value):
    if value != None and value != '' and value != []:
        return value
    else:
        return None

# process hashes: available,geographical,link,organisation,person,production,project,temporal
def process_dict(name,value):
    if name == 'available':
        d = add_date(value)
        mp = MAPPING[name]
        if mp in md_csv:
            md_csv[mp].append(d)
        else:
            md_csv[mp] = [d]
    elif name == 'person':
        d = None
        if value['internal'] != []:
            for p in value['internal']:
                add_person(name,p,'name','role','uuid')
        if value['external'] != []:
            for pe in value['external']:
                add_person(name,pe, 'name', 'role', 'uuid')
        if value['other'] != []:
            for po in value['other']:
                add_person(name, po, 'name', 'role', 'uuid')
    elif name == 'organisation':
        d = None
        if value['name'] != '':
            d = value['name']
        if value['type'] != '':
            d += ', ' + value['type']
        if value['uuid'] != '':
            d += ' (uuid: ' + value['uuid'] + ')'
        mp = MAPPING[name]
        if mp in md_csv:
            md_csv[mp].append(d)
        else:
            md_csv[mp] = [d]
    elif name == 'project':
        d = None
        if value['title'] != '':
            d = value['title']
        if value['uuid'] != '':
            d += ' (uuid: ' + value['uuid'] + ')'
        mp = MAPPING[name]
        if mp in md_csv:
            md_csv[mp].append(d)
        else:
            md_csv[mp] = [d]
    elif name == 'publication':
        d = None
        if value['title'] != '':
            d = value['title']
        if value['type'] != '':
            d += ', ' + value['type']
        if value['uuid'] != '':
            d += ' (uuid: ' + value['uuid'] + ')'
        mp = MAPPING[name]
        if mp in md_csv:
            md_csv[mp].append(d)
        else:
            md_csv[mp] = [d]
    elif name == 'production':
        d = None
        if value['start'] != {}:
            d = add_date(value['start'])
        if value['end'] != {}:
            end = add_date(value['end'])
            if end is not None:
                d += ' - ' + end
        mp = MAPPING[name]
        if mp in md_csv:
            md_csv[mp].append(d)
        else:
            md_csv[mp] = [d]
    elif name == 'geographical':
        mp = MAPPING[name]
        if mp in md_csv:
            md_csv[mp].append(value[0])
        else:
            md_csv[mp] = [value[0]]
    elif name == 'temporal':
        d = None
        if value['start'] != {}:
            d = add_date(value['start'])
        if value['end'] != {}:
            end = add_date(value['end'])
            if end is not None:
                d += ' - ' + end
        mp = MAPPING[name]
        if mp in md_csv:
            md_csv[mp].append(d)
        else:
            md_csv[mp] = [d]
    elif name == 'link':
        if value != []:
            for link in value:
                d = None
                d = link['url']
                if link['description'] != "":
                    d += ' (' + link['description'] + ')'
                mp = MAPPING[name]
                if mp in md_csv:
                    md_csv[mp].append(d)
                else:
                    md_csv[mp] = [d]

def add_date(value):
    d = None
    if value['year'] != '':
        d = value['year']
    if value['month'] != '':
        d += '-' + value['month']
    if value['day'] != '':
        d += '-' + value['day']
    return d

def add_person(name,value,val1,val2,uuid):
    d = None
    if value[val1] != '' :
        if isinstance(value[val1],dict):
            d = value[val1]['last'] + ', ' + value[val1]['first']
        else:
            d = value[val1]
    if value[val2] != '':
        d += ', ' + value[val2]
    if value[uuid] != '':
        d += ' (uuid: ' + value['uuid'] + ')'

    if value[val2] == 'Creator':
        mp = MAPPING['creator']
    else:
        mp = MAPPING['person']

    if mp in md_csv:
        md_csv[mp].append(d)
    else:
        md_csv[mp] = [d]

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
