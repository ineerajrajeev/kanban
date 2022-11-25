from flask import *
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import uuid
from uuid import uuid4
import jwt
from flask_restful import *
from flask_cors import CORS
import requests
from werkzeug.security import *
import datetime
from flask_session import *
from itsdangerous import *
import pdfkit
import io
from weasyprint import *
import csv
from jinja2 import *
from celery import Celery

app = Flask(__name__, static_url_path='/static')
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = "thisissupersecretkey"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/1'
api = Api(
    app
)

Session(app)
app.app_context().push()
db = SQLAlchemy(app)
db.init_app(app)

