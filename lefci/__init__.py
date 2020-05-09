from flask import Flask

app = Flask(__name__, static_folder="../frontend/dist", static_url_path='/')

from lefci import routes