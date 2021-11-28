import re
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import json
import read_input
import re
# %%
keyCol = 'keyCol'
keyVal = 'value'


def sparql_to_csv(l):
    hd = [keyCol, keyVal]
    return pd.DataFrame(l, columns=hd)


def create_sparql():
    return SPARQLWrapper("http://dbpedia.org/sparql")


def json_to_dico(json, a, b):
    list_of_content = json['results']['bindings']
    D = dict()
    for elt in list_of_content:
        x, y = read_input.split_on_capital_letter(
            elt[a][keyVal].split('/')[-1]), elt[b][keyVal]
        if x in D:
            D[x].append(y)
        else:
            D[x] = [y]
    # print(D)
    return D


def send_query(query):
    print(query)
    sparql = create_sparql()
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results


def get_all_info(word):
    lang = 'en'
    link = word if 'http' in word else f"http://dbpedia.org/resource/{word}"
    query = f"""
        SELECT ?{keyCol} ?{keyVal} WHERE {{
            <{link}>  ?{keyCol}  ?{keyVal} .
        }}"""
    # print(query)
    res = json_to_dico(send_query(query), keyCol, keyVal)
    if 'wiki page redirects' in res:
        res = get_all_info(res['wiki page redirects'][0])
    if 'abstract' in res:
        res.pop('abstract')
    return res


def write_to_file(frame):
    with open('result.json', 'w') as fp:
        json.dump(frame, fp)


def get_lines_from_word(word, dico, a, b):
    list_of_content = dico['results']['bindings']
    L = set()
    for elt in list_of_content:
        col1 = elt[a][keyVal]
        col2 = elt[b][keyVal]
        if 'wikiPageRedirects' in col1:
            # print('here')
            return get_lines_from_word(word, get_all_info(col2.split("/")[-1]), a, b)
        if word.lower() in col1.lower():
            # print(elt[b])
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


if __name__ == '__main__':
    pd.set_option('display.max_rows', None)
    infos = get_all_info('USA')
    model = read_input.read_model()
    m = read_input.map_similarity(model, 'president', infos.keys())
    write_to_file(infos)
    L = []
    for i in range(min(len(m), 5)):
        L.append(
            {
                "probability": str(round(m[i][1] * 100, 3)) + " %",
                "value": m[i][0],
                "res": [i for i in set(infos[m[i][0]]) if i != ""]
            })
    print(json.dumps(L, indent=4))

# %%
"""
    TODO:
        retravailler les synonymes dans le cas par exemple de
        president et leaderName
"""
