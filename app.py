# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from .logic import logic

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/api/data', methods=['GET'])
def get_data():
    # Your main function logic goes here
    data = [{'message': 'Hello from Python backend!'}]
    return jsonify(data)


@app.route('/api/songs', methods=['GET'])
@cross_origin()
def get_songs():
    print("\n\n\nHello World")
    args = request.args
    username = args.get("username")
    data = logic(username)
    print(data)
    return data


if __name__ == '__main__':
    app.run()
