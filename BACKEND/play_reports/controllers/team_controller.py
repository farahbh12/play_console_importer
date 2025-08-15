from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction, IntegrityError
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

from play_reports.models import Client, Invitation, RoleClient, User, ClientStatus, InvitationStatus
from play_reports.serializers.team_serializer import TeamMemberSerializer
from play_reports.serializers.invitation_serializers import InvitationSerializer
from play_reports.serializers.client_serializers import ClientSerializer

class TeamInvitationController(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = request.user.client_profile
        except Client.DoesNotExist:
            return Response({'error': 'Client profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Use the existing model methods to handle the invitation logic
        can_invite, message = client.can_invite_guest()
        if not can_invite:
            return Response({'error': message}, status=status.HTTP_403_FORBIDDEN)

        success, message, invitation = client.invite_guest(email, first_name, last_name, request)

        if success:
            return Response({'message': message}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

class TeamMembersListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        print("\n--- Début de la requête TeamMembersListView ---")
        print(f"Utilisateur: {request.user}")
        try:
            # Vérifier si l'utilisateur a un profil client
            if not hasattr(request.user, 'client_profile'):
                print("ERREUR: L'utilisateur n'a pas de client_profile.")
                print("--- Fin de la requête (Erreur) ---\n")
                return Response([], status=status.HTTP_200_OK)
                
            client = request.user.client_profile
            print(f"Profil client trouvé: {client}")
            
            # Si le client n'a pas de tenant, retourner une liste vide
            if not client or not hasattr(client, 'tenant') or not client.tenant:
                print("ERREUR: Le profil client n'a pas de tenant.")
                print("--- Fin de la requête (Erreur) ---\n")
                return Response([], status=status.HTTP_200_OK)

            print(f"Tenant trouvé: {client.tenant}. Récupération des membres...")
            # Récupérer les membres actifs (clients avec utilisateurs)
            active_members = Client.objects.filter(tenant=client.tenant, user__isnull=False).select_related('user')
            active_members_data = TeamMemberSerializer(active_members, many=True).data
            print(f"Membres actifs trouvés: {len(active_members_data)}")

            # Récupérer les invitations en attente
            pending_invitations = Invitation.objects.filter(tenant=client.tenant, status=InvitationStatus.PENDING)
            pending_invitations_data = InvitationSerializer(pending_invitations, many=True).data
            print(f"Invitations en attente trouvées: {len(pending_invitations_data)}")

            # Fusionner les deux listes
            all_members_data = active_members_data + pending_invitations_data
            print(f"Données fusionnées trouvées: {len(all_members_data)} membres.")
            print("--- Fin de la requête (Succès) ---\n")
            return Response(all_members_data, status=status.HTTP_200_OK)

        except Exception as e:
            # En cas d'erreur, logger l'erreur et retourner une réponse appropriée
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in TeamMembersListView: {str(e)}", exc_info=True)
            print(f"--- Fin de la requête (Exception: {e}) ---\n")
            
            # Retourner une réponse vide plutôt qu'une erreur 500
            return Response([], status=status.HTTP_200_OK)

class CheckInvitationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            invitation = Invitation.objects.select_related('invited_client', 'tenant').get(token=token)
        except Invitation.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Lien d\'invitation invalide.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Vérifier si déjà acceptée
        if invitation.status == InvitationStatus.ACCEPTED:
            return Response({
                'valid': False,
                'error': 'Cette invitation a déjà été utilisée.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier expiration
        if invitation.is_expired:
            if invitation.status != InvitationStatus.EXPIRED:
                invitation.status = InvitationStatus.EXPIRED
                invitation.save(update_fields=['status'])
            return Response({
                'valid': False,
                'error': 'Cette invitation a expiré.'
            }, status=status.HTTP_410_GONE)

        # Invitation valide
        return Response({
            'valid': True,
            'email': invitation.email,
            'tenant_name': invitation.tenant.name if invitation.tenant else None,
            'created_at': invitation.created_at,
            'expires_at': invitation.expires_at
        }, status=status.HTTP_200_OK)


class VerifyInvitationView(APIView):
    """
    Finalise l'inscription d'un utilisateur via une invitation.
    Crée le compte utilisateur, le profil client associé, et met à jour l'invitation.
    """
    permission_classes = [AllowAny]

    def post(self, request, token):
        password = request.data.get('password')
        if not password or len(password) < 8:
            return Response(
                {'detail': 'Le mot de passe est requis et doit contenir au moins 8 caractères.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            invitation = Invitation.objects.select_related('tenant').get(
                token=token,
                status=InvitationStatus.PENDING
            )
        except Invitation.DoesNotExist:
            return Response(
                {'detail': 'Lien d\'invitation invalide ou déjà utilisé.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.is_expired:
            invitation.status = InvitationStatus.EXPIRED
            invitation.save()
            return Response(
                {'detail': 'L\'invitation a expiré.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # 1) Déterminer les noms et créer l'utilisateur avec first_name/last_name
                req_first_name = request.data.get('first_name')
                req_last_name = request.data.get('last_name')

                invited_client_first = invitation.invited_client.first_name if invitation.invited_client else None
                invited_client_last = invitation.invited_client.last_name if invitation.invited_client else None

                first_name = (req_first_name or invited_client_first or invitation.email.split('@')[0]).strip()
                last_name = (req_last_name or invited_client_last or '').strip()

                user = User.objects.create_user(
                    email=invitation.email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )

                # 2) Lier cet utilisateur au client invité existant en conservant son rôle de membre invité
                if invitation.invited_client:
                    client = invitation.invited_client
                    client.user = user
                    client.status = ClientStatus.ACTIVE
                    # Conserver le rôle existant, sinon définir comme MEMBRE_INVITE
                    if not client.role_client:
                        client.role_client = RoleClient.MEMBRE_INVITE
                    # Synchroniser les noms si manquants côté Client
                    client_first = client.first_name.strip() if client.first_name else ''
                    client_last = client.last_name.strip() if client.last_name else ''
                    fields_to_update = ['user', 'status', 'role_client', 'updated_at']
                    if not client_first and first_name:
                        client.first_name = first_name
                        fields_to_update.append('first_name')
                    if not client_last and last_name:
                        client.last_name = last_name
                        fields_to_update.append('last_name')
                    client.save(update_fields=fields_to_update)
                else:
                    # Filet de sécurité: créer un client membre invité si absent
                    client = Client.objects.create(
                        user=user,
                        tenant=invitation.tenant,
                        first_name=first_name,
                        last_name=last_name,
                        status=ClientStatus.ACTIVE,
                        role_client=RoleClient.MEMBRE_INVITE
                    )

                # 3) Marquer l'invitation comme acceptée
                invitation.status = InvitationStatus.ACCEPTED
                invitation.invited_client = client
                invitation.save(update_fields=['status', 'invited_client', 'updated_at'])

                # 4) Générer les jetons pour connecter l'utilisateur immédiatement
                refresh = RefreshToken.for_user(user)

                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': client.first_name,
                        'last_name': client.last_name,
                        'role': client.role_client  # Renvoyer le rôle au frontend
                    }
                }, status=status.HTTP_200_OK)

        except IntegrityError:
            return Response(
                {'detail': 'Un utilisateur avec cet email existe déjà.'},
                status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            print(f"Erreur inattendue lors de la vérification de l'invitation : {e}")
            return Response(
                {'detail': 'Une erreur de serveur inattendue est survenue.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )