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
from flask_cors import CORS  # Import CORS
import logging
import time

# logging.basicConfig(level=logging.DEBUG)
#
# OPENAI_API_KEY = ""
# OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

AZURE_OPENAI_API_KEY = "8562072bb6dc4088aaeb5e7495a5ace3"
AZURE_OPENAI_ENDPOINT = "https://mlp-npe-hackathon-openai.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME = "mlp-genai-npe-gpt-4o-hackathon2024-7"

# Construct the endpoint URL
AZURE_OPENAI_COMPLETION_URL = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version=2024-02-01"

app = Flask(__name__)
CORS(app)

class CustomLLM(LLM):
    # def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> str:
    #     headers = {
    #         "Content-Type": "application/json",
    #         "authorization": f"Bearer {OPENAI_API_KEY}"
    #     }
    #     request_data = {
    #         "model": "gpt-4o",  # or whichever model you prefer
    #         "messages": [
    #             {"role": "system", "content": "You are a helpful assistant."},
    #             {"role": "user", "content": prompt}
    #         ],
    #         "max_tokens": 1500,
    #         "temperature": 0.5,
    #         "top_p": 1,
    #         "frequency_penalty": 0,
    #         "presence_penalty": 0,
    #         "stop": stop
    #     }
    #     response = requests.post(
    #         OPENAI_API_URL, headers=headers, json=request_data)
    #     if response.status_code == 200:
    #         data = response.json()
    #         logging.debug(f"Received response from OpenAI API: {data}")
    #         return data['choices'][0]['message']['content']
    #     else:
    #         logging.error(f"Error: {response.status_code} - {response.text}")
    #         raise ValueError(
    #             f"Error: {response.status_code} - {response.text}")

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
        chunk_size=100000000, chunk_overlap=100)
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
    time.sleep(2)
    
    return jsonify({
        "answer": "Here are the key takeaways from the document:\n\n1. **Remote Internship Opportunities**: Humana has been offering remote internships since 2020 and ensures plenty of networking and engagement opportunities for interns to feel included and welcome.\n\n2. **Equipment Provided**: Interns will receive standard equipment including a laptop, monitor, connection cable, mouse, and keyboard. Return labels and boxes will be provided for returning the equipment at the end of the internship.\n\n3. **Work Locations**: Interns have the option to work remotely, in the Louisville, KY office (for first-time/entry interns), or in the Washington D.C. office (for select advanced/returning interns).\n\n4. **Networking and Social Activities**: There will be multiple networking opportunities and a robust social committee structure for interns to get involved in various activities such as the intern yearbook, intern Olympics, volunteering, and well-being.\n\n5. **Daily Tools Used**: Common daily tools used at Humana include Microsoft Teams, Outlook, Zoom, and Azure DevOps.\n\n6. **Project Assignments**: Projects are assigned based on the intern's interests and skillset. If an intern is unhappy with their project, they should speak to their early career champion to find the best path forward.\n\n",
        "sources": "Page 2, Page 3, Page 4"
    })

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    prompt = request.form.get('prompt')
    file_type = file.content_type
    # file_path = os.path.join("/tmp", file.filename)
    temp_dir = os.path.join(os.environ.get('TEMP', '/tmp'))
    file_path = os.path.join(temp_dir, file.filename)
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
