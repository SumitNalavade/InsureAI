import os
import asyncio
import requests
import logging
from typing import Any, Dict, List, Optional
from flask import Flask, request, jsonify
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
from flask_cors import CORS

logging.basicConfig(level=logging.DEBUG)

AZURE_OPENAI_API_KEY = "8562072bb6dc4088aaeb5e7495a5ace3"
AZURE_OPENAI_ENDPOINT = "https://mlp-npe-hackathon-openai.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME = "mlp-genai-npe-gpt-4o-hackathon2024-7"

AZURE_OPENAI_COMPLETION_URL = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version=2024-02-01"

# Global dictionary to hold the vector stores
vector_stores = {}

app = Flask(__name__)
CORS(app)

class CustomLLM(LLM):
    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[Any] = None,
              **kwargs: Any) -> str:
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
        logging.debug(f"Request Data: {request_data}")
        response = requests.post(AZURE_OPENAI_COMPLETION_URL, headers=headers, json=request_data)
        logging.debug(f"Response Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Received response from Azure OpenAI API: {data}")
            return data['choices'][0]['message']['content']
        else:
            logging.error(f"Error: {response.status_code} - {response.text}")
            raise ValueError(f"Error: {response.status_code} - {response.text}")

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": "OpenAI"}

    @property
    def _llm_type(self) -> str:
        return "openai"

def process_file(file_path, file_type) -> List[Document]:
    if file_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        raise TypeError("Only PDF and Excel files are supported")

    loader = PDFPlumberLoader(
        file_path) if file_type == "application/pdf" else UnstructuredExcelLoader(file_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100)  # Adjusted chunk size
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

def get_vector_store(file_id: str) -> Optional[VectorStore]:
    global vector_stores
    return vector_stores.get(file_id)

def set_vector_store(file_id: str, vector_store: VectorStore):
    global vector_stores
    vector_stores[file_id] = vector_store
    logging.debug(f"Set vector store for file_id {file_id}")

async def process_prompt(file_id: str, file_path: str, file_type: str, prompt: str):
    search_engine = get_vector_store(file_id)
    logging.debug(f"Retrieved vector store for file_id {file_id}: {search_engine is not None}")

    if search_engine is None:
        docs = process_file(file_path, file_type)
        embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en")
        search_engine = create_search_engine(docs=docs, embeddings=embeddings)
        set_vector_store(file_id, search_engine)

    model = CustomLLM()
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=model,
        chain_type='stuff',
        retriever=search_engine.as_retriever(max_token_limit=30000),
    )

    response = await chain.acall(prompt)
    logging.debug(f"Chain response: {response}")
    answer = response["answer"]
    sources = response["sources"].strip()

    return {"answer": answer, "sources": sources}

@app.route('/api/process_prompt', methods=['POST'])
def process_prompt_route():
    if 'file' not in request.files:
        logging.error("No file part in the request")
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        logging.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    prompt = request.form.get('prompt')
    file_type = file.content_type
    file_id = request.form.get('file_id')
    logging.debug(f"Processing prompt for file_id {file_id}")
    temp_dir = os.path.join(os.environ.get('TMPDIR', '/tmp'))
    file_path = os.path.join(temp_dir, file.filename)
    file.save(file_path)

    try:
        result = asyncio.run(process_prompt(file_id, file_path, file_type, prompt))
        return jsonify(result), 200
    except (TypeError, ValueError) as e:
        logging.error(f"Processing error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Something went wrong. Please try again later."}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    app.run(port=5328)
