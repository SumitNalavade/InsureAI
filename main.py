import chainlit as cl
import os
import langchain
import requests
import unstructured
from langchain_core.language_models.llms import LLM
from typing import Any, Dict, Iterator, List, Mapping, Optional
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import GenerationChunk
from chainlit.types import AskFileResponse
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document, StrOutputParser
from langchain.chains import LLMChain, RetrievalQAWithSourcesChain
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain.document_loaders import PDFPlumberLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tempfile import NamedTemporaryFile
from typing import List
from chainlit.types import AskFileResponse
import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.vectorstores.base import VectorStore
from langchain.schema.embeddings import Embeddings
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
#from langsmith import traceable
import logging

logging.basicConfig(level=logging.DEBUG)


AZURE_OPENAI_API_KEY = "8562072bb6dc4088aaeb5e7495a5ace3"
AZURE_OPENAI_ENDPOINT = "https://mlp-npe-hackathon-openai.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME = "mlp-genai-npe-gpt-4o-hackathon2024-7"

# Construct the endpoint URL
AZURE_OPENAI_COMPLETION_URL = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version=2024-02-01"


#Stider as a Custom LLM
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

    # def _stream(
    #         self,
    #         prompt: str,
    #         stop: Optional[List[str]] = None,
    #         run_manager: Optional[CallbackManagerForLLMRun] = None,
    #         **kwargs: Any,
    # ) -> Iterator[GenerationChunk]:
    #     for char in prompt[: self.n]:
    #         chunk = GenerationChunk(text=char)
    #         if run_manager:
    #             run_manager.on_llm_new_token(chunk.text, chunk=chunk)
    #
    #         yield chunk

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": "Strider",
        }

    @property
    def _llm_type(self) -> str:
        return "custom"


#Chainlit
def process_file(*, file: AskFileResponse) -> List[Document]:
    print("PROCESS START")

    # We only support PDF as input.
    if file.type != "application/pdf" and file.type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        raise TypeError("Only PDF and Excel files are supported")

    with NamedTemporaryFile() as tempfile:
        #tempfile.write(file)

        loader = None
        print("LOADER START")
        if file.type == "application/pdf":
            loader = PDFPlumberLoader(file.path)
        else:
            loader = UnstructuredExcelLoader(file.path)
        documents = loader.load()
        print("LOADED")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100000000,
            chunk_overlap=100
        )
        docs = text_splitter.split_documents(documents)
        print("SPLIT")
        # We are adding source_id into the metadata here to denote which
        # source document it is.
        for i, doc in enumerate(docs):
            doc.metadata["source"] = f"source_{i}"

        if not docs:
            raise ValueError("PDF file parsing failed.")
        #print(f"DOCS:{docs}")
        print("RETURN")
        return docs

def create_search_engine(*, docs: List[Document], embeddings: Embeddings) -> VectorStore:

    client = chromadb.PersistentClient(path="C:\\Users\\SKS3298\\OneDrive - Humana\\Desktop\\miniDB")
    client_settings=Settings(
        allow_reset=True,
        anonymized_telemetry=False
    )

    search_engine = Chroma(
        client=client,
        client_settings=client_settings
    )

    #search_engine._client.reset()
    search_engine = Chroma.from_documents(
        client=client,
        documents=docs,
        embedding=embeddings,
        client_settings=client_settings
    )
    return search_engine

@cl.on_chat_start
async def on_chat_start():
    # docs = None
    # for i in range(1):
    #     files = None
    #     while files is None:
    #         files = await cl.AskFileMessage(
    #             content="Please upload the file you want to ask questions against",
    #             accept=['application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    #             max_size_mb=20,
    #             max_files=2
    #         ).send()
    #     file = files[0]
    #     msg = cl.Message(content=f"Processing `{file.name}`...")
    #     await msg.send()
    #     if docs == None:
    #         docs = process_file(file=file)
    #     else:
    #         docs += process_file(file=file)
    #     print("FILE PROCESSED")
    # 
    #     #docs = process_file(file=file)
    #     cl.user_session.set("docs", docs)
    #     msg.content = f"`{file.name}` processed. Loading ..."
    #     await msg.update()
    #     os.environ["ALLOW_RESET"] = "True"
    #     #embeddings = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    #     #embeddings = GPT2TokenizerFast.from_pretrained('Xenova/text-embedding-ada-002')
    #     #embeddings = gensim.downloader.load('glove-twitter-25')
    #     #embeddings = TogetherEmbeddings(model="togethercomputer/m2-bert-80M-8k-retrieval")
    #     #embeddings = TensorflowHubEmbeddings()
    #     embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en")
    #     #embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    #     print("EMBEDDING")
    #     try:
    #         print("BEFORE SEARCH START")
    #         search_engine = await cl.make_async(create_search_engine)(
    #             docs=docs, embeddings=embeddings
    #         )
    #         print("SEARCH ENGINE")
    #     except Exception as e:
    #         await cl.Message(content=f"Error: {e}").send()
    #         raise SystemError
    #     msg.content = f"`{file.name}` loaded. You can now ask questions!"
    #     await msg.update()

    model = CustomLLM()
    # prompt = ChatPromptTemplate.from_messages(
    #     [
    #         (
    #             "system",
    #             "End every message with the phrase 'over'"
    #         ),
    #         (
    #             "human",
    #             "{question}"
    #         )
    #     ]
    # )
    #search_engine = chromadb.PersistentClient(path="C:\\Users\\SKS3298\\OneDrive - Humana\\Desktop\\miniDB")
    try:
        print("BEFORE SEARCH START")
        embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en")
        search_engine = await cl.make_async(create_search_engine)(
            docs=[], embeddings=embeddings
        )
        print("SEARCH ENGINE")
    except Exception as e:
        await cl.Message(content=f"Error: {e}").send()
        raise SystemError
    chain= RetrievalQAWithSourcesChain.from_chain_type(
        llm = model,
        chain_type = 'stuff',
        retriever = search_engine.as_retriever(max_token_limit=30000),
    )
    cl.user_session.set("chain", chain)

@cl.on_message
async def main(message: cl.Message):

    # Let's load the chain from user_session
    chain = cl.user_session.get("chain")  # type: RetrievalQAWithSourcesChain

    response = await chain.acall(
        message.content,
        callbacks=[cl.AsyncLangchainCallbackHandler(stream_final_answer=True)]
    )
    #print(f"RESPONSE: {response.response_metadata}")
    #print(f"RESPONSE:{response}")
    answer = response["answer"]
    sources = response["sources"].strip()

    # Get all of the documents from user session
    docs = cl.user_session.get("docs")
    metadatas = [doc.metadata for doc in docs]
    all_sources = [m["source"] for m in metadatas]

    # Adding sources to the answer
    source_elements = []
    if sources:
        found_sources = []

        # Add the sources to the message
        for source in sources.split(","):
            source_name = source.strip().replace(".", "")
            # Get the index of the source
            try:
                index = all_sources.index(source_name)
            except ValueError:
                continue
            text = docs[index].page_content
            found_sources.append(source_name)
            # Create the text element referenced in the message
            source_elements.append(cl.Text(content=text, name=source_name))

        if found_sources:
            answer += f"\nSources: {', '.join(found_sources)}"
        else:
            answer += "\nNo sources found"
    print(f"SOURCES: {source_elements}")
    await cl.Message(content=answer, elements=source_elements).send()

@cl.on_stop
def on_stop():
    print("The user wants to stop the task!")

@cl.on_chat_end
def on_chat_end():
    print("The user disconnected!")