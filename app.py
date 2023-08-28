from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from .logic import logic, location_logic
from .music_recognition import get_human_readable_db, upload_to_db_protected, delete_id_from_db_protected_for_web

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
    data = request.get_json()
    track_path = data.get("track_path")
    title = data.get("title")
    artist = data.get("artist")
    album = data.get("album")
    
    if not all([track_path, title, artist]):
        return jsonify(error="Missing required parameters."), 400

    try:
        upload_to_db_protected(user_full_track=track_path, title=title, artist=artist, album=album)
        return jsonify(message="Song uploaded successfully.")
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/delete_song', methods=['POST'])
def delete_song():
    data = request.get_json()  # Retrieve data from the request body

    # Check if the 'id' parameter exists in the request body
    file_id = data.get("id")
    if not file_id:
        return jsonify(error="Missing 'id' parameter in the request body."), 400

    try:
        delete_id_from_db_protected_for_web(file_id)
        return jsonify(message="Song deleted successfully.")
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/location_songs', methods=['POST'])
def get_location_songs():
    data = request.get_json()  # Retrieve data from the request body
    location = data.get('location')
    start_day, start_month, start_year = data.get('date').split('-')
    if not all([start_day, start_month, start_year]):
        return jsonify(error="Missing a date parameter ('start_day'/'start_month'/'start_year')."), 400
    try:
        recognized_songs_links = location_logic(location=location,
                                                day=int(start_day), month=int(start_month), year=int(start_year))
        return jsonify(recognized_songs_links)
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':
    app.run()
