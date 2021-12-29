import tkinter.ttk as ttk
from os import terminal_size, unlink
from tkinter.constants import BOTH, END, TOP
from typing import List
import read_input
from query_class import query, removeHTTP
import time
import json
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from read_input import update_txt
from sys import argv


class main:
    def __init__(self, txt_panel,  model=read_input.read_model()) -> None:
        self.model = model
        self.txt_panel = txt_panel

    def launch_query(self, w1: List[str]):
        self.domain = w1.pop().capitalize()
        current_lvl: list = []
        next_lvl: list = []
        self.last_lvl: dict = {}
        self.make_query(self.domain, "", 1, current_lvl, w1.pop())
        while w1:
            current_attribute = w1.pop()
            # tant que l'étage courant n'est pas vide
            while current_lvl:
                current_object = current_lvl.pop(0)
                # pour tous les meilleurs resultats de la requête précédente
                for i in current_object:
                    current_domain_list = i['res']
                    current_proba = i['probability']
                    current_father = i['father']
                    # Si la liste liée au domain courant à plus
                    # de 5 élément alors on ne la considère pas
                    if len(current_domain_list) > 5:
                        continue
                    # pour tous les éléments associés à la categorie courante
                    for current_domain in current_domain_list:
                        try:
                            # si le current_domain est un float alors on ne le considère pas
                            float(current_domain)
                            continue
                        except:
                            pass
                        self.make_query(current_domain, current_father,
                                        current_proba, next_lvl, current_attribute)
            # on bascule le next lvl dans current lvl
            while next_lvl:
                current_lvl.append(next_lvl.pop(0))

    def make_query(self, current_domain, current_father, current_proba, next_lvl, current_attribute):
        def send_query(attribute, o1, is_last_lvl=False):
            update_txt(self.txt_panel,
                       f"Looking for {attribute} in {removeHTTP(current_domain)}", 'green')
            o1.initiate(attribute)
            next_lvl.append(o1.best_match[:5])
            if is_last_lvl:
                self.last_lvl[attribute].extend(o1.best_match[:5])
            if o1.best_match != []:
                try:
                    self.res[current_domain].append(o1)
                except KeyError:
                    self.res[current_domain] = [o1]
                except AttributeError:
                    self.res = {self.domain: [o1]}
        o1 = query(current_domain.replace(' ', '_'),
                   father=current_father, model=self.model, proba=current_proba)
        if type(current_attribute) == list:
            if len(self.last_lvl) == 0:
                for elt in current_attribute:
                    self.last_lvl[elt] = []
            for s in current_attribute:
                send_query(s, o1, True)
        else:
            send_query(current_attribute, o1)

    def get_result(self):
        return {i: [k.dict_without_float() for k in self.res[i]] for i in self.res}

    def flat_list(self):
        for key, value in self.last_lvl.items():
            self.last_lvl[key] = []
            for elt in value:
                elt['probability'] = str(elt['probability'])
                self.last_lvl[key].append(elt)
            self.last_lvl[key].sort(key=lambda x: float(x['probability']))
        return self.last_lvl

    def pretty_print(self, verbose=False):
        def white_line(): update_txt(self.txt_panel, "")
        def dotted_line(): update_txt(self.txt_panel, "  " + "~"*35)
        for key, value in self.flat_list().items():
            update_txt(self.txt_panel, f"Looking for: {key}")
            for x in reversed(value[-10:]):
                update_txt(self.txt_panel, "  Probability : {} %".format(
                    int(float(x["probability"]) * 100)), end='', tag='red'),
                if verbose:
                    update_txt(txt_panel, "\n  Path : {}\n ".format(
                        x["father"]), end='', tag='magenta')
                update_txt(self.txt_panel, "Results : ", tag='green')
                for elt in x['res']:
                    update_txt(self.txt_panel,
                               f"    {removeHTTP(elt)}", tag='blue')
                dotted_line()
            white_line()


if __name__ == '__main__':
    questions = ["What are the birthdate, birthplace and spuse of the major of the capital of France ?",
                 "What is the birthplace and the birthdate of Emmanuel_Macron ?",
                 "What are the birthdate and birthplace of founder of Microsoft ?",
                 "What is the name of the president of the country with Venice ?",
                 "What is the date of Valentine's-Day ?",
                 "Who is the president of USA ?",
                 "Who is the author of the Divine_Comedy ?"]
    if not '-shell' in argv:
        """ On crée pas défault l'interface graphique si l'utilisateur n'a pas spécifié la sortie sur le terminal """

        root = tk.Tk()
        root.title("Question answering")
        mainPanel = tk.PanedWindow(root)

        underPanel = tk.PanedWindow(mainPanel)
        underPanel.pack(fill=BOTH)

        entry = ttk.Combobox(underPanel, values=questions)

        default_font = tk.font.nametofont("TkDefaultFont")
        import tkinter.font as tkf

        entry.bind("<FocusIn>", lambda e: setDefault(False))
        entry.bind("<FocusOut>", lambda e: setDefault(True))
        entry.set("Enter your question")
        entry.configure(font=(default_font.cget('family'),
                        default_font.cget('size'), 'italic'))

        def get_current_font():
            return tkf.Font(font=entry['font'])

        def setDefault(b):
            """ Pour faire apparaître le hint text en italique 'Enter your question' si le champ de saisie est vide et n'est pas sélectionné """
            if b:
                if entry.get() == '':
                    entry.set("Enter your question")
                    entry.configure(font=(default_font.cget('family'),
                                          default_font.cget('size'), 'italic'))
            else:
                if entry.get() == 'Enter your question' and get_current_font().cget('slant') == 'italic':
                    entry.set("")

                entry.configure(font=default_font)

        def calc_res():
            """ Méthode qui sera appelée après avoir envoyer la question """
            if get_current_font().cget('slant') == 'italic':
                return
            txt_panel.delete('1.0', END)
            t = time.time()
            inp = read_input.main(entry.get(), txt_panel)
            update_txt(txt_panel, inp)
            m.launch_query(inp)
            update_txt(txt_panel, json.dumps(m.flat_list(), indent=2))
            update_txt(txt_panel, m.pretty_print())
            update_txt(txt_panel, str(time.time() - t))

        entry.bind('<Return>', lambda e: calc_res())

        sendButton = tk.Button(underPanel, text='Send',
                               command=calc_res)

        entry.grid(row=0, column=0, sticky="nsew")
        sendButton.grid(row=0, column=1)
        underPanel.columnconfigure(0, weight=1)

        v = tk.StringVar(mainPanel, "1")

        radiopanel = tk.PanedWindow(mainPanel)

        values = {"Dictionary": "1",
                  "Verbose List": "2",
                  "Simply List": "3"}

        def swap_view(id):
            """
            Radio button pour passer d'une réponse détaillée à une réponse ne contenant que l'essentiel ou a une réponse présentant
            l'arbre de recherche de chacun des résultats.
            """
            if m == None:
                return
            txt_panel.delete('1.0', END)
            if id.get() == '1':
                update_txt(txt_panel, json.dumps(m.flat_list(), indent=2))
            elif id.get() == '2':
                m.pretty_print(verbose=True)
            elif id.get() == '3':
                m.pretty_print(verbose=False)

        for (pos, (text, value)) in enumerate(values.items()):
            tk.Radiobutton(radiopanel, text=text, variable=v,
                           value=value, command=lambda: swap_view(v)).grid(column=pos, row=0, sticky='nsew')
        radiopanel.pack()

        txt_panel = ScrolledText(mainPanel)
        color_list = ['red', 'green', 'blue', 'magenta']
        for i in color_list:
            txt_panel.tag_config(i, foreground=i)
        txt_panel.pack(expand=1, fill=BOTH)
        mainPanel.pack(expand=1, fill=BOTH)
        m = main(txt_panel)
        root.mainloop()

    else:
        """ Sinon on affiche le résultat sur le terminal """
        t = time.time()
        m = main(None)
        i = read_input.main(input('Enter you question : '), None)
        m.launch_query(i)
        update_txt(None, m.pretty_print())
        update_txt(None, str(time.time() - t))
