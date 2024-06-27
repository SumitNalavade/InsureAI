# app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from main import CustomLLM, process_file, create_search_engine
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain.chains import RetrievalQAWithSourcesChain
import asyncio
import logging

bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/', methods=['GET', 'POST'])
def home():
    result = None
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            file.save(file_path)

            prompt = request.form['prompt']

            # Process the file and prompt
            result = process_prompt(file_path, file.content_type, prompt)
            logging.debug(f"Result: {result}")

    return render_template('index.html', result=result)

def process_prompt(file_path, file_type, prompt):
    # Process the file
    docs = process_file(file_path, file_type)

    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en")
    search_engine = create_search_engine(docs=docs, embeddings=embeddings)

    model = CustomLLM()
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=model,
        chain_type='stuff',
        retriever=search_engine.as_retriever(max_token_limit=30000),
    )

    response = asyncio.run(chain.acall(prompt))
    logging.debug(f"Chain response: {response}")
    answer = response["answer"]
    sources = response["sources"].strip()

    return f"Answer: {answer}\nSources: {sources}"
