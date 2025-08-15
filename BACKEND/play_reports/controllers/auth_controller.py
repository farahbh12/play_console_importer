from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError

from play_reports.serializers.auth_serializers import (
    EmployeeRegisterSerializer,
    ClientRegisterSerializer,
    EmployeeLoginSerializer,
    ClientLoginSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)
from play_reports.services.auth_service import AuthService


class EmployeeRegisterController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmployeeRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                AuthService.register_employee(serializer.validated_data)
                return Response({"message": "Inscription réussie."}, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientRegisterController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ClientRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                client = AuthService.register_client(serializer.validated_data)
                return Response({
                    "message": "Client enregistré avec succès.",
                    "client_id": client.id,
                    "email": client.user.email,
                    "role": client.role_client
                }, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeLoginController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmployeeLoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                response_data = AuthService.login_employee(**serializer.validated_data)
                return Response(response_data, status=status.HTTP_200_OK)
            except ValidationError as e:
                detail = e.detail
                if isinstance(detail, dict):
                    return Response(detail, status=status.HTTP_401_UNAUTHORIZED)
                return Response({"non_field_errors": detail}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientLoginController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ClientLoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                response_data = AuthService.login_client(**serializer.validated_data)
                return Response(response_data, status=status.HTTP_200_OK)
            except ValidationError as e:
                detail = e.detail
                if isinstance(detail, dict):
                    return Response(detail, status=status.HTTP_401_UNAUTHORIZED)
                return Response({"non_field_errors": detail}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            AuthService.send_password_reset_email(serializer.validated_data['email'])
            return Response({'message': 'E-mail de réinitialisation envoyé.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmController(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                AuthService.confirm_password_reset(uidb64, token, serializer.validated_data['new_password'])
                return Response({'message': 'Mot de passe mis à jour.'}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
