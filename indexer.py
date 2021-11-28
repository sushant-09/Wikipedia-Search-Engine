import sys
import xml.sax
import re
from collections import defaultdict
from nltk.corpus import stopwords
import Stemmer
import timeit
import os
import json
import glob
from heapq import heapify,heappop, heappush

stemmer = Stemmer.Stemmer('english')
sw_list=stopwords.words('english')
sw_dict=defaultdict(int)
for i in sw_list:
   sw_dict[i]=1
inverted_index={}
DOCSPERINTERMEDIATE=30000                ##change here
idtotitle={}
docsParsed=0
lif=0
key_offset={}
total_tokens=0
total_keys=0

def remove_links(text):
   text = re.sub(r'http[^\ ]*\ ', r' ', text)
   return text

def remove_html(text):
   if (type(text) is list):
      text=' '.join(text)
   text = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;', r' ', text)
   return text

def remove_sc(text):          #special characters
   text = re.sub(r'\—|\%|\$|\'|\||\.|\*|\[|\]|\:|\;|\,|\{|\}|\(|\)|\=|\+|\-|\_|\#|\!|\`|\"|\?|\/|\>|\<|\&|\\|\u2013|\n|°|“|”|’|‘|@|»|«|~', r' ', text)
   return text

def remove_sw(text):          #stop words
   if(type(text) is not list):
      text=text.split()
   return [word for word in text if not sw_dict[word]]

def remove_single_letters(text):
   if(type(text) is not list):
      text=text.split()
   return [word for word in text if len(word)>1]

def get_fields(text):

   temp=text.split('==references==')
   if(len(temp)<=1):
      temp=text.split('== references == ')
   text=temp
   body=re.sub(r'\{\{.*\}\}',r' ',text[0])
   body=remove_html(body)
   body=remove_links(body)
   body=remove_sc(body)
   body=body.encode("ascii", errors="ignore").decode()

   temp=text[0].split('\n')
   flag=0
   info=[]
   for line in temp:
      if re.match(r'\{\{infobox', line):
         flag=1
         info.append(re.sub(r'\{\{infobox(.*)', r'\1', line))
      elif flag==1:
         if line=='}}':
            flag=0
            continue
         info.append(line)
   info=remove_html(info)
   info=remove_links(info)
   info=remove_sc(info)
   info=info.encode("ascii", errors="ignore").decode()

   refs, links, categories= [], [], []

   if(len(text)>1):
      temp=text[1].split('\n')
      for line in temp:
         if re.search(r'<ref', line):
               refs.append(re.sub(r'.*title[\ ]*=[\ ]*([^\|]*).*', r'\1', line))
      refs=remove_html(refs)
      refs=remove_links(refs)
      refs=remove_sc(refs)
      refs=refs.encode("ascii", errors="ignore").decode()
      refs=refs.split()
      refs=[w for w in refs if w not in ['references','refer','reflist','ref']]

      temp=text[1].split('\n')
      for line in temp:
         if re.match(r'\[\[category', line):
            categories.append(re.sub(r'\[\[category:(.*)\]\]', r'\1',line))
      categories=remove_html(categories)
      categories=remove_links(categories)
      categories=remove_sc(categories)
      categories=categories.encode("ascii", errors="ignore").decode()
      categories=categories.split()

      temp=text[1].split('\n')
      for line in temp:
         if re.match(r'\*[\ ]*\[', line):
            links.append(line)
      links=remove_html(links)
      links=remove_links(links)
      links=remove_sc(links)
      links=links.encode("ascii", errors="ignore").decode()
      links=links.split()

   # return info.split(),body.split(),refs.split(),links.split(),categories.split()
   return info.split(),body.split(),refs,links,categories

def create_index_entries(id,field,words):
   global total_tokens
   global inverted_index
   total_tokens+=len(words)
   for word in words:
      word=word.strip()
      if sw_dict[word]>0 or len(word)<=1 or not word.isalnum():
         continue
      word=stemmer.stemWord(word)
      if word not in inverted_index:
         inverted_index[word]={}
      if id not in inverted_index[word]:
         inverted_index[word][id]={}
      if field not in inverted_index[word][id]:
         inverted_index[word][id][field]=1
      else:
         inverted_index[word][id][field]+=1
   

#SAX Parser
class WikipediaHandler(xml.sax.ContentHandler):
   def __init__(self):
      self.currentTag=""
      self.docId=0
      self.title=""
      self.text=""
   def startElement(self, tag, attributes):
      self.currentTag=tag
   def characters(self,content):
      if self.currentTag=="title":
         self.title+=content
      if self.currentTag=="text":
         self.text+=content
   def endElement(self, tag):
      global idtotitle
      if tag=="page":
         self.docId+=1
         df=process(self)
         idtotitle[self.docId]=str(df)+":"+self.title.strip()
         self.title=""
         self.text=""

def process_title(title, docId):
   title=remove_html(title.lower())
   title=remove_links(title)
   title=remove_sc(title)
   title=title.encode("ascii", errors="ignore").decode()
   create_index_entries(docId,'t',title.split())

def process_content(content,docId):
   info,body,refs,links,categories=get_fields(content.lower())
   create_index_entries(docId,'i',info)
   create_index_entries(docId,'b',body)
   create_index_entries(docId,'r',refs)
   create_index_entries(docId,'l',links)
   create_index_entries(docId,'c',categories)
   return len(info)+len(body)+len(refs)+len(links)+len(categories)

def process(elements):
   global docsParsed
   docsParsed+=1
   docId=elements.docId
   title=elements.title
   content=elements.text
   if(docId % DOCSPERINTERMEDIATE == 0 and docId>0):
      writeToIntermediateFile(str(int(docId/DOCSPERINTERMEDIATE)))
   process_title(title,docId)
   df=process_content(content,docId)
   return df

def writeToIntermediateFile(fileno):
   global inverted_index
   global lif
   lif=int(fileno)
   filename="index_files/intermediate_files/"+fileno+".txt"
   print("Writing into intermediate file ",fileno)
   try:
      f=open(filename,'x')
   except FileExistsError:
      f=open(filename,'w')
   for word,value in sorted(inverted_index.items()):
      entry=str(word)+":"
      for docID,val in value.items():
            entry += str(docID) + "-"
            for field,v in val.items():
               entry = entry + str(field) + str(v) + "|"
            entry = entry[:-1]+","
      f.write(entry[:-1]+"\n")
   f.close()
   print(len(inverted_index)," keys written")
   inverted_index.clear()

def mergeIntermediateFiles():
   intermediate_files=glob.glob("index_files/intermediate_files/*")
   nfiles=len(intermediate_files)
   fileheap=[]
   open_file_pointers={}
   current_row={}
   postings={}
   keys={}
   for i in range(nfiles):
      try:
         open_file_pointers[i]=open(intermediate_files[i],"r")
      except:
         print("file missing")
      current_row[i]=open_file_pointers[i].readline()
      keys[i],postings[i]="".join(current_row[i].strip().split(":")[:-1]),current_row[i].strip().split(":")[-1]
      if keys[i] not in fileheap:
         heappush(fileheap,keys[i])
   global total_keys
   inverted_index={}
   count=nfiles
   isParsed=defaultdict(int)
   current_letter='a'
   while count>0:
      key=heappop(fileheap)
      if key[0]>current_letter:
         writeToIndex(inverted_index,current_letter)
         current_letter=key[0]
         total_keys+=len(inverted_index)
         inverted_index.clear()
      for i in range(nfiles):
         if isParsed[i]:
            continue
         if keys[i]==key:
            if key in inverted_index:
               inverted_index[key]+=","+postings[i]
            else:
               inverted_index[key]=postings[i]
            current_row[i]=open_file_pointers[i].readline().strip()

            if not current_row[i]:
               open_file_pointers[i].close()
               # if  os.path.exists(intermediate_files[i]):
               #    os.remove(intermediate_files[i])
               isParsed[i]=1
               count-=1
            else:
               keys[i],postings[i]="".join(current_row[i].strip().split(":")[:-1]),current_row[i].strip().split(":")[-1]
               if keys[i] not in fileheap:
                  heappush(fileheap,keys[i])
   writeToIndex(inverted_index,current_letter)
   inverted_index.clear()



def writeToIndex(inverted_index,filename):
   global key_offset
   filename="index_files/"+filename+".txt"
   try:
      fp=open(filename,"x")
   except FileExistsError:
      fp=open(filename,"w")
   for key in sorted(inverted_index):
      key_offset[key]=fp.tell()
      fp.write(str(key)+":"+inverted_index[key]+"\n")
   fp.close()
   print(filename,"keys written")

def writeDocIdToTitle(dic):
   try:
      os.mkdir("index_files/id_to_title")
   except FileExistsError:
      pass
   last=len(dic)
   temp={}
   filename=0
   for id,title in dic.items():
      if int(int(id)/200000)==filename:
         temp[id]=title
      else:
         print(id)
         fname="index_files/id_to_title/"+str(filename)+".json"
         f=open(fname,"w")
         json.dump(temp,f)
         f.close()
         temp.clear()
         temp[id]=title
         filename+=1
      if int(id)==last:
         print(id)
         fname="index_files/id_to_title/"+str(filename)+".json"
         f=open(fname,"w")
         json.dump(temp,f)
         f.close()
         temp.clear()
   dic.clear()

def writeOffsets(off):
   try:
      os.mkdir("index_files/offsets")
   except FileExistsError:
      pass
   temp={}
   filename='a'
   for key,value in off.items():
      if key[0]==filename:
         temp[key]=value
      else:
         f=open('index_files/offsets/'+filename+'.json','w')
         json.dump(temp,f)
         f.close()
         temp.clear()
         filename=chr(ord(filename)+1)
         temp[key]=value
   f=open('index_files/offsets/'+filename+'.json','w')
   json.dump(temp,f)
   f.close()
   temp.clear()

#######################################################


# wikidump_path="data"
# try:
#    os.mkdir('index_files')
# except FileExistsError:
#    pass
# try:
#    os.mkdir('index_files/intermediate_files')
# except FileExistsError:
#    pass
# print("Parsing Started")
start_time=timeit.default_timer()
# parser=xml.sax.make_parser()
# parser.setFeature(xml.sax.handler.feature_namespaces, 0)
# handler=WikipediaHandler()
# parser.setContentHandler(handler)
# parser.parse(wikidump_path)
# if(len(inverted_index)>0):
#    lif+=1
#    writeToIntermediateFile(str(lif))
# print("Parsing Ended. Intermediate files created.")
# writeDocIdToTitle(idtotitle)
# idtotitle.clear()
# stop_time=timeit.default_timer()
# print("Intermediate files creation time : ",int(stop_time-start_time)/60," minutes")
# start_time=timeit.default_timer()
print("Merging intermediate files")
mergeIntermediateFiles()
print("Merging done")
writeOffsets(key_offset)
try:
   f=open('index_files/stat.txt','x')
except:
   f=open('index_files/stat.txt','w')
f.write(str(total_tokens)+"\n")
f.write(str(total_keys))
f.close()
stop_time=timeit.default_timer()
print("merging time : ",int(stop_time-start_time)/60," minutes")