# main.py

import requests
from typing import Any, Dict, List, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain, RetrievalQAWithSourcesChain
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain.document_loaders import PDFPlumberLoader
import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.vectorstores.base import VectorStore
from langchain_core.language_models.llms import LLM
import logging

logging.basicConfig(level=logging.DEBUG)

class CustomLLM(LLM):
    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> str:
        url = 'https://striderai.azurewebsites.net/api/Strider/AskStrider'
        request = {"user": "sahil :)", "message": prompt}
        logging.debug(f"Sending request to API: {request}")
        response = requests.post(url, json=request)
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Received response from API: {data}")
            return data['response']
        else:
            logging.error(f"Error: {response.status_code}")
            raise ValueError(f"Error: {response.status_code}")

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": "Strider"}

    @property
    def _llm_type(self) -> str:
        return "custom"

def process_file(file_path, file_type) -> List[Document]:
    if file_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        raise TypeError("Only PDF and Excel files are supported")

    loader = PDFPlumberLoader(file_path) if file_type == "application/pdf" else UnstructuredExcelLoader(file_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100000000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    for i, doc in enumerate(docs):
        doc.metadata["source"] = f"source_{i}"

    if not docs:
        raise ValueError("File parsing failed.")
    return docs

def create_search_engine(docs: List[Document], embeddings) -> VectorStore:
    client_settings = Settings(
        allow_reset=True,
        anonymized_telemetry=False
    )

    search_engine = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        client_settings=client_settings
    )
    return search_engine
