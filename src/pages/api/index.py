import os
import asyncio
import requests
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
import logging

logging.basicConfig(level=logging.DEBUG)

OPENAI_API_KEY = ""
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

app = Flask(__name__)


class CustomLLM(LLM):
    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        request_data = {
            "model": "gpt-4o",  # or whichever model you prefer
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
        response = requests.post(
            OPENAI_API_URL, headers=headers, json=request_data)
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Received response from OpenAI API: {data}")
            return data['choices'][0]['message']['content']
        else:
            logging.error(f"Error: {response.status_code} - {response.text}")
            raise ValueError(
                f"Error: {response.status_code} - {response.text}")

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
        chunk_size=2000, chunk_overlap=200)
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


async def process_prompt(file_path, file_type, prompt):
    docs = process_file(file_path, file_type)
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en")
    search_engine = create_search_engine(docs=docs, embeddings=embeddings)

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
    return jsonify({
        "answer": "Sumit Nalavade is a Computer Engineering student at Texas A&M University, College Station, expected to graduate in May 2026 with a GPA of 3.88. He has experience as a Software Engineering Intern at Humana, where he collaborated on developing provider-facing applications using tools like Palantir Foundry, Azure Synapse, and Databricks. He also worked as a Full Stack Software Engineer at Texas A&M University Health Science Center, contributing to a project called OliviaHealth aimed at enhancing maternal and familial care. His technical skills include React.js, TypeScript, Python, Flask, SQLAlchemy, and various other technologies. Additionally, he has served as an Undergraduate Teaching Assistant, a Front End Developer at Crypt Cloud, and has led multiple notable projects such as Maroon Rides and Gradual Grades. Sumit has also held leadership positions in the Aggie Coding Club and the Texas A&M Computing Society.\n\n",
        "sources": "Page 1, Page 2, Page 3"
    })

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    prompt = request.form.get('prompt', '')
    file_type = file.content_type
    file_path = os.path.join("/tmp", file.filename)
    file.save(file_path)

    try:
        result = asyncio.run(process_prompt(file_path, file_type, prompt))
        return jsonify(result), 200
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    finally:
        os.remove(file_path)


if __name__ == '__main__':
    app.run(port=5328)
