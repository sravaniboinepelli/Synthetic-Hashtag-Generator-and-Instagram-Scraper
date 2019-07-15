import re
from itertools import groupby
import os
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import gensim.downloader as api

cleanup = re.compile(r'[^a-z0-9]')

def word_prob(word): 
	return dictionary.get(word, 0) / total

def entry(line): 
    w, c = line.split("\t", 2)
    return (w, int(c))

def segment(text): 
    text = re.sub(cleanup, ' ', text)
    probs, lasts = [1.0], [0]
    for i in range(1,len(text) + 1):
        prob_k, k = max((probs[j] * word_prob(text[j:i]), j)for j in range(max(0, i - max_word_length), i))
        probs.append(prob_k)
        lasts.append(k)
    words = []
    i = len(text)
    while i > 0:
        words.append(text[lasts[i]:i])
        i = lasts[i]
    words.reverse()
    return words, probs[-1]
        
dict_path = "dict.txt"
dictionary = dict(entry(line) for line in open(dict_path))
max_word_length = max(map(len, dictionary))
total = float(sum(dictionary.values()))

def words(text): return re.findall(r'\w+', text.lower())

WORDS = dictionary

def P(word, N=sum(WORDS.values())): 
    return WORDS[word] / N

def correction(word): 
    return max(candidates(word), key=P)

def candidates(word): 
    return (known([word]) or known(edits1(word)) or known(edits2(word)) or [word])

def known(words): 
    return set(w for w in words if w in WORDS)

def edits1(word):
    letters    = 'abcdefghijklmnopqrstuvwxyz'
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    inserts    = [L + c + R               for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)

def edits2(word): 
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))

print('Loading...')

model = api.load('fasttext-wiki-news-subwords-300')


def sentence_vec(sentence, emb_size):
    nwords = 0
    vocab = model.vocab
    sen_emb = np.zeros((emb_size), dtype = "float32")
    for word in sentence:
        if word in vocab:
            nwords = nwords+1 
            sen_emb = np.add(sen_emb, model[word])
    if nwords > 0:
        sen_emb = np.divide(sen_emb, nwords)
    return sen_emb

print('Model Loaded!')