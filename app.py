from loguru import logger
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_mail import Mail, Message
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
import datetime
from werkzeug.security import check_password_hash
import traceback
from config import Config
from logic import location_logic
from music_recognition import upload_to_db_protected, delete_id_from_db_protected_for_web
from music_recognition import rescan_all_files, get_human_readable_db, MusicDuplicationError, MusicFileDoesNotExist
from drive_logic import Drive
from dbconf import db, Account, Track, Location
from db_add_remove_tools import create_track, delete_track, create_location, delete_location
from db_add_remove_tools import delete_account_followed_location, add_account_followed_location
from db_add_remove_tools import TrackExistsError, TrackNotExistsError, LocationExistsError, LocationNotExistsError
from auth import create_account, EmailExistsError
from dotenv.main import load_dotenv
load_dotenv()

app = Flask(__name__)

app.config.from_object(Config)

mail = Mail(app)
cors = CORS(app)

login_manager = LoginManager()
login_manager.init_app(app=app)

db.init_app(app)

drive = Drive()


@app.before_request
def before_request():
    args = None
    if request.method in ["POST", "DELETE"] and request.headers.get("Content-Type") == "application/json":
        args = args or request.get_json()
    elif request.method == "GET":
        args = args or {key: value for key, value in request.args.items()}
    logger.debug(f"Request details: {request} | args: {args}")


@app.route('/api/life_check', methods=['GET'])
def life_check():
    # Your main function logic goes here
    data = {'message': 'Hello from Python backend!'}
    return jsonify(data)


@app.route('/api/database_songs', methods=['GET'])
@login_required
def get_database_songs():
    db_songs = db.session.scalars(
        db.select(Track.title)
        .join(Account.tracks)
        .where(Account.id == current_user.id)
    ).all()
    return jsonify(db_songs)


@app.route('/api/upload_song', methods=['POST'])
@login_required
def upload_song():
    audio_file = request.files.get("file")
    title = request.form.get("title")

    if not all([audio_file, title]):
        return jsonify(error="Missing required parameters."), 400

    try:
        upload_to_db_protected(audio_file=audio_file, title=title)  # Uploads track to ACRCloud db
        acrcloud_id = [acrcloud_track['id'] for acrcloud_track in get_human_readable_db() if acrcloud_track['title'] == title][0]
        create_track(title=title, account_id=current_user.id, acrcloud_id=acrcloud_id)  # Creates track in SQL db
        return jsonify(message="Song uploaded successfully.")
    except (TrackExistsError, MusicDuplicationError) as e:
        return jsonify(error=str(e)), 409
    except Exception as e:
        logger.error(f"Server error uploading song. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/delete_song', methods=['DELETE'])
def delete_song():
    data = request.get_json()  # Retrieve data from the request body

    # Check if the 'id' parameter exists in the request body
    file_id = data.get("id")
    if not file_id:
        return jsonify(error="Missing 'id' parameter in the request body."), 400

    account_songs_id = db.session.scalars(db.select(Track.track_id).where(Track.account_id == current_user.id)).all()
    if not current_user.admin and file_id not in account_songs_id:
        logger.warning(f"Account tried deleting other account's song. Account ID:{current_user.id} | Song: {file_id}")
        return "Admin permission required.", 403
    try:
        delete_track(acrcloud_id=file_id)  # Delete from SQL db
        delete_id_from_db_protected_for_web(file_id)  # Delete from ACRCloud db
        return jsonify(message="Song deleted successfully.")
    except (TrackNotExistsError, MusicFileDoesNotExist) as e:
        return jsonify(error=str(e)), 404
    except Exception as e:
        logger.error(f"Server error deleting song. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/location_songs', methods=['POST'])
@login_required
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

    drive.date_now = datetime.datetime.today().date()
    try:
        stories_with_recognized_songs = location_logic(location=location, drive=drive,
                                                day=int(start_day), month=int(start_month), year=int(start_year),
                                                end_day=int(end_day), end_month=int(end_month), end_year=int(end_year))
        account_tracks = db.session.scalars(
            db.select(Track.title)
            .join(Account.tracks)
            .where(Account.id == current_user.id)
        ).all()
        stories_with_recognized_account_songs = []
        for story in stories_with_recognized_songs:
            if story["results"]["title"] in account_tracks:
                stories_with_recognized_account_songs.append(story)
        return jsonify(stories_with_recognized_account_songs)
    except Exception as e:
        logger.error(f"Server error searching recognized location songs. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/admin/add_location_to_account', methods=['POST'])
@login_required
def add_location_to_account():
    if not current_user.admin:
        return "Admin permission required.", 403

    data = request.get_json()  # Retrieve data from the request body
    location_name = data.get('location_name')
    username = data.get('username')
    if not all([location_name, username]):
        return jsonify(error="Missing required parameters (location_name or username)."), 400

    account = db.session.execute(db.select(Account).filter_by(username=username)).scalar_one_or_none()
    if not account:
        return jsonify(error="Account not found"), 404

    try:
        add_account_followed_location(location_name=location_name, account=account)
        return jsonify(f"Successfully added location {location_name} to user {username}"), 200
    except LocationExistsError as e:
        return jsonify(error=str(e)), 409
    except Exception as e:
        logger.error(f"Server error adding location to account. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/admin/delete_location_from_account', methods=['DELETE'])
@login_required
def delete_location_from_account():
    if not current_user.admin:
        return "Admin permission required.", 403

    data = request.get_json()  # Retrieve data from the request body
    location_name = data.get('location_name')
    username = data.get('username')
    if not all([location_name, username]):
        return jsonify(error="Missing required parameters (location_name or username)."), 400

    account = db.session.execute(db.select(Account).filter_by(username=username)).scalar_one_or_none()
    if not account:
        return jsonify(error="Account not found"), 404

    try:
        delete_account_followed_location(location_name=location_name, account=account)
        return jsonify(f"Successfully deleted location {location_name} from account {username}"), 200
    except LocationNotExistsError as e:
        return jsonify(error=str(e)), 404
    except Exception as e:
        logger.error(f"Server error deleting location for account in SQL db. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/admin/add_location_to_follow', methods=['POST'])
@login_required
def add_location_to_follow():
    if not current_user.admin:
        return "Admin permission required.", 403

    data = request.get_json()  # Retrieve data from the request body
    location_name = data.get('location_name')

    try:
        create_location(location_name)
        return jsonify(f"Successfully added location {location_name} to download and recognize stories from."), 200
    except LocationExistsError as e:
        return jsonify(error=str(e)), 409
    except Exception as e:
        logger.error(f"Server error adding location to account. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/admin/delete_location_for_all_accounts', methods=['DELETE'])
@login_required
def delete_location_for_all_accounts():
    """Delete location and all it's associations from database"""
    if not current_user.admin:
        return "Admin permission required.", 403

    data = request.get_json()  # Retrieve data from the request body
    location_name = data.get('location_name')
    if not location_name:
        return jsonify(error="Missing parameter location name."), 400

    try:
        delete_location(name=location_name)
        return jsonify(f"Successfully deleted location {location_name}"), 200
    except LocationNotExistsError as e:
        return jsonify(error=str(e)), 404
    except Exception as e:
        logger.error(f"Server error deleting location from SQL db. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/locations', methods=['GET'])
@login_required
def get_locations():
    drive.date_now = datetime.datetime.today().date()
    try:
        all_users_locations_dates = drive.get_locations_and_dates(locations_dir_id=drive.SPOT_LOCATIONS_DIR_ID)
        user_locations_and_dates = []
        user_locations = db.session.scalars(
            db.select(Location.name)
            .join(Account.locations)
            .where(Account.id == current_user.id)
        ).all()
        for location_name in user_locations:
            location_and_date = [location_date for location_date in all_users_locations_dates if location_date['location'] == location_name][0]
            user_locations_and_dates.append(location_and_date)
    except Exception as e:
        logger.error(f"Server error getting locations and dates. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500
    return jsonify(user_locations_and_dates)


@app.route('/api/admin/user_locations', methods=['GET'])
@login_required
def get_user_locations():
    """Get all users associated locations"""
    if not current_user.admin:
        return "Admin permission required.", 403

    username = request.args.get("username")
    account = db.session.execute(db.select(Account).filter_by(username=username)).scalar_one_or_none()
    if not account:
        return jsonify(error="Account not found"), 404

    locations = db.session.execute(
        db.select(Location.name, Location.created_at)
        .join(Account.locations)
        .where(Account.username == username)
    ).all()
    location_and_creation = [{"name": location.name, "created_at": location.created_at} for location in locations]
    return jsonify(location_and_creation), 200


@app.route('/api/admin/user_tracks', methods=['GET'])
@login_required
def get_user_tracks():
    """Get all users associated tracks"""
    if not current_user.admin:
        return "Admin permission required.", 403

    username = request.args.get("username")
    account = db.session.execute(db.select(Account).filter_by(username=username)).scalar_one_or_none()
    if not account:
        return jsonify(error="Account not found"), 404

    tracks = db.session.execute(
        db.select(Track.title, Track.acrcloud_id, Track.created_at)
        .join(Account.tracks)
        .where(Account.username == username)
    ).all()
    user_tracks_data = [{"title": track.title, "acrcloud_id": track.acrcloud_id, "created_at": track.created_at} for track in tracks]
    return jsonify(user_tracks_data), 200


@app.route('/api/admin/all_users', methods=['GET'])
@login_required
def get_all_users():
    """Get all users basic data"""
    if not current_user.admin:
        return "Admin permission required.", 403

    users = db.session.execute(
        db.select(
            Account.username,
            Account.first_name,
            Account.last_name,
            Account.email,
            Account.created_at,
            Account.last_login_at,
            Account.date_of_birth,
            Account.admin
        )
    ).all()
    users_data = []
    for user in users:
        users_data.append({"username": user.username,
                           "first_name": user.first_name,
                           "last_name": user.last_name,
                           "email": user.email,
                           "created_at": user.created_at,
                           "last_login_at": user.last_login_at,
                           "date_of_birth": user.date_of_birth,
                           "admin": user.admin})
    return jsonify(users_data), 200


@app.route('/api/send_location_email', methods=['POST'])
@login_required
def send_email():
    data = request.get_json()
    recipients = data.get('recipients')
    subject = f"New Location Request! from {data.get('fullname')}"
    message_body = render_template('email_template.html', subject=subject,
                                   fullname=data.get('fullname'), email=data.get('email'),
                                   locationWanted=data.get('locationWanted'))

    if not recipients or not isinstance(recipients, list):
        return jsonify(error="Invalid recipients data, should send an array."), 400

    msg = Message(subject=subject, recipients=recipients)
    msg.html = message_body

    try:
        mail.send(msg)
        return jsonify(message="Email was sent successfully!")
    except Exception as e:
        logger.error(f"Server error sending mail. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()  # Retrieve data from the request body
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    date_of_birth = datetime.date.fromisoformat(data.get('date_of_birth'))
    try:
        create_account(email, username, password, first_name, last_name, date_of_birth)
        return jsonify(message="Account signed up successfully"), 201
    except EmailExistsError as e:
        return jsonify(error=str(e)), 409
    except Exception as e:
        logger.error(f"Server error signing up. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()  # Retrieve data from the request body
    username = data.get('username')
    password = data.get('password')
    remember = True if data.get('remember') else False

    account = db.session.execute(db.select(Account).filter_by(username=username)).scalar_one_or_none()
    if not account or not check_password_hash(account.password, password):
        return jsonify(error="Account not found"), 404

    account.last_login_at = datetime.datetime.now()
    db.session.commit()
    login_user(account, remember=remember)
    return jsonify({'first_name': account.first_name, 'last_name': account.last_name, "admin": account.admin}), 200


@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(Account).where(Account.id == user_id)).scalar_one_or_none()


@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return f'Successfully logged out', 200


@login_required
@app.route('/api/delete_user', methods=['DELETE'])
def delete_user():
    account = db.session.execute(db.select(Account).filter_by(id=current_user.id)).scalar_one_or_none()
    try:
        account_tracks_id = db.session.scalars(
            db.select(Track.acrcloud_id)
            .join(Account.tracks)
            .where(Account.id == account.id)
        ).all()
        for track_id in account_tracks_id:
            delete_id_from_db_protected_for_web(track_id)  # Delete from ACRCloud db
        db.session.delete(account)
        db.session.commit()
    except Exception as e:
        logger.error(f"Server error deleting user {current_user.username}. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500
    return f'Successfully deleted user {current_user.username}', 200


@app.route('/')
def index():
    return jsonify({'answer': 'Hello, this is Spot backend. Check out our site, Google SPOT music.'})


@app.route('/api/admin/rescan_all_songs', methods=['POST'])
@login_required
def rescan_all_songs():
    if not current_user.admin:
        return "Admin permission required.", 403

    try:
        rescan_all_files()
        return f'Successfully rescanned all songs in the database', 200
    except Exception as e:
        logger.error(f"Server error rescanning all songs. Traceback:\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(host='0.0.0.0', port=5000, debug=True)
