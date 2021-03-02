#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Generates weighted yearly networks with informal collaboration."""

from collections import Counter, defaultdict
from itertools import product
from json import loads
from urllib.request import urlopen

import networkx as nx
import pandas as pd

ACK_FILE = "https://raw.githubusercontent.com/Michael-E-Rose/CoFE/"\
           "master/acks_min.json"
EDITOR_FILE = 'https://raw.githubusercontent.com/Michael-E-Rose/What-5-000-'\
              'Acknowledgements-Tell-Us-About-Informal-Collaboration-in-'\
              'Financial-Economics/master/075_editor_tenures/list.csv'
TARGET_FOLDER = "networks/"

MAX_YEAR = 2011
SPAN = 3  # yearly 3-year rolling networks


def add_attribute(network, item, val, attr='weight'):
    """Creates, appends or increases attribute of edges"""
    for entry in item:
        try:  # edge
            d = network.edges[entry[0], entry[1]]
        except KeyError:  # node
            d = network.nodes[entry]
        try:
            if isinstance(d[attr], str):
                d[attr] += ";" + val  # append
            else:
                d[attr] += val  # increase
        except KeyError:
            d[attr] = val  # create


def main():
    # READ IN
    eds = pd.read_csv(EDITOR_FILE).dropna(subset=['scopus_id'])
    eds = eds[eds['managing_editor'] == 1]
    eds['scopus_id'] = eds['scopus_id'].astype(int).astype(str)
    acks = loads(urlopen(ACK_FILE).read().decode("utf-8"))['data']

    # GENERATE NETWORKS
    C = defaultdict(lambda: nx.DiGraph(name="com"))
    for item in acks:
        pub_year = item['year']
        journal = item['journal']
        # Authors
        auths = [a['label'] for a in item['authors']]
        # Editors of this and previous year
        eds_range = range(pub_year-1, pub_year+1)
        mask = (eds['year'].isin(eds_range)) & (eds['journal'] == item['journal'])
        cur_editors = set(eds[mask]['scopus_id'])
        # Commenters
        coms = [c['label'] for c in item.get('com', []) if
                c.get('scopus_id', c['label']) not in cur_editors]
        coms.extend([c['label'] for c in item.get('dis', [])])
        coms.extend([c['label'] for c in item.get('phd', [])])
        # Add weighted links to this and the next SPAN-1 networks
        for cur_year in range(pub_year, pub_year+SPAN):
            if cur_year < 1997+SPAN-1 or cur_year > MAX_YEAR:
                continue
            com_links = list(product(coms, auths))
            C[cur_year].add_nodes_from(coms)
            C[cur_year].add_edges_from(com_links)
            add_attribute(C[cur_year], com_links, 1/len(auths))
            add_attribute(C[cur_year], com_links, journal, 'journal')
            add_attribute(C[cur_year], coms, 1.0, 'thanks')

    # WRITE OUT
    for year, G in C.items():
        ouf = f"{TARGET_FOLDER}/{year}.gexf"
        nx.write_gexf(G, ouf)


if __name__ == '__main__':
    main()
