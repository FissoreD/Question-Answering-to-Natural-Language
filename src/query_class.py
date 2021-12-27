from SPARQLWrapper import SPARQLWrapper, JSON
import json
from read_input import update_txt
import read_input

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

    def __init__(self, domain: str, father="", proba=1,
                 model=read_input.read_model(), txt_panel=None) -> None:
        self.domain = domain.replace('"', "").replace("-", "_")
        self.father = father
        self.proba = proba
        self.model = model
        self.txt_panel = txt_panel
        self.sparql = self.create_sparql()
        self.link = self.create_link()
        self.query = self.create_query()
        self.send_query()
        self.create_page_dico()

    def initiate(self, attribute):
        self.attribute = attribute.lower().replace("-", "")
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
        try:
            self.page_json = self.sparql.query().convert()
        except Exception as e:
            update_txt(self.txt_panel,
                       'Error in send following query', tag='blue')
            update_txt(self.txt_panel, self.query, tag='blue')
            update_txt(self.txt_panel, e, tag='red')
            raise e

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
            # print(self.proba, i[1], self.proba * i[1])
            L.append(
                {
                    "father": f"{self.father} -> {removeHTTP(self.domain)} -> {i[0]} ({self.attribute})",
                    "probability": i[1] * self.proba,
                    "domain": removeHTTP(self.domain),
                    "value": i[0],
                    "wanted": self.attribute,
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


if __name__ == '__main__':
    Q = query('France')
    Q.initiate('capital')
    print(Q.best_match)
