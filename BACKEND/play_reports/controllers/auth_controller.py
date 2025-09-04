from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from urllib.parse import urlparse

from play_reports.models import Client, Abonnement, User
from play_reports.serializers.abonnement_serializers import AbonnementSerializer

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
                # On délègue la logique à AuthService.login_client
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


class ActivateClientAccountController(APIView):
    """
    Handles client account activation after subscription selection.
    This endpoint is called after a client selects a subscription plan.
    """
    permission_classes = [AllowAny]  # Allow unauthenticated access for activation

    def post(self, request):
        client_id = request.data.get('user_id') # This is actually client_id
        subscription_type = request.data.get('subscription_type')
        
        if not client_id or not subscription_type:
            return Response(
                {"error": "client_id and subscription_type are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the client by its primary key
            client = get_object_or_404(Client, pk=client_id)

            # Get or create the subscription
            abonnement, created = Abonnement.objects.get_or_create(
                type_abonnement=subscription_type,
                defaults={'is_active': True}
            )
            
            # Update client's subscription
            client.abonnement = abonnement
            client.save()
            
            # Activate the user account if not already active
            if not client.user.is_active:
                client.user.is_active = True
                client.user.save()
            
            # Serialize the subscription for the response
            serializer = AbonnementSerializer(abonnement)
            
            return Response({
                "message": "Account activated successfully",
                "subscription": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error in account activation: {str(e)}")
            return Response(
                {"error": f"Account activation failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# --- OAuth Redirect helper for Apps Script / Looker Studio ---
def oauth_redirect(request):
    """
    Simple endpoint to complete an OAuth/login popup by redirecting the user
    back to the URL provided by Google Apps Script/Looker Studio via
    the `redirect_uri` query parameter.

    Usage:
      GET /oauth/redirect/?redirect_uri=<encoded-url>

    Optionally forwards through extra query parameters like `state` and `code` if provided.
    """
    redirect_uri = request.GET.get('redirect_uri') or request.POST.get('redirect_uri')
    if not redirect_uri:
        return HttpResponseBadRequest('Missing redirect_uri')

    # Minimal safety check: only allow http(s) schemes
    parsed = urlparse(redirect_uri)
    if parsed.scheme not in ('http', 'https'):
        return HttpResponseBadRequest('Invalid redirect_uri scheme')

    # If state/code are present, append them to the redirect target
    params = []
    state = request.GET.get('state') or request.POST.get('state')
    code = request.GET.get('code') or request.POST.get('code')
    if state:
        params.append(f"state={state}")
    if code:
        params.append(f"code={code}")

    target = redirect_uri
    if params:
        sep = '&' if ('?' in redirect_uri) else '?'
        target = f"{redirect_uri}{sep}{'&'.join(params)}"

    return redirect(target)
