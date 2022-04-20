from flask_restful import Resource
from starlette import status

from schemas.store import StoreSchema
from models.store import StoreModel

NAME_ALREADY_EXISTS = "A store with name '{}' already exists."
ERROR_INSERTING = "An error occurred while creating the store."
STORE_NOT_FOUND = "Store not found."
STORE_DELETED = "Store deleted."

store_schema = StoreSchema()
store_list_schema = StoreSchema(many=True)


class Store(Resource):
    @classmethod
    def get(cls, name: str):
        store = StoreModel.find_by_name(name)
        if store:
            return store_schema.dump(store)
        return {"message": STORE_NOT_FOUND}, status.HTTP_404_NOT_FOUND

    @classmethod
    def post(cls, name: str):
        if StoreModel.find_by_name(name):
            return {
                "message": NAME_ALREADY_EXISTS.format(name)
            }, status.HTTP_400_BAD_REQUEST

        store = StoreModel(name=name)

        try:
            store.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, status.HTTP_500_INTERNAL_SERVER_ERROR

        return store_schema.dump(store), status.HTTP_201_CREATED

    @classmethod
    def delete(cls, name: str):
        store = StoreModel.find_by_name(name)
        if store:
            store.delete_from_db()

        return {"message": STORE_DELETED}


class StoreList(Resource):
    @classmethod
    def get(cls):
        return {"stores": store_list_schema.dump(StoreModel.find_all())}
