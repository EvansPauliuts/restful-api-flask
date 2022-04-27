from flask_restful import Resource
from flask import request
from werkzeug.security import safe_str_cmp
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)
from starlette import status

from schemas.user import UserSchema
from models.user import UserModel

# from models.confirmation import ConfirmationModel
from blacklist import BLACKLIST

# from libs.mailgun import MailGunException
from libs.strings import gettext

user_schema = UserSchema()


class UserRegister(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user_data = user_schema.load(user_json)

        if UserModel.find_by_username(user_data.username):
            return {
                "message": gettext("user_username_exists")
            }, status.HTTP_400_BAD_REQUEST

        if UserModel.find_by_email(user_data.email):
            return {
                "message": gettext("user_email_exists")
            }, status.HTTP_400_BAD_REQUEST

        try:
            user_data.save_to_db()
            # confirmation = ConfirmationModel(user_data.id)
            # confirmation.save_to_db()
            # user_data.send_confirmation_email()

            return {"message": gettext("user_registered")}, status.HTTP_201_CREATED
        # except MailGunException as e:
        #     user_data.delete_from_db()
        #     return {"message": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR
        except:
            user_data.delete_from_db()
            return {
                "message": gettext("user_error_creating")
            }, status.HTTP_500_INTERNAL_SERVER_ERROR


class User(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, status.HTTP_404_NOT_FOUND
        return user_schema.dump(user), status.HTTP_200_OK

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, status.HTTP_404_NOT_FOUND
        user.delete_from_db()
        return {"message": gettext("user_deleted")}, status.HTTP_200_OK


class UserLogin(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user_data = user_schema.load(user_json, partial=("email",))

        user = UserModel.find_by_username(user_data.username)

        if user and user.password and safe_str_cmp(user.password, user_data.password):
            # confirmation = user.most_recent_confirmation
            # if confirmation and confirmation.confirmed:
            #     access_token = create_access_token(identity=user.id, fresh=True)
            #     refresh_token = create_refresh_token(user.id)
            #     return {
            #         "access_token": access_token,
            #         "refresh_token": refresh_token,
            #     }, status.HTTP_200_OK
            # return {
            #     "message": gettext("user_not_confirmed").format(user.email)
            # }, status.HTTP_400_BAD_REQUEST

            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(user.id)
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }, status.HTTP_200_OK

        return {
            "message": gettext("user_invalid_credentials")
        }, status.HTTP_401_UNAUTHORIZED


class UserLogout(Resource):
    @classmethod
    @jwt_required
    def post(cls):
        jti = get_jwt()["jti"]
        user_id = get_jwt_identity()
        BLACKLIST.add(jti)
        return {
            "message": gettext("user_logged_out").format(user_id)
        }, status.HTTP_200_OK


class TokenRefresh(Resource):
    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, status.HTTP_200_OK


class SetPassword(Resource):
    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        user_json = request.get_json()
        user_data = user_schema.load(user_json)
        user = UserModel.find_by_username(user_data.username)

        if not user:
            return {"message": gettext("user_not_found")}, status.HTTP_400_BAD_REQUEST

        user.password = user_data.password
        user.save_to_db()

        return {"message": gettext("user_password_updated")}, status.HTTP_201_CREATED
