# Wikipedia Search Engine
##### Problem Statement
To design and implement a search engine from scratch on a Wikipedia corpus (English) of over 21 million articles (~85 Gb in size) to give search results within 3-4 seconds.
##### Overview
- The XML dump is parsed to get Wikipedia documents.
- Stop words removal and stemming using NLTK.
- An inverted index structure was created which contains posting lists of each word.
- While searching, these posting lists are retrieved to get document IDs, then TF-IDF is applied to get most relevant search results.
##### System requirements
- python3
- NLTK
- 85GB of free space for the corpus and 21GB for inverted index
##### To run
Create inverted index
```
python3 indexer.py <path to wikipedia dump>
```
Search
```
python3 search <search query>
```
