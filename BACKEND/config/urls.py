from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from play_reports.controllers.gcs_controlleur import (
    validate_gcs_uri,
    validation_success,
    trigger_gcs_sync,
    get_data_source_details,
    display_gcs_files,
)

from play_reports.controllers.auth_controller import (
    PasswordResetController,
    PasswordResetConfirmController,
    oauth_redirect,
    ActivateClientAccountController,
    ClientRegisterController,
    ClientLoginController,
    EmployeeRegisterController,
    EmployeeLoginController,
)

from play_reports.controllers.abonnement_controller import (
    AbonnementListView,
    AbonnementDetailView,
    AbonnementToggleActiveView,
    AbonnementUpdateRequestView,
    ClientSubscriptionView,
    ClientSubscriptionDetailView
)

from play_reports.controllers.team_controller import (
    TeamInvitationController,
    TeamMembersListView,
    VerifyInvitationView,
    CheckInvitationView
)

from play_reports.controllers.employee_controller import (
    EmployeeListView,
    EmployeeDetailController,
    EmployeeUpdateView,
    EmployeeDeactivateController,
    EmployeeActivateController
)

from play_reports.controllers.client_controller import (
    ClientProfileView,
    ClientUpdateController, 
    ClientDeactivateController, 
    ClientActivateController,
    ClientListController, 
    ClientDetailController, 
    set_client_status, 
    ClientChangeAbonnementView,
    
)

from play_reports.controllers.looker_community_controller import (
    LookerConnectorView,
    DebugTableStructureView
)

from play_reports.controllers.insights_controller import (
    installs_insights,
    packages_list,
     reviews_insights,
    crashes_insights,
    ratings_insights,
    ai_analysis
)

urlpatterns = [
    # Manually added URL patterns that were in the deleted file
    path('api/client/activate-account/', ActivateClientAccountController.as_view(), name='client-activate-account'),

    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # GCS Management
    path('data-source-details/', get_data_source_details, name='get_data_source_details'),
    path('trigger-gcs-sync/', trigger_gcs_sync, name='trigger_gcs_sync'),
    path('validate-gcs-uri/', validate_gcs_uri, name='validate_gcs_uri'),
    path('validation-success/', validation_success, name='validation-success'),
    path('display-gcs-files/', display_gcs_files, name='display-gcs-files'),
# gestion membre
    path('team/invite/', TeamInvitationController.as_view(), name='team-invite'),
    path('team/members/', TeamMembersListView.as_view(), name='team-members-list'),
    path('team/verify-invitation/<str:token>/', VerifyInvitationView.as_view(), name='verify-invitation'),
    path('team/check-invitation/<str:token>/', CheckInvitationView.as_view(), name='check-invitation'),
    # Authentication
    path('client/register/', ClientRegisterController.as_view(), name='client_register'),
    path('client/login/', ClientLoginController.as_view(), name='client_login'),
    path('employee/register/', EmployeeRegisterController.as_view(), name='employee_register'),
    path('employee/login/', EmployeeLoginController.as_view(), name='employee_login'),
    path('password-reset/', PasswordResetController.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         PasswordResetConfirmController.as_view(),
         name='password_reset_confirm'),
    path('oauth/redirect/', oauth_redirect, name='oauth_redirect'),

    # Subscription management
    path('abonnements/', AbonnementListView.as_view(), name='abonnement_list'),
    path('abonnements/<int:pk>/', AbonnementDetailView.as_view(), name='abonnement-detail'),
    path('abonnements/<int:pk>/toggle-active/', AbonnementToggleActiveView.as_view(), name='abonnement-toggle-active'),
    path('abonnements/update-request/', AbonnementUpdateRequestView.as_view(), name='abonnement-update-request'),
    
    # Client subscription endpoints
    path('client/subscribe/', ClientSubscriptionView.as_view(), name='client_subscribe'),
    path('clients/<int:client_id>/subscription/', ClientSubscriptionDetailView.as_view(), name='client_subscription_detail'),

    path('clients/<int:user_id>/subscription/', ClientSubscriptionView.as_view(), name='client-subscription'),
    path('client/subscribe/', ClientSubscriptionView.as_view(), name='client_subscribe'),
    # Team management
    path('api/team/invite/', TeamInvitationController.as_view(), name='team-invite'),
    path('api/team/members/', TeamMembersListView.as_view(), name='team-members-list'),
    path('api/team/check-invitation/<str:token>/', CheckInvitationView.as_view(), name='check-invitation'),
    path('api/team/verify-invitation/<str:token>/', VerifyInvitationView.as_view(), name='verify-invitation'),
    
    # Gestion des abonnements
    path('abonnements/<int:pk>/toggle/', AbonnementToggleActiveView.as_view(), name='abonnement-toggle'),

    # Employee endpoints
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:pk>/', EmployeeDetailController.as_view(), name='employee-detail'),
    path('employees/<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee-update'),
    path('api/employees/<int:pk>/deactivate/', EmployeeDeactivateController.as_view(), name='employee-deactivate'),
    path('api/employees/<int:pk>/activate/', EmployeeActivateController.as_view(), name='employee-activate'),
    
    # Endpoint pour la liste des employés (compatible avec le frontend)
    path('api/employees/', EmployeeListView.as_view(), name='api-employee-list'),

    # Client endpoints
    path('api/clients/', ClientListController.as_view(), name='client-list'),
    path('clients/<int:pk>/', ClientDetailController.as_view(), name='client-detail'),
    path('clients/me/', ClientProfileView.as_view(), name='client-profile'),
    path('clients/<int:pk>/update/', ClientUpdateController.as_view(), name='client_update'),    
    path('clients/<int:pk>/deactivate/', ClientDeactivateController.as_view(), name='client_deactivate'),
    path('clients/<int:pk>/activate/', ClientActivateController.as_view(), name='client_activate'),
    # Ajout des endpoints API avec préfixe /api/
    path('api/clients/<int:pk>/deactivate/', ClientDeactivateController.as_view(), name='api_client_deactivate'),
    path('api/clients/<int:pk>/activate/', ClientActivateController.as_view(), name='api_client_activate'),
    path('clients/<int:user_id>/set-status/', set_client_status, name='set_client_status'),
    path('clients/<int:user_id>/change-abonnement/', ClientChangeAbonnementView.as_view(), name='client_change_abonnement'),
    # Liste des clients avec leurs abonnements

    # Abonnements
    path('abonnements/<int:pk>/', AbonnementDetailView.as_view(), name='abonnement-detail'),
    path('abonnements/<int:pk>/toggle-active/', AbonnementToggleActiveView.as_view(), name='abonnement-toggle-active'),
    path('abonnements/update-request/', AbonnementUpdateRequestView.as_view(), name='abonnement-update-request'),
    path('client/subscribe/', ClientSubscriptionView.as_view(), name='client-subscribe'),

    # Endpoints pour le connecteur Looker
     path('api/looker-connector/', LookerConnectorView.as_view(), name='looker_connector'),
    path('api/looker-connector/<str:table_name>/', LookerConnectorView.as_view(), name='looker_connector_table'),
    path('api/looker-community/health', lambda r: JsonResponse({'status': 'healthy'}), name='looker-community-health'),
    path('api/looker-community/<str:table_name>/', LookerConnectorView.as_view(), name='looker_connector_table'),
    
    # Endpoint de débogage
    path('api/debug/table-structure/<str:table_name>/', DebugTableStructureView.as_view(), name='debug_table_structure'),
    
    # Insights endpoints
    path('insights/packages', packages_list, name='insights_packages'),
    path('insights/packages/', packages_list, name='insights_packages_slash'),
   
    path('insights/installs', installs_insights, name='insights_installs'),
    path('insights/installs/', installs_insights, name='insights_installs_slash'),
 
    path('insights/reviews', reviews_insights, name='insights_reviews'),
    path('insights/reviews/', reviews_insights, name='insights_reviews_slash'),
    
    path('insights/crashes', crashes_insights, name='insights_crashes'),
    path('insights/crashes/', crashes_insights, name='insights_crashes_slash'),
    
    path('insights/ratings', ratings_insights, name='insights_ratings'),
    path('insights/ratings/', ratings_insights, name='insights_ratings_slash'),
    
    path('insights/ai_analysis', ai_analysis, name='insights_ai_analysis'),
    path('insights/ai_analysis/', ai_analysis, name='insights_ai_analysis_slash'),

    # Temporary diagnostics
    path('insights/ping', lambda request: JsonResponse({'success': True, 'message': 'insights URLConf loaded'}), name='insights_ping'),
    path('insights/ping/', lambda request: JsonResponse({'success': True, 'message': 'insights URLConf loaded (slash)'}), name='insights_ping_slash'),
]