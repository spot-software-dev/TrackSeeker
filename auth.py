import datetime

from loguru import logger
from werkzeug.security import generate_password_hash
from dbconf import db, Account


class AuthError(ValueError):
    pass


class EmailExistsError(AuthError):
    def __init__(self, account: Account):
        self.message = f"E-Mail already exists in the database: f'{account.email}: {account.username}'"
        logger.error(self.message)

    def __str__(self):
        return self.message


def create_account(email: str, username: str, password: str,
                   first_name: str, last_name: str, date_of_birth: datetime.date):
    """Add account credentials to db"""
    account = db.session.execute(db.select(Account).filter_by(email=email)).scalar_one_or_none()
    if account:
        raise EmailExistsError(account)

    # Create a new account
    new_account = Account(email=email, username=username, password=generate_password_hash(password),
                          first_name=first_name, last_name=last_name, date_of_birth=date_of_birth)

    # Add the new account to the database
    db.session.add(new_account)
    db.session.commit()
    return
