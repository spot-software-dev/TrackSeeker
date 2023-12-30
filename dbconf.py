import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import List, Type
from flask_login import UserMixin


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


# Association Table (Many-to-Many relationship)
account_location = db.Table(
    "account_location",
    db.Model.metadata,
    db.Column("account_id", db.ForeignKey("account.id", ondelete="CASCADE")),
    db.Column("location_id", db.ForeignKey("location.location_id", ondelete="CASCADE")),
    db.Column("created_at", db.DateTime(timezone=True), nullable=False, default=func.now())
)


class Account(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(db.Integer, db.Identity(always=True, start=1, increment=1), primary_key=True)
    username: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String, nullable=False)
    first_name: Mapped[str] = mapped_column(db.String(30))
    last_name: Mapped[str] = mapped_column(db.String(40))
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, default=func.now())
    email: Mapped[str] = mapped_column(db.String, nullable=False)
    last_login_at: Mapped[datetime.datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, default=func.now())
    date_of_birth: Mapped[datetime.date] = mapped_column(db.Date)
    admin: Mapped[bool] = mapped_column(db.Boolean, default=False)
    tracks: Mapped[List["Track"]] = db.relationship(
        "Track",
        back_populates="account",
        cascade="all, delete",
        passive_deletes=True
    )
    locations: Mapped[List["Location"]] = db.relationship(  # Enables access to locations from Account instance
        "Location",
        secondary="account_location",
        back_populates="accounts",
        cascade="all, delete",
        passive_deletes=True
    )


class Location(db.Model):
    location_id: Mapped[int] = mapped_column(db.Integer, db.Identity(always=True, start=1, increment=1), primary_key=True)
    name: Mapped[str] = mapped_column(db.String, nullable=False, unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, default=func.now())
    accounts: Mapped[List[Type[Account]]] = db.relationship(  # Enables access to accounts from Location instance
        "Account",
        secondary="account_location",
        back_populates="locations",
        cascade="all, delete",
        passive_deletes=True
    )


class Track(db.Model):
    track_id: Mapped[int] = mapped_column(db.Integer, db.Identity(always=True, start=1, increment=1), primary_key=True)
    account_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("account.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(db.String, nullable=False, unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, default=func.now())
    acrcloud_id: Mapped[int] = mapped_column(db.Integer, nullable=False, unique=True)
    account: Mapped[List[Type[Account]]] = db.relationship(
        "Account",
        back_populates="tracks",
        cascade="all, delete",
        passive_deletes=True
    )
