from loguru import logger
from dbconf import db, Track, Location, Account


class TrackDBError(Exception):
    pass


class LocationDBError(Exception):
    pass


class LocationExistsError(LocationDBError):
    def __init__(self, location: Location):
        self.message = f"Location already exists in the database: {location.name} created at {location.created_at}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class LocationNotExistsError(LocationDBError):
    def __init__(self, name: str):
        self.message = f"Location does not exist in the database: {name}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class TrackExistsError(TrackDBError):
    def __init__(self, track: Track):
        self.message = f"Track already exists in the database: {track.title} created at {track.created_at}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class TrackNotExistsError(TrackDBError):
    def __init__(self, acrcloud_id: str):
        self.message = f"Track does not exist in the database: {acrcloud_id}"
        logger.error(self.message)

    def __str__(self):
        return self.message


def create_track(title: str, account_id: int, acrcloud_id: int):
    """Add track credentials to db"""
    track = db.session.execute(db.select(Track).filter_by(title=title)).scalar_one_or_none()
    if track:
        raise TrackExistsError(track)

    # Create a new track
    new_track = Track(title=title, account_id=account_id, acrcloud_id=acrcloud_id)

    # Add the new track to the database
    db.session.add(new_track)
    db.session.commit()
    logger.success(f"Added track {title} for account ID {account_id} to SQL db")
    return


def delete_track(acrcloud_id: str):
    """Delete track from db"""
    track = db.session.execute(db.select(Track).filter_by(acrcloud_id=acrcloud_id)).scalar_one_or_none()
    if not track:
        raise TrackNotExistsError(acrcloud_id)

    db.session.delete(track)
    db.session.commit()
    logger.success(f"Deleted track with acrcloud ID {acrcloud_id} from SQL db")
    return


def create_location(location_name: str):
    """Add location credentials to db"""
    location = db.session.execute(db.select(Location).where(Location.name == location_name)).scalar_one_or_none()
    if location:
        raise LocationExistsError(location)

    # Create a new location
    admin_accounts = db.session.scalars(
        db.select(Account).filter_by(admin=True)
    ).all()
    new_location = Location(name=location_name, accounts=admin_accounts)

    # Add the new location to the database
    db.session.add(new_location)
    db.session.commit()
    logger.success(f"Added location {location_name} to SQL db")
    return


def delete_location(name: str):
    """Delete location from db"""
    location = db.session.execute(db.select(Location).filter_by(name=name)).scalar_one_or_none()
    if not location:
        raise LocationNotExistsError(name)

    db.session.delete(location)
    db.session.commit()
    logger.success(f"Delete location {name} from SQL db")
    return


def delete_account_followed_location(location_name: str, account: Account):
    """Delete location from account's followed locations (SQL db)."""
    location = db.session.execute(db.select(Location).filter_by(name=location_name)).scalar_one_or_none()
    if not location:
        raise LocationNotExistsError(location_name)

    location.accounts.remove(account)
    db.session.commit()
    logger.success(f"Deleted location {location_name} for account {account.username} from SQL db")
    return


def add_account_followed_location(location_name: str, account: Account):
    """Add location to account's followed locations (SQL db)."""
    location_in_db = db.session.execute(
        db.select(Location)
        .join(Account.locations)
        .where(Account.id == account.id)
        .filter_by(name=location_name)
    ).scalar_one_or_none()

    if location_in_db:
        raise LocationExistsError(location_in_db)
    location = db.session.scalar(  # If locations were created admin accounts contain them
        db.select(Location)
        .join(Location.accounts)
        .where(Account.admin and Location.name == location_name)
    )
    if not location:
        raise LocationNotExistsError(location_name)

    # Add the location
    location.accounts.append(account)
    db.session.commit()
    logger.success(f"Added location {location_name} for account {account.username} in SQL db")
    return
