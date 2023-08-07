from flask import Flask, jsonify, request, abort
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
    username = request.args.get("username")
    if not username:
        return jsonify(error="Missing 'username' parameter."), 400

    try:
        data = logic(username)
        return jsonify(data)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/database_songs', methods=['GET'])
def get_database_songs():
    db = get_human_readable_db()
    return jsonify(db)


@app.route('/api/upload_song', methods=['POST'])
def upload_song():
    try:
        audio_file = request.files.get("file")
        title = request.form.get("title")
        artist = request.form.get("artist")
        album = request.form.get("album")
        
        if not audio_file:
            return jsonify(error="file field is required."), 400

        upload_to_db(audio_file=audio_file, title=title, artist=artist, album=album)

        return jsonify(message="Song uploaded successfully.")
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/delete_song', methods=['POST'])
def delete_song():
    data = request.get_json()  # Retrieve data from the request body

    # Check if the 'title' parameter exists in the request body
    title = data.get("title")
    if not title:
        return jsonify(error="Missing 'title' parameter in the request body."), 400

    try:
        delete_from_db(title)
        return jsonify(message="Song deleted successfully.")
    except Exception as e:
        return jsonify(error=str(e)), 500



if __name__ == '__main__':
    app.run()
