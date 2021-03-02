#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Generates js for website to display the networks."""

import json
from glob import glob
from os.path import basename, splitext
from string import Template

import networkx as nx
from networkx.readwrite import json_graph

NETWORK_FOLDER = "./networks/"

# Templates
text_tmplte = Template(
    '$name<br>'
    'Thanks: $thanks_v (Rank: $thanks_r)<br>'
    'Betweenness cent. rank: $betw_r<br>'
    'Eigenvector cent. rank: $eig_r')
node_tmplte = Template('{id:$id,label:"$label",title:"$title",'
                       'x:$x,y:$y,value:1,group:"$group"}')
edge_tmplte = Template('{from:$fr,to:$to}')


def compress(d, drops):
    """Remove specified entries from sub-dict."""
    for sd in d:  # Remove enumeration and compress
        for drop in drops:
            sd.pop(drop, None)
    return d


def main():
    for fname in glob(NETWORK_FOLDER + "*.gexf"):
        year = splitext(basename(fname))[0]
        H = nx.read_gexf(fname)

        ring = json_graph.node_link_data(H)
        drops = ["journal", "year", "jel", "title", "id"]
        ring['links'] = compress(ring['links'], drops)
        with open(f"{year}/ring.json", 'w') as ouf:
            ouf.write(json.dumps(ring))


if __name__ == '__main__':
    main()
