from lefci import app, api


@app.route('/')
def index():
    return app.send_static_file('index.html')
