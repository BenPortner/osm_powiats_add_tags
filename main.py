import json
import pandas as pd
import osmapi

def add_polish_name(osm_without_polish_name):

    # open change set
    api.ChangesetCreate({u"comment": u"Added name:pl tag to Polish powiats where it was missing."})

    # loop over all elements
    for i, id, name in osm_without_polish_name[['@id', 'name']].itertuples():

        # get osm objects from api
        if 'relation' in id:
            numbers_only = id.replace('relation/', '')
            osm_handle = api.RelationGet(numbers_only)
            datatype = 'relation'
        elif 'node' in id:
            numbers_only = id.replace('node/', '')
            osm_handle = api.NodeGet(numbers_only)
            datatype = 'node'

        # check again for name:pl tag to make sure not to overwrite existing one
        if 'name:pl' not in osm_handle['tag']:
            # set name:pl tag
            osm_handle['tag']['name:pl'] = name

            # send changes to api
            if datatype == 'relation':
                new_data = api.RelationUpdate(osm_handle)
            elif datatype == 'node':
                new_data = api.NodeUpdate(osm_handle)

        pass

    # close change set
    return api.ChangesetClose()

def add_english_names(osm_without_english_name):

    # open change set
    api.ChangesetCreate({u"comment": u"Added name:en tag to Polish powiats where it was missing. English names matched via 'wikidata' tag."})

    # loop over all elements
    for i, id, name in osm_without_english_name[['@id', 'label_en']].itertuples():

        # get osm objects from api
        if 'relation' in id:
            numbers_only = id.replace('relation/', '')
            osm_handle = api.RelationGet(numbers_only)
            datatype = 'relation'
        elif 'node' in id:
            numbers_only = id.replace('node/', '')
            osm_handle = api.NodeGet(numbers_only)
            datatype = 'node'

        # check again if tag is not already present
        # also make sure not to overwrite the name:pl tags from before
        if 'name:en' not in osm_handle['tag'] and \
                'name:pl' in osm_handle['tag']:

            # set name:en tag
            osm_handle['tag']['name:en'] = name

            # send changes to api
            if datatype == 'relation':
                new_data = api.RelationUpdate(osm_handle)
            elif datatype == 'node':
                new_data = api.NodeUpdate(osm_handle)

        pass

    # close change set
    return api.ChangesetClose()


# connect to osm api
api = osmapi.OsmApi(api="https://api.openstreetmap.org/", username = u"BenPortner", password = u"(removed)")

# load osm data from disk (contains Overpass query result)
osm_powiats = "./data/osm_powiat.geojson"
with open(osm_powiats, 'r', encoding='UTF-8') as f:
    owm_powiats = json.load(f)
osm_powiat_props = pd.DataFrame([f['properties'] for f in owm_powiats['features']])

# load wikidata from disk (contains SPARQL query result)
wiki_powiats = "./data/wikidata_powiats.csv"
wiki_powiats_props = pd.read_csv(wiki_powiats)

# extract wikidata id from hyperlinks
wiki_powiats_props['wikidata'] = wiki_powiats_props['powiat'].str.replace(r'.*?(Q[0-9]+)',r'\1')

# merge osm data and wiki data on wikidata id
merged = wiki_powiats_props[['wikidata','label_en','label_pl']].merge(osm_powiat_props[['@id', 'wikidata','name','name:pl','name:en']], on='wikidata')

# sanity check: wikidata label_pl should match osm name
merged_sane = merged[merged['label_pl'] == merged['name']]

# filter osm entries with name:pl
no_name_pl = merged_sane[merged_sane['name:pl'].isna()]

# add name:pl tags where missing
changeset_id = add_polish_name(no_name_pl)

# filter osm entries with english name
no_name_en = merged_sane[merged_sane['name:en'].isna()]

# add name:en tags where missing
changset_id = add_english_names(no_name_en)

pass