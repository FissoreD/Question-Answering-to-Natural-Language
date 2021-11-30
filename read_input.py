from nltk.corpus import brown
import gensim
import os
import functools
#from PyDictionary import PyDictionary
from bs4 import BeautifulSoup
import requests
#dictionary = PyDictionary()


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
        try:
            return model.wv.similarity(wordA, wordBs[0])
        except KeyError:
            return float(0)
    x = [similarity(model, wordA, i) for i in wordBs]
    return 1 if max(x) > 0.999 else sum(x)/len(x)


def map_similarity_ordered(m):
    return sorted(list(m), key=lambda x: x[1], reverse=True)


def map_similarity(model, wordA, word_list):
    return map_similarity_ordered(map(lambda wordB: (wordB, similarity(model, wordA, wordB)), word_list))


def most_similar(m):
    return functools.reduce(lambda a, b: a if a[1] > b[1] else b, m)


wh_question = 'where,when,what,how,which'.split(',')


def read_input():
    return input().strip().split()


def work_input():
    return


def clean_input(str):
    return


def parse_sentence(str):
    res = []
    words = str.lower().strip().split()
    for w in words:
        r = requests.get("https://www.dictionary.com/browse/" +
                         w + "#", allow_redirects=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        cla = soup.find('span', {'class': 'luna-pos'})
        if cla == None:
            continue
        word_class = cla.text.strip()
        if word_class == 'noun':
            res.append(w)
        elif 'abbreviation' in word_class:
            defi = soup.find('div', attrs={"value": "1"}).get_text().replace(
                ':', '.').split('.')[0]
            res.append(defi)
    return res


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
    print(parse_sentence("ufo"))
    # create_model()
    # m = read_model()
    # print(similarity(m, 'world', 'world'))
    # print(map_similarity_ordered(map_similarity(m, 'president',
    #       ['date', 'leader', 'year', 'apple'])))
