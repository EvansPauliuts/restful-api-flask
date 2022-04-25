import os

from starlette import status
from flask_restful import Resource
from flask_uploads import UploadNotAllowed
from flask import request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from libs import image_helper
from libs.strings import gettext
from schemas.image import ImageSchema

image_schema = ImageSchema()


class ImageUpload(Resource):
    @classmethod
    @jwt_required
    def post(cls):
        data = image_schema.load(request.files)
        user_id = get_jwt_identity()
        folder = f"user_{user_id}"

        try:
            image_path = image_helper.save_image(data["image"], folder)
            basename = image_helper.get_basename(image_path)
            return {
                "message": gettext("image_uploaded").format(basename)
            }, status.HTTP_201_CREATED
        except UploadNotAllowed:
            extension = image_helper.get_extension(data["image"])
            return {
                "message": gettext("image_illegal_extension").format(extension)
            }, status.HTTP_400_BAD_REQUEST


class Image(Resource):
    @classmethod
    @jwt_required
    def get(cls, filename: str):
        user_id = get_jwt_identity()
        folder = f"user_{user_id}"

        if not image_helper.is_filename_safe(filename):
            return {
                "message": gettext("image_illegal_file_name").format(filename)
            }, status.HTTP_400_BAD_REQUEST

        try:
            return send_file(image_helper.get_path(filename, folder=folder))
        except FileNotFoundError:
            return {
                "message": gettext("image_not_found").format(filename)
            }, status.HTTP_404_NOT_FOUND

    @classmethod
    @jwt_required
    def delete(cls, filename: str):
        user_id = get_jwt_identity()
        folder = f"user_{user_id}"

        if not image_helper.is_filename_safe(filename):
            return {
                "message": gettext("image_illegal_file_name").format(filename)
            }, status.HTTP_400_BAD_REQUEST

        try:
            os.remove(image_helper.get_path(filename, folder=folder))
            return {"message": gettext("image_deleted")}, status.HTTP_200_OK
        except FileNotFoundError:
            return {
                "message": gettext("image_not_found").format(filename)
            }, status.HTTP_404_NOT_FOUND
        except:
            return {
                "message": gettext("image_delete_failed")
            }, status.HTTP_500_INTERNAL_SERVER_ERROR


class AvatarUpload(Resource):
    @classmethod
    @jwt_required
    def put(cls):
        data = image_schema.load(request.files)
        filename = f"user_{get_jwt_identity()}"
        folder = "avatars"
        avatar_path = image_helper.find_image_any_format(filename, folder)

        if avatar_path:
            try:
                os.remove(avatar_path)
            except:
                return {
                    "message": gettext("avatar_delete_failed")
                }, status.HTTP_500_INTERNAL_SERVER_ERROR

        try:
            ext = image_helper.get_extension(data["image"].filename)
            avatar = filename + ext
            avatar_path = image_helper.save_image(
                data["image"], folder=folder, name=avatar
            )
            basename = image_helper.get_basename(avatar_path)
            return {
                "message": gettext("avatar_uploaded").format(basename)
            }, status.HTTP_200_OK
        except UploadNotAllowed:
            extension = image_helper.get_extension(data["image"])
            return {
                "message": gettext("image_illegal_extension").format(extension)
            }, status.HTTP_400_BAD_REQUEST


class Avatar(Resource):
    @classmethod
    def get(cls, user_id: int):
        folder = "avatars"
        filename = f"user_{user_id}"
        avatar = image_helper.find_image_any_format(filename, folder)

        if avatar:
            return send_file(avatar)
        return {"message": gettext("avatar_not_found")}, status.HTTP_404_NOT_FOUND
