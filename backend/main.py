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

AZURE_OPENAI_API_KEY = "8562072bb6dc4088aaeb5e7495a5ace3"
AZURE_OPENAI_ENDPOINT = "https://mlp-npe-hackathon-openai.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME = "mlp-genai-npe-gpt-4o-hackathon2024-7"

# Construct the endpoint URL
AZURE_OPENAI_COMPLETION_URL = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version=2024-02-01"

print(f"Completion URL: {AZURE_OPENAI_COMPLETION_URL}")  # Debug print

class CustomLLM(LLM):
    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> str:
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        }
        request_data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.5,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": stop
        }
        print(f"Request Data: {request_data}")  # Debug print
        response = requests.post(AZURE_OPENAI_COMPLETION_URL, headers=headers, json=request_data)
        print(f"Response Status Code: {response.status_code}")  # Debug print
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Received response from Azure OpenAI API: {data}")
            return data['choices'][0]['message']['content']
        else:
            logging.error(f"Error: {response.status_code} - {response.text}")
            raise ValueError(f"Error: {response.status_code} - {response.text}")

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": "AzureOpenAI"}

    @property
    def _llm_type(self) -> str:
        return "azure_openai"

def process_file(file_path, file_type) -> List[Document]:
    if file_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        raise TypeError("Only PDF and Excel files are supported")

    loader = PDFPlumberLoader(file_path) if file_type == "application/pdf" else UnstructuredExcelLoader(file_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    for i, doc in enumerate(docs):
        doc.metadata["source"] = f"Page {doc.metadata.get('page_number', i+1)}"

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
