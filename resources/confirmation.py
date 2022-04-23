from flask_restful import Resource
import traceback
from time import time

from starlette import status

from models.confirmation import ConfirmationModel
from schemas.confirmation import ConfirmationSchema
from models.user import UserModel
from libs.mailgun import MailGunException
from libs.strings import gettext

confirmation_schema = ConfirmationSchema()


class Confirmation(Resource):
    @classmethod
    def get(cls, confirmation_id: str):
        confirmation = ConfirmationModel.find_by_id(confirmation_id)
        if not confirmation:
            return {
                "message": gettext("confirmation_not_found")
            }, status.HTTP_404_NOT_FOUND

        if confirmation.expired:
            return {
                "message": gettext("confirmation_link_expired")
            }, status.HTTP_400_BAD_REQUEST

        if confirmation.confirmed:
            return {
                "message": gettext("confirmation_already_confirmed")
            }, status.HTTP_400_BAD_REQUEST

        confirmation.confirmed = True
        confirmation.save_to_db()

        return {
            "message": gettext("confirmation_resend_successful")
        }, status.HTTP_200_OK


class ConfirmationByUser(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, status.HTTP_404_NOT_FOUND
        return (
            {
                "current_time": int(time()),
                "confirmation": [
                    confirmation_schema.dump(each)
                    for each in user.confirmation.order_by(ConfirmationModel.expire_at)
                ],
            },
            status.HTTP_200_OK,
        )

    @classmethod
    def post(cls, user_id):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, status.HTTP_404_NOT_FOUND

        try:
            confirmation = user.most_recent_confirmation
            if confirmation:
                if confirmation.confirmed:
                    return {
                        "message": gettext("confirmation_already_confirmed")
                    }, status.HTTP_400_BAD_REQUEST
                confirmation.force_to_expire()

            new_confirmation = ConfirmationModel(user_id)
            new_confirmation.save_to_db()
            user.send_confirmation_email()
            return {
                "message": gettext("confirmation_resend_successful")
            }, status.HTTP_201_CREATED
        except MailGunException as e:
            return {"message": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR
        except:
            traceback.print_exc()
            return {
                "message": gettext("confirmation_resend_fail")
            }, status.HTTP_500_INTERNAL_SERVER_ERROR
