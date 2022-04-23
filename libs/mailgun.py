import os

from typing import List
from requests import Response, post

from libs.strings import gettext


class MailGunException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class MailGun:
    MAILGUM_DOMAIN = os.getenv("MAILGUM_DOMAIN")
    MAILGUM_API_KEY = os.getenv("MAILGUM_API_KEY")
    FROM_TITLE = os.getenv("FROM_TITLE")
    FROM_EMAIL = os.getenv("FROM_EMAIL")

    @classmethod
    def send_email(
        cls, email: List[str], subject: str, text: str, html: str
    ) -> Response:
        if cls.MAILGUM_API_KEY is None:
            raise MailGunException(gettext("mailgun_failed_load_api_key"))

        if cls.MAILGUM_DOMAIN is None:
            raise MailGunException(gettext("mailgun_failed_load_domain"))

        response = post(
            f"https://api.mailgun.net/v3/{cls.MAILGUM_DOMAIN}/messages",
            auth=("api", cls.MAILGUM_API_KEY),
            data={
                "from": f"{cls.FROM_TITLE} <{cls.FROM_EMAIL}>",
                "to": email,
                "subject": subject,
                "text": text,
                "html": html,
            },
        )

        if response.status_code != 200:
            raise MailGunException(gettext("mailgun_error_send_email"))

        return response
