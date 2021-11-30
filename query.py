import sys
import re
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import json
import read_input
import re
# %%
keyCol = 'keyCol'
keyVal = 'value'
info_to_remove = [
    'subject',
    'abstract',
    'owl #same as',
    'rdf -schema #comment',
    'rdf -schema #label',
    'wiki page i d',
    ' 2 2 -rdf -syntax -ns #type',
    'wiki page wiki link',
    'wiki page revision i d',
    'wiki page external link',
    'wiki page uses template'
]


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
    for i in info_to_remove:
        res.pop(i, None)
    return res


def write_to_file(s):
    with open('result.json', 'w') as fp:
        json.dump(s, fp, indent=4)


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


# %%
def find_association(a, b):
    global model
    infos = get_all_info(a)
    m = read_input.map_similarity(model, b.lower(), infos.keys())
    return m, infos


def main(a, b):
    global model
    r1, infos1 = find_association(a, b)
    r2, infos2 = find_association(b, a)
    L1 = [r1[i] for i in range(min(len(r1), 5))]
    L2 = [r2[i] for i in range(min(len(r2), 5))]
    return (L1, infos1) if sum([i[1] for i in L1]) > sum([i[1] for i in L2]) else (L2, infos2)


def myPrint1(m, infos):
    L = []
    for i in range(min(len(m), 5)):
        L.append(
            {
                "probability": str(round(m[i][1] * 100, 3)) + " %",
                "value": m[i][0],
                "res": [i for i in set(infos[m[i][0]]) if i != ""]
            })
    return L


if __name__ == '__main__':
    my_questions = ["What is the population of Italy ?",
                    "What is the capital of France ?", "What is the date of Christmas ?"]

    pd.set_option('display.max_rows', None)
    model = read_input.read_model()

    key_words = read_input.parse_sentence(my_questions[2])

    if (len(key_words) != 2):
        print("This kind of question is not already supported")
        sys.exit()

    a, b = main(key_words[0], key_words[1].capitalize())
    x = myPrint1(a, b)
    write_to_file(x)
    print(json.dumps(x, indent=4))
