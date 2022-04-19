from flask_restful import Resource, reqparse
from flask_jwt_extended import (
    jwt_required,
)
from starlette import status
from models.item import ItemModel

BLANK_ERROR = "'{}' cannot be left blank."
NAME_ALREADY_EXISTS = "An item with name '{}' already exists."
ERROR_INSERTING = "An error occurred while inserting the item."
ITEM_NOT_FOUND = "Item not found."
ITEM_DELETE = "Item deleted."


class Item(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "price", type=float, required=True, help=BLANK_ERROR.format("price")
    )
    parser.add_argument(
        "store_id", type=int, required=True, help=BLANK_ERROR.format("store_id")
    )

    @classmethod
    @jwt_required
    def get(cls, name: str):
        item = ItemModel.find_by_name(name)

        if item:
            return item.json(), status.HTTP_200_OK

        return {"message": ITEM_NOT_FOUND}, status.HTTP_404_NOT_FOUND

    @classmethod
    @jwt_required(fresh=True)
    def post(cls, name: str):
        if ItemModel.find_by_name(name):
            return {
                "message": NAME_ALREADY_EXISTS.format(name)
            }, status.HTTP_400_BAD_REQUEST

        data = Item.parser.parse_args()
        item = ItemModel(name, **data)

        try:
            item.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, status.HTTP_500_INTERNAL_SERVER_ERROR

        return item.json(), status.HTTP_201_CREATED

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
        data = Item.parser.parse_args()
        item = ItemModel.find_by_name(name)

        if item:
            item.price = data["price"]
        else:
            item = ItemModel(name, **data)

        item.save_to_db()

        return item.json(), status.HTTP_200_OK


class ItemList(Resource):
    @classmethod
    def get(cls):
        items = [item.json() for item in ItemModel.find_all()]
        return {"items": items}, status.HTTP_200_OK
