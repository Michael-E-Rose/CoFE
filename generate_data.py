#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com
"""Consolidates names of persons and institutions in acknowledgment files.

Acknowledgement files are parsed based on the category (beginning of line
until colon) and stored in hierarchical structure.
"""

import os
import re
from datetime import datetime
from json import dumps

import pandas as pd


INPUT_FOLDER = "./data/raw_acks/"
PERSON_CONSOL_FILE = "./data/persons.csv"
AFF_CONSOL_FILE = "./data/institutions.csv"

# Categories indicating persons to consolidate
person_cats = ['editor', 'com', 'phd', 'ref', 'dis']
# Categories indicating affiliations to conslidate
inst_cats = ['sem', 'aff', 'former', 'aff', 'vis']
# Categories whose information will be added to the author
personal_cats = ['former', 'aff', 'vis', 'fund', 'phd']


def clean_aff(entry):
    """Remove specific strings from an institution name to ease matching."""
    clean = (entry.strip()
                  .replace("AT THE UNIVERSITY", "UNIVERSITY")
                  .replace("OF THE UNIVERSITY", "UNIVERSITY")
                  .replace("DEPT ", "DEPARTMENT "))
    useless = ["THE ", "FINANCE DEPARTMENT, ", "DEPARTMENT OF FINANCE, ",
               "DEPARTMENT OF ACCOUNTING AND FINANCE, ",
               "ECONOMICS DEPARTMENT, ", "DEPARTMENT OF ECONOMICS, ",
               "DEPARTMENT OF ECONOMICS AND FINANCE, ", "SCHOOL OF BUSINESS, ",
               "SCHOOL OF ECONOMICS, ", "SCHOOL OF ECONOMICS AND MANAGEMENT, ",
               "SCHOOL OF MANAGEMENT, ", "GRADUATE SCHOOL OF BUSINESS, ",
               "RESEARCH DEPARTMENT, ",
               "DEPARTMENT OF FINANCE AND ECONOMICS, ",
               "DEPARTMENT OF BUSINESS ADMINISTRATION, "]
    for prefix in useless:
        clean = clean[clean.startswith(prefix) and len(prefix):]
    return clean.replace('"', '').replace(',', '')


def consolidate(l, mapping, label):
    """Return an alias from a lookup dictionary if present."""
    info = []
    for entry in l:
        if label == 'Institution':
            entry = clean_aff(entry)
        new = mapping.get(entry.replace(".", "").strip())
        if new is None:
            print(f">>> {label} {entry.strip()} without mapping")
            continue
        if label == 'Person':
            new.update({'name': entry.strip()})
        info.append(new)
    return info


def parse_file(lines, fname):
    """Parse each line of a collection of lines (from file) depending on the
    category, which is indicatin by the beginning of the line.
    """
    metainfo = fname.split('/')
    biblio = {'journal': metainfo[3], 'year': int(metainfo[4])}
    out = []
    for line in lines:
        tokens = line.strip().split(": ", 1)
        cat = tokens[0].lower()
        # Initiate entry
        if cat == "title":
            title = tokens[1]
            d = biblio.copy()
            d['title'] = title
            authors = []
        # Initatiate author-specific information
        elif cat in ('auth', 'auth-cor'):
            try:
                author = pers_map[tokens[1].replace(".", "")].copy()
            except KeyError:
                print(f">>> Person {tokens[1]} without mapping")
                author = {}
            if cat == 'auth-cor':
                author.update({'corresponding': True})
            # Assert all authors are mapped to Scopus
            try:
                _ = author["scopus_id"]
            except KeyError:
                print(f">>> Author {author} w/o Scopus ID")
            author.update({'name': tokens[1]})
            authors.append(author)
        # Add information to author
        elif cat in personal_cats:
            if cat in inst_cats:
                info = consolidate(tokens[1].split(';'), inst_map, "Institution")
            elif cat in person_cats:
                info = consolidate(re.split(",|;", tokens[1]), pers_map, "Person")
            else:
                info = tokens[1].split("; ")
            authors[-1].update({cat: info})
        # Split and consolidate commenters, referees, editors, seminars, etc.
        elif cat in person_cats or cat in inst_cats:
            try:
                new = int(tokens[1])
            except ValueError:
                if cat in person_cats:
                    mapping = pers_map
                    key = "Person"
                else:
                    mapping = inst_map
                    key = "Institution"
                new = consolidate(re.split(",|;", tokens[1]), mapping, key)
            if cat in d:
                d[cat].extend(new)
            else:
                d[cat] = new
        # Split conferences
        elif cat == "con":
            d[cat] = tokens[1].split("; ")
        # Combine information
        elif cat == "":
            d['authors'] = authors
            out.append(d)
        # Any other relevant information (jel, ra, prev, misc, order)
        else:
            d[cat] = re.split(", |; ", tokens[1])
    return out


def list_input_files():
    """Return list of text files containing acknowledgements."""
    files = []
    for root, subdirs, filenames in os.walk(INPUT_FOLDER):
        for filename in filenames:
            if not filename.endswith('dat'):
                continue
            files.append(os.path.join(root, filename))
    return files


def read_person_mapping():
    """Read person mapping and return dict."""
    # Read in
    df = pd.read_csv(PERSON_CONSOL_FILE, keep_default_na=False)
    df['alias'] = df[['first_name', 'middle_name', 'last_name']].apply(
        lambda x: " ".join(x).replace("  ", " ").strip(), axis=1)
    # Create dictionary
    df.loc[df['scopus_id'] == "", 'scopus_id'] = None
    df = df.set_index('alias')
    d = df[['label']].to_dict(orient="index")
    d.update(df[['label', 'scopus_id']].dropna().to_dict(orient="index"))
    return d

# Read mapping files
pers_map = read_person_mapping()
inst_map = pd.read_csv(AFF_CONSOL_FILE, index_col=0)['alias'].to_dict()


def main():
    paper_info = []
    for file in list_input_files():
        with open(file, 'r') as inf:
            new = parse_file(inf.readlines(), file)
        paper_info.extend(new)

    now = datetime.now()
    s = {'data': paper_info, 'date': now.strftime("%Y-%m-%d"),
         'creator': 'Michael E. Rose (Michael.Ernst.Rose@gmail.com)'}
    with open("acks.json", 'w') as ouf:
        ouf.write(dumps(s, sort_keys=True, indent=1))
    with open("acks_min.json", 'w') as ouf:
        ouf.write(dumps(s, sort_keys=True))


if __name__ == '__main__':
    main()
