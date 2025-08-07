from django.contrib.auth import  get_user_model
from django.contrib.auth.tokens import  PasswordResetTokenGenerator
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken



from play_reports.serializers.serializers import (
    EmployeeRegisterSerializer,
    ClientRegisterSerializer,
    EmployeeLoginSerializer,
    ClientLoginSerializer,
    EmployeeTokenObtainPairResponseSerializer,
    ClientTokenObtainPairResponseSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)


UserModel = get_user_model()

class EmployeeRegisterController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("Données reçues pour l'inscription employé:", request.data)  # Log des données reçues
        serializer = EmployeeRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({"message": "Inscription réussie."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                print("Erreur lors de la création de l'employé:", str(e))  # Log de l'erreur
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        print("Erreurs de validation:", serializer.errors)  # Log des erreurs de validation
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientRegisterController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Créer une copie des données pour éviter de modifier l'original
        data = request.data.copy()
        
        # ✅ NE PAS retirer first_name et last_name ici
        data.pop('type_abonnement', None)  # ok si non utilisé

        serializer = ClientRegisterSerializer(data=data)
        if serializer.is_valid():
            client = serializer.save()
            return Response({
                "message": "Client enregistré avec succès.",
                "client_id": client.id,
                "email": client.user.email,
                "role": client.role_client
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmployeeLoginController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("Données reçues pour la connexion employé:", request.data)
        serializer = EmployeeLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            print("Erreurs de validation:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.validated_data['user']
            employee = serializer.validated_data['employee']
            
            # Vérifier si l'utilisateur est actif
            if not user.is_active:
                return Response(
                    {"non_field_errors": ["Ce compte est désactivé."]}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            
            # Préparer la réponse
            response_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_type': 'employee',
                    'role': employee.role_employe,
                    'is_superuser': user.is_superuser,
                }
            }
            
            print(f"Connexion réussie pour l'employé {user.email}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Erreur lors de la connexion de l'employé: {str(e)}")
            return Response(
                {"non_field_errors": ["Une erreur est survenue lors de la connexion."]}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClientLoginController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ClientLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        client = serializer.validated_data['client']

        # Mettre à jour la dernière connexion
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Générer le token JWT
        refresh = RefreshToken.for_user(user)

        # Préparer les données de réponse (sans first_name/last_name)
        response_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': client.id,
                'email': user.email,
                'user_type': 'client',
                'role': client.role_client,
                'is_active': user.is_active,
                'last_login': user.last_login,
                'tenant_id': client.tenant.id if client.tenant else None,
            }
        }

        response_serializer = ClientTokenObtainPairResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.validated_data, status=status.HTTP_200_OK)

        
       

class PasswordResetController(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = UserModel.objects.get(email=email)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = PasswordResetTokenGenerator().make_token(user)
                reset_link = f"{settings.FRONTEND_URL}/reset-password-confirm/?uid={uid}&token={token}"

                send_mail(
                    subject="Réinitialisation de votre mot de passe",
                    message=f"Bonjour,\n\nVoici le lien pour réinitialiser votre mot de passe : {reset_link}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                )
            except UserModel.DoesNotExist:
                pass  # Ne révèle pas l'existence de l'utilisateur

            return Response({'message': 'E-mail de réinitialisation envoyé.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmController(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        # Combine URL parameters with request body for the serializer
        data = {
            'new_password': request.data.get('new_password'),
            'uidb64': uidb64,
            'token': token
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Mot de passe mis à jour.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
