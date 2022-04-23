from flask_restful import Resource
from starlette import status

from schemas.store import StoreSchema
from models.store import StoreModel
from libs.strings import gettext

store_schema = StoreSchema()
store_list_schema = StoreSchema(many=True)


class Store(Resource):
    @classmethod
    def get(cls, name: str):
        store = StoreModel.find_by_name(name)
        if store:
            return store_schema.dump(store)
        return {"message": gettext("store_not_found")}, status.HTTP_404_NOT_FOUND

    @classmethod
    def post(cls, name: str):
        if StoreModel.find_by_name(name):
            return {
                "message": gettext("store_name_exists").format(name)
            }, status.HTTP_400_BAD_REQUEST

        store = StoreModel(name=name)

        try:
            store.save_to_db()
        except:
            return {
                "message": gettext("store_error_inserting")
            }, status.HTTP_500_INTERNAL_SERVER_ERROR

        return store_schema.dump(store), status.HTTP_201_CREATED

    @classmethod
    def delete(cls, name: str):
        store = StoreModel.find_by_name(name)
        if store:
            store.delete_from_db()
            return {"message": gettext("store_deleted")}, status.HTTP_200_OK

        return {"message": gettext("store_not_found")}, status.HTTP_404_NOT_FOUND


class StoreList(Resource):
    @classmethod
    def get(cls):
        return {"stores": store_list_schema.dump(StoreModel.find_all())}
