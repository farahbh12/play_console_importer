from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # The simple-jwt serializer uses the 'username' field for the email.
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        except MultipleObjectsReturned:
            # In case of multiple users with the same email, return the first one.
            # This should ideally not happen if the email field is unique.
            return UserModel.objects.filter(email=username).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
