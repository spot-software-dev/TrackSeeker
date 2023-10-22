from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_mail import Mail, Message
from config import Config
from logic import location_logic
from music_recognition import get_human_readable_db, upload_to_db_protected, delete_id_from_db_protected_for_web
from drive_logic import Drive
app = Flask(__name__)

app.config.from_object(Config)

mail = Mail(app)
cors = CORS(app)


drive = Drive()


@app.route('/api/data', methods=['GET'])
def get_data():
    # Your main function logic goes here
    data = [{'message': 'Hello from Python backend!'}]
    return jsonify(data)


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
    """
    Expose searching recognized location songs.

    data expected in JSON:
        location (str): Name of location
        date (str): Date of uploaded story to Spot-Stories Google Drive Database
            to start searching. Format: "DD-MM-YYYY"
        end_date (str) - optional: Date of uploaded story to Spot-Stories Google Drive Database
            to finish searching. Defaults to date JSON parameter. Format: "DD-MM-YYYY".
    """

    data = request.get_json()  # Retrieve data from the request body
    location = data.get('location')
    start_day, start_month, start_year = data.get('date').split('-')
    end_day, end_month, end_year = data.get('end_date', f"{start_day}-{start_month}-{start_year}").split('-')

    if not all([start_day, start_month, start_year]):
        return jsonify(error="Missing a date parameter ('start_day'/'start_month'/'start_year')."), 400

    try:
        recognized_songs_links = location_logic(location=location,
                                                day=int(start_day), month=int(start_month), year=int(start_year),
                                                end_day=int(end_day), end_month=int(end_month), end_year=int(end_year))
        return jsonify(recognized_songs_links)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/locations', methods=['GET'])
def get_locations():
    try:
        locations_and_dates = drive.get_locations_and_dates(locations_dir_id=drive.SPOT_LOCATIONS_DIR_ID)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(locations_and_dates)


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


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
