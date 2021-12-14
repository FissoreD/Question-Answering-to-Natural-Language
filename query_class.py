import time
from typing import Dict, List
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


def removeHTTP(s: str):
    return s if 'http' not in s else s.split("/")[-1]


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

    def __init__(self, domain: str, attribute, father="", proba=1,
                 model=read_input.read_model()) -> None:
        self.domain = domain.replace('"', "").replace("-", "_")
        self.father = father
        self.proba = proba
        print("attribute : ", attribute)
        self.attribute = attribute.lower().replace("-", "")
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
            #print(self.proba, i[1], self.proba * i[1])
            L.append(
                {
                    "father": f"{self.father} -> {i[0]} ({self.attribute})",
                    "probability": i[1] * self.proba,
                    "domain": removeHTTP(self.domain),
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

    def __str__(self) -> str:
        return json.dumps(self.dict_without_float())

    def dict_without_float(self, precision=5):
        bm = self.best_match
        return [f"looking for {self.attribute} in {self.domain}", [{x: (bm[e][x] if x != 'probability' else str(round(bm[e][x], 2))) for x in bm[e]} for e in range(min(precision, len(bm)))]]

    def __repr__(self) -> str:
        return self.__str__()


class main:
    def __init__(self, w1: list,
                 model=read_input.read_model()) -> None:
        self.model = model
        self.domain = w1.pop().capitalize()
        first_attribute = w1.pop()
        self.make_query(
            self.domain, f"-> {first_attribute}", first_attribute, 1, [], first_attribute)

        # print(self.res[-1])
        current_lvl: list = []
        next_lvl: list = []
        current_lvl.append((self.res[self.domain], 1, self.domain))
        while w1 and current_lvl:
            current_attribute = w1.pop()
            while current_lvl:
                current_object, _, father = current_lvl.pop(0)
                print(current_object)
                for k in current_object:
                    for i in k.best_match[:5]:
                        current_domain_list = i['res']
                        current_proba = i['probability']
                        # TODO
                        current_father = f"{father} -> {i['value']}"
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
                            print(i['value'], current_domain,
                                  current_attribute)
                            self.make_query(current_domain, current_father, first_attribute,
                                            current_proba, next_lvl, current_attribute)

            first_attribute = current_attribute

            while next_lvl:
                current_lvl.append(next_lvl.pop(0))
        self.last_lvl = current_lvl

    def make_query(self, current_domain, current_father, first_attribute, current_proba, next_lvl, current_attribute):
        def send_query(s):
            o1 = query(current_domain.replace(' ', '_'),
                       s, father=f"{current_father} ({first_attribute}) -> {removeHTTP(current_domain)}", model=self.model, proba=current_proba)
            o1.initiate()
            if o1.best_match != []:
                try:
                    self.res[current_domain].append(o1)
                except KeyError:
                    self.res[current_domain] = [o1]
                except AttributeError:
                    self.res = {self.domain: [o1]}
                next_lvl.append(
                    ([o1], current_proba, f"{current_father} ({first_attribute}) -> {removeHTTP(current_domain)}"))

        print(type(current_attribute))
        if type(current_attribute) == list:
            for s in current_attribute:
                send_query(s)
        else:
            send_query(current_attribute)

    def get_result(self):
        return {i: [k.dict_without_float() for k in self.res[i]] for i in self.res}

    def get_last_lvl(self):
        return [i[0].dict_without_float() for i in self.last_lvl]

    def flat_list(self):
        L = []
        for x, y, z in self.last_lvl:
            [L.extend(i) for i in [k.dict_without_float()[1] for k in x]]
        print(L[:2])
        L.sort(key=lambda x: float(x['probability']))
        return L

    def pretty_print(self, verbose=False):
        L = self.flat_list()
        [print("Probabilité : {} % - Résultat : {}".format(int(float(e["probability"]) * 100), [removeHTTP(i) for i in e["res"]]), "- Father : {}".format(e["father"]) if verbose else "")
         for e in L[-10:]]


if __name__ == '__main__':
    questions = ["What is the children, birthdate and birthplace of the major of the capital of France ?",
                 "What is the birthdate and birthplace of foundator of Microsoft ?",
                 "What is the name of the president of the country with Venice ?",
                 "What is the date of Valentine's-Day",
                 "What is the birthplace and the birthdate of Emmanuel_Macron ?"]

    print('Charging')
    t = time.time()
    model = read_input.read_model()
    inp = read_input.main(questions[1])
    print(inp)
    m = main(inp, model)
    with open('./output/' + m.domain + '.json', 'w') as fp:
        json.dump(m.get_result(), fp)
    # print(json.dumps(m.get_last_lvl(), indent=2))
    print(json.dumps(m.flat_list(), indent=2))
    m.pretty_print()
    print(time.time() - t)

"""
todo : 
    question avec deux reponses :
        ex : what is the birthdate and the birthplace of joe biden ?
    question avec implication :
        ex : What is the birthday of the président of USA ?
    les deux :
        ex : what is the birthdate and the birthplace of the president of USA ?

"""
