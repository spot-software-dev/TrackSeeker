import time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS, cross_origin
from flask_mail import Mail, Message
from .config import Config
from .logic import logic, location_logic
from .music_recognition import get_human_readable_db, upload_to_db_protected, delete_id_from_db_protected_for_web
from .story_story_logic import StoryStorySession

app = Flask(__name__)

app.config.from_object(Config)

mail = Mail(app)
cors = CORS(app)

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
    audio_file = request.files.get("file")
    title = request.form.get("title")
    artist = request.form.get("artist")
    album = request.form.get("album")
    
    if not all([audio_file, title, artist]):
        return jsonify(error="Missing required parameters."), 400

    try:
        upload_to_db_protected(audio_file=audio_file, title=title, artist=artist, album=album)
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


@app.route('/api/locations', methods=['POST'])
def get_locations():
    data = request.get_json()
    dashboard = data.get('dashboard')
    try:
        storystory_session = StoryStorySession()
        time.sleep(0.5)
        locations = storystory_session.get_instagram_followed_locations_and_dates(dashboard_name=dashboard)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(locations)


@app.route('/api/send_location_email', methods=['POST'])
def send_email():
    data = request.get_json()
    recipients = data.get('recipients')
    subject = f"New Location Request! from {data.get('fullname')}"
    message_body = render_template('email_template.html', subject=subject, fullname=data.get('fullname'), email=data.get('email'), locationWanted=data.get('locationWanted'))
    
    if not recipients or not isinstance(recipients, list):
        return jsonify(error="Invalid recipients data, should send an array."), 400

    msg = Message(subject=subject, recipients=recipients)
    msg.html = message_body

    try:
        mail.send(msg)
        return jsonify(message="Email was sent successfully!")
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':
    app.run()
