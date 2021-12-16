import read_input
from query_class import query, removeHTTP
import time
import json


class main:
    def __init__(self, w1: list,
                 model=read_input.read_model()) -> None:
        self.model = model
        self.domain = w1.pop().capitalize()
        first_attribute = w1.pop()
        self.make_query(self.domain, f"-> {first_attribute}",
                        first_attribute, 1, [], first_attribute)
        # current lvl = la pile à traiter au temps i
        current_lvl: list = []
        # next lvl = la pile à traiter au temps i + 1
        next_lvl: list = []
        # le nivau courant contient la liste des queries associées
        # au père, la proba du père et le domain du père
        current_lvl.append((self.res[self.domain], 1, self.domain))
        # tant que la file des sujets de la requête n'est pas vide
        while w1:
            current_attribute = w1.pop()
            # tant que l'étage courant n'est pas vide
            while current_lvl:
                current_object, _, father = current_lvl.pop(0)
                # pour tous les éléments de la liste de ???
                for k in current_object:
                    # pour tous les meilleurs resultats de la requête précédente
                    for i in k.best_match[:5]:
                        current_domain_list = i['res']
                        current_proba = i['probability']
                        current_father = f"{father} -> {i['value']}"
                        # Si la liste liée au domain courant à plus
                        # de 5 élément alors on la considère pas
                        if len(current_domain_list) > 5:
                            continue
                        # pour tous les éléments associés à la categorie courante
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
            # on bascule le next lvl dans current lvl
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
    inp = read_input.main(questions[0])
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
