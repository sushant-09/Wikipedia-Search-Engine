import sys
import os
import timeit
import Stemmer
import re
import json
from math import log10
from collections import defaultdict

if len(sys.argv)<3:
    print('too few arguments')
    sys.exit(1)


search_keys=[]
for i in range(2,len(sys.argv)):
    search_keys.append(sys.argv[i])

stemmer=Stemmer.Stemmer('english')
fields={'t':'title', 'b':'body', 'i':'infobox', 'r':'references', 'l':'links', 'c':'category'}

result={}
for search_key in search_keys:
    if ':' in search_key:
        search_key=search_key.split(':')[1]
    word=search_key.strip()
    word=stemmer.stemWord(word.lower())
    result[search_key]={}
    for field in ['title', 'body', 'infobox', 'category', 'references', 'links']:
        result[search_key][field]=[]
    indexfile=open('../inverted_indexes/2020201003/index.txt','r')
    for line in indexfile:
        line=line.strip()
        line=line.split(':')
        key=line[0]
        if key==word:
            entries=line[1].split(',')
            for entry in entries:
                # print(entry)
                docId, occurences=entry.split('-')
                for i in occurences.split('|'):
                    result[search_key][fields[i[0]]].append(int(docId))
    indexfile.close()



d=open("index_files/docidtotitle.json","r")
docidtotitle=json.load(d)
d.close()

w=open("index/hash.json","w")
wordpos=json.load(w)
w.close()

weights = {}
weights["t"] = 500
weights["i"] = 50
weights["r"] = 50
weights["l"] = 50
weights["c"] = 50
weights["b"] = 1


def preprocess():
    pass
def normal_query(query):
    global weights
    query=preprocess(query)
    for word in query:
        filetoopen=wordpos[word][0]
        f=open(filetoopen,"r")
        f.seek(wordpos[word][1])
        postings=f.readline.strip().split(":")[1]
        print(postings)