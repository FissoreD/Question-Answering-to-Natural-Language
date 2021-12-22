from tkinter.constants import END
from nltk.corpus import brown
import gensim
import os
import functools
from nltk.stem import PorterStemmer
from tkinter.scrolledtext import ScrolledText
from bs4 import BeautifulSoup
import requests
from tkinter import INSERT
THRESHOLD = 0.5


def update_txt(txt_panel: ScrolledText, string, tag='', end='\n'):
    if txt_panel is None:
        print(string, end=end)
        return
    if not isinstance(string, list):
        string = [string]
    for i in string:
        txt_panel.insert(INSERT, f"{i} {end}", tag)
    txt_panel.update()
    txt_panel.see(END)


def create_model():
    model = gensim.models.Word2Vec(brown.sents())
    model.save('brown.embedding')


def split_on_capital_letter(s: str):
    return "".join([i if i.islower() else (' ' + i.lower()) for i in s])


def read_model():
    if not os.path.exists('./brown.embedding'):
        create_model()
    return gensim.models.Word2Vec.load('brown.embedding')


def similarity(model, wordA, wordB):
    wordBs = wordB.split()
    if len(wordBs) == 1:
        stemmer = PorterStemmer()
        if wordA == wordB or (True and stemmer.stem(wordA) == stemmer.stem(wordB)):
            return 1
        try:
            return model.wv.similarity(wordA, wordBs[0])
        except KeyError:
            return float(0)
    x = [similarity(model, wordA, i) for i in wordBs]
    return 1 if wordB.replace(' ', '') == wordA else sum(x)/len(x)


def map_similarity_ordered(m):
    return sorted(list(m), key=lambda x: x[1], reverse=True)


def map_similarity(model, wordA, word_list):
    return map_similarity_ordered([i for i in map(lambda wordB: (wordB, similarity(model, wordA, wordB)), word_list) if i[1] > THRESHOLD])


def most_similar(m):
    return functools.reduce(lambda a, b: a if a[1] > b[1] else b, m)


def read_input():
    return input().strip().split()


accepted_classes = ["noun", "abbreviation"]
friendly_list = [chr(ord('a') + i) for i in range(26)] + \
    [chr(ord('A') + i) for i in range(26)] + list("_-'")


def parse_sentence(question, txt):
    res = []

    words = question.lower().strip().split()
    for w in words:
        [w := w.replace(i, "") for i in list(w) if i not in friendly_list]
        if w == "":
            continue
        url = "https://www.dictionary.com/browse/" + w.replace("'", "-") + "#"
        try:
            r = requests.get(url)
        except Exception as e:
            if txt != None:
                update_txt(txt, f"Error in loading {url} page", tag='blue')
                update_txt(txt, e, tag='red')
            raise e
        soup = BeautifulSoup(r.text, 'html.parser')
        cla = soup.find('span', {'class': 'luna-pos'})
        if cla == None:
            res.append(w)
            continue
        word_class = cla.text.strip()
        if word_class[-1] == ',':
            word_class = word_class[:-1]
        update_txt(txt, f"{(w, word_class)}")
        if word_class in accepted_classes:
            res.append(w)
        # elif word_class == 'abbreviation':
        #     # defi = soup.find('div', attrs={"value": "1"}).get_text().replace(
        #     #     ':', '.').split('.')[0]
        #     res.append(defi)
    return res


def parse_and(question, txt):
    temp = question.split(" and ")
    if len(temp) == 2:
        first = parse_sentence(temp[0], txt)
        second = parse_sentence(temp[1], txt)
        return [first + [second[0]],  *second[1:]]
    res = parse_sentence(temp[0], txt)
    return [[res[0]]] + res[1:]


def main(question, txt):
    return parse_and(question, txt)


if __name__ == '__main__':
    # print(parse_and(
    #     "What is the birthplace and the birthdate of Emmanuel_Macron ?", tk.Entry()))

    stemmer = PorterStemmer()
    print(stemmer.stem("founded"))
    print(stemmer.stem("foundator"))
    print(stemmer.stem("troubling"))
    print(stemmer.stem("troubled"))

    m = read_model()
    print(similarity(m, 'predecessor', 'birthplace'))
    print(similarity(m, 'leader', 'president'))
    print(similarity(m, 'founder', 'founded'))
    print(similarity(m, 'founder', 'founders'))
    print(map_similarity_ordered(map_similarity(m, 'president',
          ['date', 'leader', 'year', 'apple'])))
