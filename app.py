from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from marshmallow import ValidationError
from starlette import status

from db import db
from blacklist import BLACKLIST
from resources.user import UserRegister, UserLogin, User, TokenRefresh, UserLogout
from resources.item import Item, ItemList
from resources.store import Store, StoreList
from ma import ma

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = [
    "access",
    "refresh",
]
app.secret_key = "jose"
api = Api(app)


@app.before_first_request
def create_tables():
    db.create_all()


@app.errorhandler(ValidationError)
def handle_marshmallow(err):
    return jsonify(err.messages), status.HTTP_400_BAD_REQUEST


jwt = JWTManager(app)


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    return decrypted_token["jti"] in BLACKLIST


api.add_resource(Store, "/store/<string:name>")
api.add_resource(StoreList, "/stores")
api.add_resource(Item, "/item/<string:name>")
api.add_resource(ItemList, "/items")
api.add_resource(UserRegister, "/register")
api.add_resource(User, "/user/<int:user_id>")
api.add_resource(UserLogin, "/login")
api.add_resource(TokenRefresh, "/refresh")
api.add_resource(UserLogout, "/logout")

if __name__ == "__main__":
    db.init_app(app)
    ma.init_app(app)
    app.run(port=5000, debug=True)
