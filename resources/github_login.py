from flask import g, request, url_for
from flask_restful import Resource
from flask_jwt_extended import create_refresh_token, create_access_token
from oauth.oa import github
from starlette import status

from models.user import UserModel


class GithubLogin(Resource):
    @classmethod
    def get(cls):
        return github.authorize(callback=url_for("github.authorize", _external=True))


class GithubAuthorize(Resource):
    @classmethod
    def get(cls):
        resp = github.authorized_response()

        if resp is None or resp.get("access_token") is None:
            error_message = {
                "error": request.args["error"],
                "error_description": request.args["error_description"],
            }
            return error_message

        g.access_token = resp["access_token"]
        github_user = github.get("user")
        github_username = github_user.data["login"]

        user = UserModel.query.filter_by(username=github_username).first()

        if not user:
            user = UserModel(username=github_username, password=None)
            user.save_to_db()

        access_token = create_access_token(identity=user.id, fresh=True)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "name": user.username,
        }, status.HTTP_200_OK
