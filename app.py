# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from .logic import logic
from .music_recognition import get_human_readable_db, upload_to_db, delete_from_db

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
    args = request.args
    username = args.get("username")
    data = logic(username)
    print(data)
    return data


@app.route('/api/database_songs')
def get_database_songs():
    db = get_human_readable_db()
    return db


@app.route('/api/upload_song')
def upload_song():
    args = request.args
    track_path = args.get("track_path")
    title = args.get("title")
    artist = args.get("artist")
    album = args.get("album")
    upload_to_db(user_full_track=track_path, title=title, artist=artist, album=album)
    return


@app.route('/api/delete_song')
def delete_song():
    args = request.args
    title = args.get("title")
    delete_from_db(title)


if __name__ == '__main__':
    app.run()
