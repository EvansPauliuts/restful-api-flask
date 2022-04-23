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
from blacklist import BLACKLIST
from libs.mailgun import MailGunException

BLANK_ERROR = "'{}' cannot be blank."
USER_ALREADY_EXISTS = "A user with that username already exists."
EMAIL_ALREADY_EXISTS = "A user with that email already exists."
CREATED_SUCCESSFULLY = "Account created successfully."
USER_NOT_FOUND = "User not found."
USER_DELETED = "User deleted."
INVALID_CREDENTIALS = "Invalid credentials!"
USER_LOGGED_OUT = "User <id={}> successfully logged out."
NOT_CONFIRMED_ERROR = (
    "You have not confirmed registration, please check your email <{}>"
)
USER_CONFIRMED = "User confirmed."
FAILED_TO_CREATE = "Internal server error. Failed to create user."

user_schema = UserSchema()


class UserRegister(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user_data = user_schema.load(user_json)

        if UserModel.find_by_username(user_data.username):
            return {"message": USER_ALREADY_EXISTS}, status.HTTP_400_BAD_REQUEST

        if UserModel.find_by_email(user_data.email):
            return {"message": EMAIL_ALREADY_EXISTS}, status.HTTP_400_BAD_REQUEST

        try:
            user_data.save_to_db()
            user_data.send_confirmation_email()

            return {"message": CREATED_SUCCESSFULLY}, status.HTTP_201_CREATED
        except MailGunException as e:
            user_data.delete_from_db()
            return {"message": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR
        except:
            return {"message": FAILED_TO_CREATE}, status.HTTP_500_INTERNAL_SERVER_ERROR


class User(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, status.HTTP_404_NOT_FOUND
        return user_schema.dump(user), status.HTTP_200_OK

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, status.HTTP_404_NOT_FOUND
        user.delete_from_db()
        return {"message": USER_DELETED}, status.HTTP_200_OK


class UserLogin(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user_data = user_schema.load(user_json, partial=("email",))

        user = UserModel.find_by_username(user_data.username)

        if user and safe_str_cmp(user.password, user_data.password):
            if user.activated:
                access_token = create_access_token(identity=user.id, fresh=True)
                refresh_token = create_refresh_token(user.id)
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }, status.HTTP_200_OK
            return {
                "message": NOT_CONFIRMED_ERROR.format(user.email)
            }, status.HTTP_400_BAD_REQUEST

        return {"message": INVALID_CREDENTIALS}, status.HTTP_401_UNAUTHORIZED


class UserLogout(Resource):
    @classmethod
    @jwt_required
    def post(cls):
        jti = get_jwt()["jti"]
        user_id = get_jwt_identity()
        BLACKLIST.add(jti)
        return {"message": USER_LOGGED_OUT.format(user_id)}, status.HTTP_200_OK


class TokenRefresh(Resource):
    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, status.HTTP_200_OK


class UserConfirm(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, status.HTTP_404_NOT_FOUND

        user.activated = True
        user.save_to_db()
        return {"message": USER_CONFIRMED}, status.HTTP_200_OK
