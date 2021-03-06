from flask import request, url_for
from typing import Dict, Union
from requests import Response

from database.db import db
from libs.mailgun import MailGun
from .confirmation import ConfirmationModel

UserJSON = Dict[str, Union[str, int]]


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    # password = database.Column(database.String(80), nullable=False)
    # email = db.Column(db.String(80), nullable=False, unique=True)

    # oauth
    password = db.Column(db.String(80))

    # confirmation = database.relationship(
    #     "ConfirmationModel",
    #     lazy="dynamic",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    # )

    @property
    def most_recent_confirmation(self) -> "ConfirmationModel":
        return self.confirmation.order_by(db.desc(ConfirmationModel.expire_at)).first()

    @classmethod
    def find_by_username(cls, username: str) -> "UserModel":
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_email(cls, email: str) -> "UserModel":
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_id(cls, _id: int) -> "UserModel":
        return cls.query.filter_by(id=_id).first()

    def send_confirmation_email(self) -> Response:
        link = request.url_root[:-1] + url_for(
            "confirmation", confirmation_id=self.most_recent_confirmation.id
        )
        subject = "Registration confirmation"
        text = f"Please click the link to confirm your registration: {link}"
        html = f'<html>Please click the link to confirm your registration: <a href="{link}">{link}</a></html>'

        return MailGun.send_email([self.email], subject=subject, text=text, html=html)

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
