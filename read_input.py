from nltk.corpus import brown
import gensim
import os
import functools
from nltk.stem import PorterStemmer
from nltk.stem import LancasterStemmer
# from PyDictionary import PyDictionary
from bs4 import BeautifulSoup
import requests
# dictionary = PyDictionary()
THRESHOLD = 0.5


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
        lancaster = LancasterStemmer()
        if wordA == wordB or lancaster.stem(wordA) == lancaster.stem(wordB):
            return 1
        try:
            return model.wv.similarity(wordA, wordBs[0])
        except KeyError:
            return float(0)
    x = [similarity(model, wordA, i) for i in wordBs]
    return 1 if max(x) > 0.999 or wordB.replace(' ', '') == wordA else sum(x)/len(x)


def map_similarity_ordered(m):
    return sorted(list(m), key=lambda x: x[1], reverse=True)


def map_similarity(model, wordA, word_list):
    return map_similarity_ordered([i for i in map(lambda wordB: (wordB, similarity(model, wordA, wordB)), word_list) if i[1] > THRESHOLD])


def most_similar(m):
    return functools.reduce(lambda a, b: a if a[1] > b[1] else b, m)


wh_question = 'where,when,what,how,which'.split(',')


def read_input():
    return input().strip().split()


def work_input():
    return


def clean_input(str):
    return


accepted_classes = ["noun", "abbreviation"]
friendly_list = [chr(ord('a') + i) for i in range(26)] + \
    [chr(ord('A') + i) for i in range(26)] + list("_-'")


def parse_sentence(question):
    res = []

    words = question.lower().strip().split()
    for w in words:
        [w := w.replace(i, "") for i in list(w) if i not in friendly_list]
        if w == "":
            continue
        r = requests.get("https://www.dictionary.com/browse/" +
                         w.replace("'", "-") + "#", allow_redirects=True)
        soup = BeautifulSoup(r.text, 'html.parser')
        cla = soup.find('span', {'class': 'luna-pos'})
        if cla == None:
            res.append(w)
            continue
        word_class = cla.text.strip()
        if word_class[-1] == ',':
            word_class = word_class[:-1]
        print((w, word_class))
        if word_class in accepted_classes:
            res.append(w)
        # elif word_class == 'abbreviation':
        #     # defi = soup.find('div', attrs={"value": "1"}).get_text().replace(
        #     #     ':', '.').split('.')[0]
        #     res.append(defi)
    return res


def parse_and(question):
    temp = question.split(" and ")
    if len(temp) == 2:
        first = parse_sentence(temp[0])
        second = parse_sentence(temp[1])
        return [first + [second[0]],  *second[1:]]
    res = parse_sentence(temp[0])
    return [[res[0]]] + res[1:]


def main(question):
    return parse_and(question)


# def parse_sentence2():
#     words = input().strip().split()

#     res = []
#     for w in words:
#         print(w)
#         try:
#             d = dictionary.meaning(w, disable_errors=True)
#             if d != None:
#                 r = d.keys()
#                 if 'Noun' in r:
#                     res.append(w)
#         except:
#             pass

#     return res

if __name__ == '__main__':
    print(parse_and("What is the birthplace and the birthdate of Emmanuel_Macron ?"))

    # m = read_model()
    # print(similarity(m, 'leader', 'president'))

    lancaster = LancasterStemmer()
    print(lancaster.stem("founded"))
    print(lancaster.stem("foundator"))
    print(lancaster.stem("troubling"))
    print(lancaster.stem("troubled"))

    # print(map_similarity_ordered(map_similarity(m, 'president',
    #       ['date', 'leader', 'year', 'apple'])))
