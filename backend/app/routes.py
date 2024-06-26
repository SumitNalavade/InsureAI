# backend/app/routes.py
from flask import Blueprint

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return "Hello, Flask from routes.py!"
