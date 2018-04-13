#!/usr/bin/env python
# Copyright (C) 2017 Emanuel Goncalves

import igraph
import pandas as pd


STRING_FILE = 'data/resources/string/9606.protein.links.full.v10.5.txt'
STRING_ALIAS_FILE = 'data/resources/string/9606.protein.aliases.v10.5.txt'
STRING_PICKLE = 'data/igraph_string.pickle'

BIOGRID_FILE = 'data/ppi/BIOGRID-ORGANISM-Homo_sapiens-3.4.157.tab2.txt'
BIOGRID_PICKLE = 'data/igraph_biogrid.pickle'

OMNIPATH_FILE = 'data/resources/omnipath/omnipathdb.org.txt'


def import_ppi(ppi_pickle):
    return igraph.Graph.Read_Pickle(ppi_pickle)


def build_omnipath_ppi(is_directed=True, is_signed=True):
    df = pd.read_csv(OMNIPATH_FILE, sep='\t')

    if is_directed:
        df = df.query('is_directed == 1')

    if is_signed:
        df = df[df[['is_stimulation', 'is_inhibition']].sum(1) == 1]

    # igraph network
    net_i = igraph.Graph(directed=is_directed)

    # Initialise network lists
    edges = [(px, py) for px, py in df[['source_genesymbol', 'target_genesymbol']].values]
    vertices = list({p for p1, p2 in edges for p in [p1, p2]})

    # Add nodes
    net_i.add_vertices(vertices)

    # Add edges
    net_i.add_edges(edges)
    net_i.es['interaction'] = list(df['is_stimulation'].replace(0, -1))

    # Simplify
    net_i = net_i.simplify(combine_edges=max)
    print(net_i.summary())

    return net_i


def build_biogrid_ppi(exp_type=None, int_type=None, organism=9606, export_pickle=False):
    # 'Affinity Capture-MS', 'Affinity Capture-Western', 'Co-crystal Structure', 'Co-purification',
    # 'Reconstituted Complex', 'PCA', 'Two-hybrid'

    # Import
    biogrid = pd.read_csv(BIOGRID_FILE, sep='\t')

    # Filter organism
    biogrid = biogrid[
        (biogrid['Organism Interactor A'] == organism) & (biogrid['Organism Interactor B'] == organism)
    ]

    # Filter non matching genes
    biogrid = biogrid[
        (biogrid['Official Symbol Interactor A'] != '-') & (biogrid['Official Symbol Interactor B'] != '-')
    ]

    # Physical interactions only
    if int_type is not None:
        biogrid = biogrid[[i in int_type for i in biogrid['Experimental System Type']]]
    print('Experimental System Type considered: {}'.format('; '.join(set(biogrid['Experimental System Type']))))

    # Filter by experimental type
    if exp_type is not None:
        biogrid = biogrid[[i in exp_type for i in biogrid['Experimental System']]]
    print('Experimental System considered: {}'.format('; '.join(set(biogrid['Experimental System']))))

    # Interaction source map
    biogrid['interaction'] = biogrid['Official Symbol Interactor A'] + '<->' + biogrid['Official Symbol Interactor B']

    # Unfold associations
    biogrid = {
        (s, t) for p1, p2 in biogrid[['Official Symbol Interactor A', 'Official Symbol Interactor B']].values
        for s, t in [(p1, p2), (p2, p1)] if s != t
    }

    # Build igraph network
    # igraph network
    net_i = igraph.Graph(directed=False)

    # Initialise network lists
    edges = [(px, py) for px, py in biogrid]
    vertices = list({p for p1, p2 in biogrid for p in [p1, p2]})

    # Add nodes
    net_i.add_vertices(vertices)

    # Add edges
    net_i.add_edges(edges)

    # Simplify
    net_i = net_i.simplify()
    print(net_i.summary())

    # Export
    if export_pickle:
        net_i.write_pickle(BIOGRID_PICKLE)

    return net_i


def build_string_ppi(score_thres=900, export_pickle=False):
    # ENSP map to gene symbol
    gmap = pd.read_csv(STRING_ALIAS_FILE, sep='\t')
    gmap = gmap[['BioMart_HUGO' in i.split(' ') for i in gmap['source']]]
    gmap = gmap.groupby('string_protein_id')['alias'].agg(lambda x: set(x)).to_dict()
    gmap = {k: list(gmap[k])[0] for k in gmap if len(gmap[k]) == 1}
    print('ENSP gene map: ', len(gmap))

    # Load String network
    net = pd.read_csv(STRING_FILE, sep=' ')

    # Filter by moderate confidence
    net = net[net['combined_score'] > score_thres]

    # Filter and map to gene symbol
    net = net[[p1 in gmap and p2 in gmap for p1, p2 in net[['protein1', 'protein2']].values]]
    net['protein1'] = [gmap[p1] for p1 in net['protein1']]
    net['protein2'] = [gmap[p2] for p2 in net['protein2']]
    print('String: ', len(net))

    #  String network
    net_i = igraph.Graph(directed=False)

    # Initialise network lists
    edges = [(px, py) for px, py in net[['protein1', 'protein2']].values]
    vertices = list(set(net['protein1']).union(net['protein2']))

    # Add nodes
    net_i.add_vertices(vertices)

    # Add edges
    net_i.add_edges(edges)

    # Add edge attribute score
    net_i.es['score'] = list(net['combined_score'])

    # Simplify
    net_i = net_i.simplify(combine_edges='max')
    print(net_i.summary())

    # Export
    if export_pickle:
        net_i.write_pickle(STRING_PICKLE)

    return net_i


if __name__ == '__main__':
    build_biogrid_ppi(int_type=['physical'])
    build_string_ppi()
    print('[INFO] PPIs pickle files created')
