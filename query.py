import re
from SPARQLWrapper import SPARQLWrapper, CSV
import pandas as pd

# %%


def sparql_to_csv(res):
    res = list(map(lambda x: x.split('","'), res.split('"\n"')))
    hd = res.pop(0)
    return pd.DataFrame(res, columns=hd)


def create_sparql():
    return SPARQLWrapper("http://dbpedia.org/sparql")


def send_query(query):
    sparql = create_sparql()
    sparql.setQuery(query)

    sparql.setReturnFormat(CSV)
    results = sparql.query().convert()
    return results.decode('utf-8').strip()


def query_for_properties(category):
    string = "select distinct * where {?property rdfs:domain <http://dbpedia.org/ontology/" + \
        category+"> ; rdfs:label ?l .}"
    return send_query(string)


def get_entity_of_type(word):
    string = 'select distinct * where {?info rdfs:label "' + \
        word+'"@en; gold:hypernym ?hypernym .}'
    return send_query(string)


def get_info():
    return send_query("""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dbp: <http://dbpedia.org/property/>
    SELECT distinct ?name ?birthDate WHERE
    {   
        ?person dbo:birthPlace <http://dbpedia.org/resource/Paris> .
        ?person dbo:birthDate ?birthDate .
        ?person dbp:name ?name  .
        filter(regex(?name, ".+")) .
        filter(?birthDate >= xsd:date("2000-01-01"))
    }  
    """)


# %%
