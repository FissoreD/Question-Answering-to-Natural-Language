import re
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import json

# %%


def sparql_to_csv(res):
    res = list(map(lambda x: x.split(','), res.split('\n')))
    hd = res.pop(0)
    return pd.DataFrame(res, columns=hd)


def create_sparql():
    return SPARQLWrapper("http://dbpedia.org/sparql")


def send_query(query):
    sparql = create_sparql()
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results


def get_all_info(word):
    return send_query("SELECT ?page ?output WHERE { <http://dbpedia.org/resource/"+word+">  ?page  ?output}")


def get_lines_from_word(word, dico, a, b):
    list_of_content = dico['results']['bindings']
    L = set()
    for elt in list_of_content:
        col1 = elt[a]['value']
        col2 = elt[b]['value']
        if word in col1:
            L.add(col2.split('/')[-1])
    return L


# def query_for_properties(category):
#     string = "select distinct * where {?property rdfs:domain <http://dbpedia.org/ontology/" + \
#         category+"> ; rdfs:label ?l .}"
#     return send_query(string)


# def get_entity_of_type(word):
#     string = 'select distinct * where {?info rdfs:label "' + \
#         word+'"@en; gold:hypernym ?hypernym .}'
#     return send_query(string)


def get_info():
    return send_query("""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dbp: <http://dbpedia.org/property/>
    SELECT distinct ?person WHERE
    {   
        ?person dbo:birthPlace <http://dbpedia.org/resource/Paris> .
    }  
    """)


# %%

def main(a, b):
    info1 = get_all_info(a)
    info2 = get_all_info(b)
    L1 = get_lines_from_word(a, info2, 'page', 'output')
    L2 = get_lines_from_word(b, info1, 'page', 'output')
    print(L1, L2)


# %%
"""
    TODO:
        retravailler les synonymes dans le cas par exemple de 
        preseident et leaderName
"""
