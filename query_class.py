import time
from typing import List
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import read_input
# %%
output_folder = './output/'
keyCol = 'keyCol'
keyVal = 'value'
black_list = [
    'subject',
    'abstract',
    'owl #same as',
    'rdf -schema #comment',
    'rdf -schema #label',
    'wiki page i d',
    ' 2 2 -rdf -syntax -ns #type',
    'wiki page wiki link',
    'wiki page length',
    'wiki page revision i d',
    'wiki page external link',
    'wiki page uses template',
    'rdf -schema #see also',
    'prov #was derived from',
    'image',
    'wgs 8 4 _pos #geometry',
    'point',
    'direction',
    'image coat',
    'image flag'
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

    def __init__(self, domain: str, attribute,
                 model=read_input.read_model()) -> None:
        self.domain = domain.replace('"', "")
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
            if x == 'wiki page redirects':
                self.link = y
                self.query = self.create_query()
                self.send_query()
                return self.create_page_dico()
            if x in black_list:
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
            fp.write(str(self))

    def __str__(self, precision=5) -> str:
        bm = self.best_match
        return json.dumps([f"looking for {self.attribute} in {self.domain}", [{x: (bm[e][x] if x != 'probability' else str(round(bm[e][x], 2))) for x in bm[e]} for e in range(min(precision, len(bm)))]])

    def __repr__(self) -> str:
        return self.__str__()


class main:
    def __init__(self, w1: list,
                 model=read_input.read_model()) -> None:
        self.model = model
        self.domain = w1.pop().capitalize()
        self.res = [query(self.domain, w1.pop(), model=model)]
        self.res[-1].initiate()
        # print(self.res[-1])
        current_lvl: list = []
        next_lvl: list = []
        current_lvl.append(self.res[-1])
        while w1 and current_lvl:
            current_attribute = w1.pop()
            while current_lvl:
                current_object = current_lvl.pop(0)
                for i in current_object.best_match[:5]:
                    current_domain_list = i['res']
                    # Si la liste liée au domain courant à plus
                    # de 5 élément alors on le considère pas
                    if len(current_domain_list) > 5:
                        continue
                    for current_domain in current_domain_list:
                        # si le domain courant est un nombre on skip
                        try:
                            float(current_domain)
                            continue
                        except ValueError:
                            pass
                        print(i['value'], current_domain, current_attribute)
                        o1 = query(current_domain.replace(' ', '_'),
                                   current_attribute, model=self.model)
                        o1.initiate()
                        if o1.best_match != []:
                            self.res.append(o1)
                        next_lvl.append(o1)
            while next_lvl:
                current_lvl.append(next_lvl.pop(0))

    def get_result(self) -> List[query]:
        return self.res


if __name__ == '__main__':
    print('Charging')
    t = time.time()
    model = read_input.read_model()
    inp = read_input.parse_sentence(input('Enter your question : '))
    print(inp)
    m = main(inp, model)
    with open('./output/' + m.domain + '.json', 'w') as fp:
        fp.write(str(m.get_result()))

    print(time.time() - t)

"""
todo : 
    question avec deux reponses :
        ex : what is the birthdate and the place of birth of joe biden ?
    question avec implication :
        ex : What is the birthday of the président of USA ?
    les deux :
        ex : what is the birthdate and the birthplace of the president of USA ?

"""
# %%

"""
 What is the birthplace of the major of the capital of the country with Paris ?    

 What is the name of the president of the country with Venice ?
"""
