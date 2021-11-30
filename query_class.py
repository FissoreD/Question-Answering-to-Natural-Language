import re
from SPARQLWrapper import SPARQLWrapper, JSON
from gensim.utils import identity
import pandas as pd
import json
import read_input
import re
# %%
output_folder = './output/'
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


class query:
    """
    Class representing a query for dbpedia :
        To create a query pass:
            the subject of the query
            the field of the subject looking for
            optional : the model of gensim
        You must call the initiate method to compile
        the class
    """

    def __init__(self, domain, attribute,
                 model=read_input.read_model()) -> None:
        self.domain = domain
        self.attribute = attribute.lower()
        self.model = model
        self.sparql = self.create_sparql()
        self.link = self.create_link()
        self.query = self.create_query()

    def initiate(self):
        self.send_query()
        self.create_page_dico()
        self.find_association()
        self.calc_best_match()

    def create_sparql(self):
        return SPARQLWrapper("http://dbpedia.org/sparql")

    def create_link(self):
        return self.domain if 'http' in self.domain else f"http://dbpedia.org/resource/{self.domain}"

    def create_query(self):
        lang = 'en'
        return f"""
            SELECT ?{keyCol} ?{keyVal} WHERE {{
                <{self.link}>  ?{keyCol}  ?{keyVal} .
            }}"""

    def send_query(self):
        self.sparql.setQuery(self.query)
        self.sparql.setReturnFormat(JSON)
        self.page_json = self.sparql.query().convert()

    def create_page_dico(self):
        list_of_content = self.page_json['results']['bindings']
        self.page_dico = dict()
        for elt in list_of_content:
            x, y = read_input.split_on_capital_letter(
                elt[keyCol][keyVal].split('/')[-1]), elt[keyVal][keyVal]
            if x in info_to_remove:
                continue
            if x in self.page_dico:
                self.page_dico[x].append(y)
            else:
                self.page_dico[x] = [y]

    def find_association(self):
        self.similarity = read_input.map_similarity(
            self.model, self.attribute, self.page_dico.keys())

    def calc_best_match(self):
        L = []
        for i in self.similarity:
            L.append(
                {
                    "probability": i[1],
                    "value": i[0],
                    "res": [j for j in set(self.page_dico[i[0]]) if j != ""]
                })
        self.best_match = L

    def write_dbpedia(self):
        file_name = output_folder + self.domain + '.json'
        with open(file_name, 'w') as fp:
            json.dump(self.page_json, fp, indent=4)

    def write_res(self):
        file_name = output_folder + self.domain + '_res.json'
        with open(file_name, 'w') as fp:
            json.dump(self.best_match, fp, indent=4)

    def __str__(self, precision=5) -> str:
        bm = self.best_match
        return json.dumps([{x: (bm[e][x] if x != 'probability' else str(round(bm[e][x], 2))) for x in bm[e]} for e in range(precision)], indent=2)

    def __repr__(self) -> str:
        return self.__str__()


class main:
    def __init__(self, w1: str, w2: str,
                 model=read_input.read_model()) -> None:
        self.model = model
        self.o1: query = query(w1, w2, model=self.model)
        self.o2: query = query(w2, w1, model=self.model)
        self.o1.initiate()
        self.o2.initiate()

    def best_result(self):
        s1 = sum([i['probability'] for i in self.o1.best_match])
        s2 = sum([i['probability'] for i in self.o2.best_match])
        return self.o1 if s1 > s2 else self.o2


if __name__ == '__main__':
    model = read_input.read_model()
    m = main('France', 'capital')
    print(m.best_result())
