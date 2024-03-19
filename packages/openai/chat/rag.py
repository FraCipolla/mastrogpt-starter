#--param OPENAI_API_KEY $OPENAI_API_KEY

import pickle
from langchain_community.document_loaders import WebBaseLoader

# Use a markdown file from github page
loader = WebBaseLoader("https://appfront-operations.gitbook.io/lookinglass-manuale-utente/preventivi")

docs = loader.load()
print(docs[0].page_content[:500])

from langchain.text_splitter import RecursiveCharacterTextSplitter

chunk_size =100
chunk_overlap = 20

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    length_function=len,
)

#Create a split of the document using the text splitter
splits = text_splitter.split_documents(docs)
print(splits[0])
print(splits[1])

import os
from langchain.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.vectorstores.faiss import FAISS

embedding = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])

vectorstore = FAISS.from_texts(splits, embedding)