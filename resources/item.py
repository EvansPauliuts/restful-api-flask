from flask_restful import Resource
from flask import request
from flask_jwt_extended import (
    jwt_required,
)
from starlette import status

from schemas.item import ItemSchema
from models.item import ItemModel

NAME_ALREADY_EXISTS = "An item with name '{}' already exists."
ERROR_INSERTING = "An error occurred while inserting the item."
ITEM_NOT_FOUND = "Item not found."
ITEM_DELETE = "Item deleted."

item_schema = ItemSchema()
item_list_schema = ItemSchema(many=True)


class Item(Resource):
    @classmethod
    @jwt_required
    def get(cls, name: str):
        item = ItemModel.find_by_name(name)

        if item:
            return item_schema.dump(item), status.HTTP_200_OK

        return {"message": ITEM_NOT_FOUND}, status.HTTP_404_NOT_FOUND

    @classmethod
    @jwt_required(fresh=True)
    def post(cls, name: str):
        if ItemModel.find_by_name(name):
            return {
                "message": NAME_ALREADY_EXISTS.format(name)
            }, status.HTTP_400_BAD_REQUEST

        item_json = request.get_json()
        item_json["name"] = name

        item = item_schema.load(item_json)

        try:
            item.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, status.HTTP_500_INTERNAL_SERVER_ERROR

        return item_schema.dump(item), status.HTTP_201_CREATED

    @classmethod
    @jwt_required
    def delete(cls, name: str):
        item = ItemModel.find_by_name(name)

        if item:
            item.delete_from_db()
            return {"message": ITEM_DELETE}, status.HTTP_200_OK

        return {"message": ITEM_NOT_FOUND}, status.HTTP_404_NOT_FOUND

    @classmethod
    def put(cls, name: str):
        item_json = request.get_json()
        item = ItemModel.find_by_name(name)

        if item:
            item.price = item_json.price
        else:
            item_json.name = name
            item = item_json.load(item_json)

        item.save_to_db()

        return item_schema.dump(item), status.HTTP_200_OK


class ItemList(Resource):
    @classmethod
    def get(cls):
        return {
            "items": item_list_schema.dump(ItemModel.find_all())
        }, status.HTTP_200_OK
