#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Generates html for website to display the network rankings."""

from glob import glob
from os.path import basename, splitext

import networkx as nx
import pandas as pd

SOURCE_FOLDER = "./networks/"

pd.set_option('display.max_colwidth', None)


def giant(H):
    """Return giant component of a network."""
    components = nx.weakly_connected_components(H)
    return H.subgraph(sorted(components, key=len, reverse=True)[0])


def main():
    for file in sorted(glob(SOURCE_FOLDER + "*.gexf")):
        year = basename(splitext(file)[0])
        H = nx.read_gexf(file)
        G = giant(H)
        df = pd.DataFrame(index=sorted(H.nodes()))
        df['Name'] = pd.Series(nx.get_node_attributes(H, "label"))

        df["Number of thanks"] = pd.Series(nx.get_node_attributes(H, "thanks"))
        df["Number of thanks"] = df["Number of thanks"].fillna(0).astype(int)
        df = df.sort_values("Number of thanks", ascending=False)
        df["Number of thanks"] = df["Number of thanks"].astype(str).str.replace("0", "")
        df["Betweenness centrality"] = pd.Series(
            nx.betweenness_centrality(G.to_undirected(), weight="weight"))
        df["Eigenvector centrality"] = pd.Series(
            nx.eigenvector_centrality_numpy(G, weight="weight"))
        df["Eigenvector centrality"] = df["Eigenvector centrality"].clip(lower=0)

        fname = f"{year}/ranking.html"
        df.to_html(fname, index=False, escape=False, float_format="%.4f",
                   classes="table table-hover sortable", na_rep="")


if __name__ == '__main__':
    main()
