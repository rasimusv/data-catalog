import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import configparser

config = configparser.ConfigParser()
config.optionxform = str

app = Flask(__name__)

path = os.environ.get('CONFIG_PATH') if os.environ.get('CONFIG_PATH') else "./settings.ini"
config.read(path)
try:
    app.config.update(dict(
        SECRET_KEY=str(config['FLASK_APP']['FLASK_APP_SECRET_KEY']),
        SQLALCHEMY_DATABASE_URI=str(config['SQLALCHEMY']['SQLALCHEMY_DATABASE_URL']),
        SQLALCHEMY_TRACK_MODIFICATIONS=bool(config['SQLALCHEMY']['SQLALCHEMY_DATABASE_URL'])
    ))
    print(f"\n\033[32m Сервер запустился с конфигом:\n\033[32m {path}\n")
except KeyError:
    print(f"\033[31m Файл {path} не найден или неверный")

db = SQLAlchemy(app)
from app.routes import route
route(app)
