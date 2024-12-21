import os
import nbformat
from nbconvert import MarkdownExporter
from langchain.retrievers.merger_retriever import MergerRetriever

import re
from bs4 import BeautifulSoup, SoupStrainer
import bs4
import asyncio
from langchain_text_splitters import HTMLHeaderTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PythonLoader
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from common import commented_code


def context_or_tools_web_docs():
    path = "./chroma_db/document"
    if os.path.exists(path):
        print("---LOCAL VECTOR STORE LOADED---")
        vectorstore = Chroma(persist_directory=path, embedding_function=OpenAIEmbeddings())
    else:
        print("---CREATING NEW VECTOR STORE---")
        pages = ['tsp', 'vrp', 'cvrp', 'pickup_delivery', 'vrptw', 'cvrptw_resources', 'dimensions', 'penalties',
                 'routing_tasks']
        urls = ["https://developers.google.com/optimization/routing/" + i for i in pages]
        loader = WebBaseLoader(
            web_paths=urls,
        )
        docs = asyncio.run(loader.fetch_all(urls))
        strainer = SoupStrainer(class_="devsite-article")

        headers_to_split_on = [
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        documents = []
        html_splitter = HTMLHeaderTextSplitter(headers_to_split_on)
        for doc in docs:
            soup = BeautifulSoup(doc, 'html.parser', parse_only=strainer)

            for section in soup.find_all('section'):
                if section.find('h3') and 'C++' in section.find('h3').get_text():
                    section.decompose()
                elif section.find('h3') and 'C#' in section.find('h3').get_text():
                    section.decompose()
                elif section.find('h3') and 'Java' in section.find('h3').get_text():
                    section.decompose()
            html_header_splits = html_splitter.split_text(str(soup))
            for v in html_header_splits:
                documents.append(v)
        vectorstore = Chroma.from_documents(documents=documents, embedding=OpenAIEmbeddings(), persist_directory=path)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    return retriever

def context_or_tools_mds():
    path = "./chroma_db/example"
    if os.path.exists(path):
        print("---LOCAL VECTOR STORE LOADED---")
        vectorstore = Chroma(persist_directory=path, embedding_function=OpenAIEmbeddings())
    else:
        print("---CREATING NEW VECTOR STORE---")
        loader_code = DirectoryLoader("./data/OR-tools/python/", glob="**/*.py", loader_cls=PythonLoader, show_progress=True)
        codes = loader_code.load()
        vectorstore = Chroma.from_documents(documents=codes, embedding=OpenAIEmbeddings(), persist_directory=path)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    return retriever


def context_or_tools_codes():
    path = "./chroma_db/code"
    if os.path.exists(path):
        print("---LOCAL VECTOR STORE LOADED---")
        vectorstore = Chroma(persist_directory=path, embedding_function=OpenAIEmbeddings())
    else:
        print("---CREATING NEW VECTOR STORE---")
        loader_code = DirectoryLoader("./data/OR-tools/mds/", glob="**/*.md", loader_cls=TextLoader, show_progress=True)
        content = loader_code.load()
        vectorstore = Chroma.from_documents(documents=content, embedding=OpenAIEmbeddings(), persist_directory=path)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    return retriever


def context_gurobi_codes():
    path = "./chroma_db/gurobi"
    if os.path.exists(path):
        print("---LOCAL VECTOR STORE LOADED---")
        vectorstore = Chroma(persist_directory=path, embedding_function=OpenAIEmbeddings())
    else:
        print("---CREATING NEW VECTOR STORE---")
        loader_code = DirectoryLoader("./data/Gurobi/", glob="**/*.py", loader_cls=TextLoader, show_progress=True)
        content = loader_code.load()
        vectorstore = Chroma.from_documents(documents=content, embedding=OpenAIEmbeddings(), persist_directory=path)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    return retriever


def context_mds_bm25():
    loader_code = DirectoryLoader("./data/OR-tools/mds/", glob="**/*.md", loader_cls=TextLoader, show_progress=True)
    content = loader_code.load()
    retriever = BM25Retriever.from_documents(content)
    return retriever


def context_all():
    retriever_doc = context_or_tools_web_docs()
    retriever_mds = context_or_tools_mds()
    retriever_code = context_or_tools_codes()
    merge_retriever = MergerRetriever(retrievers=[retriever_doc, retriever_code, retriever_mds])
    return merge_retriever


def context_merged():
    db1 = Chroma(
    persist_directory="./chroma_db/code",
    embedding_function=OpenAIEmbeddings(),
)

    db2 = Chroma(
    persist_directory="./chroma_db/document",
    embedding_function=OpenAIEmbeddings(),
)
    db3 = Chroma(
    persist_directory="./chroma_db/example",
    embedding_function=OpenAIEmbeddings(),
)

    db2_data = db2._collection.get(include=['documents', 'metadatas', 'embeddings'])
    db1._collection.add(
        embeddings=db2_data['embeddings'],
        metadatas=db2_data['metadatas'],
        documents=db2_data['documents'],
        ids=db2_data['ids']
    )

    db3_data = db3._collection.get(include=['documents', 'metadatas', 'embeddings'])
    db1._collection.add(
        embeddings=db3_data['embeddings'],
        metadatas=db3_data['metadatas'],
        documents=db3_data['documents'],
        ids=db3_data['ids']
    )
    retriever = db1.as_retriever(search_kwargs={"k": 3})
    return retriever

def convert_ipynb_to_md(notebook_path, output_path):
    # Load the notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    # Initialize the Markdown exporter
    md_exporter = MarkdownExporter()

    # Convert the notebook to markdown
    (body, resources) = md_exporter.from_notebook_node(nb)

    # Write the markdown file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(body)


def convert_all_notebooks(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for notebook_filename in os.listdir(input_dir):
        if notebook_filename.endswith('.ipynb'):
            notebook_path = os.path.join(input_dir, notebook_filename)
            output_path = os.path.join(output_dir, notebook_filename.replace('.ipynb', '.md'))
            convert_ipynb_to_md(notebook_path, output_path)
            print(f"Converted {notebook_filename} to Markdown.")




def commenter(input, llm):
    prompt_template_gen = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert in Python programming for operations research. Now I give you a code snippet, and you need to add necessary comments to it."""
            ),
            ("user",
             """
         This is the code snippet:
         
{snippet}

Please directly return the commented code snippet and do not change the code and generate other things.
"""
             ),
            ("placeholder", "{messages}")
        ]
    )
    if llm.startswith("gpt"):
        llm = ChatOpenAI(model=llm, temperature=0.0, verbose=True)
    elif llm.startswith("claude"):
        llm = ChatAnthropic(model=llm,
                            temperature=0.0, max_tokens=5000)
    else:
        raise NotImplementedError
    chain = prompt_template_gen | llm.with_structured_output(commented_code)
    result = chain.invoke(input)
    return result


def write_code_to_file(problem, imports, code, llm):
    file_path = f"./data/OR-tools/gene_codes/{problem}.py"
    code_string = "# " + problem + "\n" + imports + "\n" + code
    new_code_string = commenter(code_string, llm).code
    with open(file_path, "w") as file:
        file.write(new_code_string)


def context_gene_codes():
    path = "./chroma_db/gene_codes"
    if os.path.exists(path):
        print("---LOCAL VECTOR STORE LOADED---")
        vectorstore = Chroma(persist_directory=path, embedding_function=OpenAIEmbeddings())
    else:
        print("---CREATING NEW VECTOR STORE---")
        loader_code = DirectoryLoader("./data/OR-tools/gene_codes", glob="**/*.py", loader_cls=TextLoader, show_progress=True)
        content = loader_code.load()
        vectorstore = Chroma.from_documents(documents=content, embedding=OpenAIEmbeddings(), persist_directory=path)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    return retriever


def merge_retriever():
    retriever_gene = context_gene_codes()
    retriever_code = context_or_tools_codes()
    merge_retriever = EnsembleRetriever(retrievers=[retriever_gene, retriever_code], weights=[0.5, 0.5])
    return merge_retriever

def context_assign():
    path = "./chroma_db/assignment"
    if os.path.exists(path):
        print("---LOCAL VECTOR STORE LOADED---")
        vectorstore = Chroma(persist_directory=path, embedding_function=OpenAIEmbeddings())
    else:
        print("---CREATING NEW VECTOR STORE---")
        loader_code = DirectoryLoader("./data/OR-tools/assignment/", glob="**/*.py", loader_cls=TextLoader, show_progress=True)
        content = loader_code.load()
        vectorstore = Chroma.from_documents(documents=content, embedding=OpenAIEmbeddings(), persist_directory=path)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    return retriever

def context_location():
    path = "./chroma_db/location"
    if os.path.exists(path):
        print("---LOCAL VECTOR STORE LOADED---")
        vectorstore = Chroma(persist_directory=path, embedding_function=OpenAIEmbeddings())
    else:
        print("---CREATING NEW VECTOR STORE---")
        loader_code = DirectoryLoader("./data/Gurobi/flp/", glob="**/*.py", loader_cls=TextLoader, show_progress=True)
        content = loader_code.load()
        vectorstore = Chroma.from_documents(documents=content, embedding=OpenAIEmbeddings(), persist_directory=path)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    return retriever

if __name__ == "__main__":
    # ret = context_gene_codes()
    ret = context_location()
    aa = ret.invoke(" Python code of p-Median")
