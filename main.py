from os import unlink
from tkinter.constants import BOTH, END, TOP
from typing import List
import read_input
from query_class import query, removeHTTP
import time
import json
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from read_input import update_txt


class main:
    def __init__(self,  model=read_input.read_model()) -> None:
        self.model = model

    def launch_query(self, w1: List[str]):
        self.domain = w1.pop().capitalize()
        first_attribute = w1.pop()
        self.make_query(self.domain, f"{self.domain} -> {first_attribute}",
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
                            update_txt(txt_panel,
                                       f"{i['value']}, {current_domain}, {current_attribute}")
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
        L.sort(key=lambda x: float(x['probability']))
        return L

    def pretty_print(self, verbose=False):
        L = self.flat_list()
        return ["Probabilité : {} % - Résultat : {} of {}{}".format(
            int(float(e["probability"]) * 100),
            [removeHTTP(i) for i in e["res"]],
            [e['wanted']],
            ", - Father : {}".format(e["father"]) if verbose else "")
            for e in L[-10:]]


if __name__ == '__main__':
    questions = ["What is the children, birthdate and birthplace of the major of the capital of France ?",
                 "What is the birthdate and birthplace of founder of Microsoft ?",
                 "What is the name of the president of the country with Venice ?",
                 "What is the date of Valentine's-Day",
                 "What is the birthplace and the birthdate of Emmanuel_Macron ?"]
    root = tk.Tk()
    mainPanel = tk.PanedWindow(root, bg='red')

    underPanel = tk.PanedWindow(mainPanel)
    underPanel.pack(expand=1, fill=BOTH)

    m = main()

    entry = tk.Entry(underPanel)

    def calc_res():
        txt_panel.delete('1.0', END)
        t = time.time()
        inp = read_input.main(entry.get(), txt_panel)
        update_txt(txt_panel, inp)
        m.launch_query(inp)
        with open('./output/' + m.domain + '.json', 'w') as fp:
            json.dump(m.get_result(), fp)
        update_txt(txt_panel, json.dumps(m.flat_list(), indent=2))
        update_txt(txt_panel, m.pretty_print())
        update_txt(txt_panel, str(time.time() - t))

    sendButton = tk.Button(underPanel, text='Send',
                           command=calc_res)
    entry.pack(expand=1, fill='x')
    sendButton.pack(expand=1, fill='x')
    v = tk.StringVar(mainPanel, "1")

    radiopanel = tk.PanedWindow(mainPanel)

    values = {"Dictionary": "1",
              "Verbose List": "2",
              "Simply List": "3"}

    def swap_view(id):
        if m == None:
            return
        txt_panel.delete('1.0', END)
        if id.get() == '1':
            update_txt(txt_panel, json.dumps(m.flat_list(), indent=2))
        elif id.get() == '2':
            update_txt(txt_panel, m.pretty_print(verbose=True))
        elif id.get() == '3':
            update_txt(txt_panel, m.pretty_print(verbose=False))

    for (pos, (text, value)) in enumerate(values.items()):
        tk.Radiobutton(radiopanel, text=text, variable=v,
                       value=value, command=lambda: swap_view(v)).grid(column=pos, row=0, sticky='nsew')
    radiopanel.pack(expand=1, fill=BOTH)

    txt_panel = ScrolledText(mainPanel)
    txt_panel.pack(expand=1, fill=BOTH)
    mainPanel.pack(expand=1, fill=BOTH)
    root.mainloop()


"""
todo:
    question avec deux reponses:
        ex: what is the birthdate and the birthplace of joe biden ?
    question avec implication:
        ex: What is the birthday of the président of USA ?
    les deux:
        ex: what is the birthdate and the birthplace of the president of USA ?

"""
