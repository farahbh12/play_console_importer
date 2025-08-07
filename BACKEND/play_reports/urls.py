from django.urls import path
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

from play_reports.controllers.looker_studio_controller import (
    TableListView,
    TableSchemaView,
    TableDataView,
    TestAuthView,
)

from play_reports.controllers.auth_controller import (
    PasswordResetController,
    PasswordResetConfirmController,
    ClientRegisterController,
    ClientLoginController,
    EmployeeRegisterController,
    EmployeeLoginController,
)

from play_reports.controllers.employee_controller import (
    EmployeeListView,
    EmployeeDetailController,
    EmployeeUpdateView,
    EmployeeDeactivateController,
    EmployeeActivateController,
)

from play_reports.controllers.abonnement_controller import (
    AbonnementListView,
    AbonnementDetailView,
    AbonnementToggleActiveView,
    ClientSubscriptionView,
)

from play_reports.controllers.client_controller import (
    ClientListController,
    ClientDetailController,
    ClientUpdateController,
    ClientDeactivateController,
    ClientActivateController,
    set_client_status
)

urlpatterns = [
    # ... (toutes vos autres routes restent ici)

    # Gestion des données GCS
    path('data-source-details/', get_data_source_details, name='get_data_source_details'),
    path('trigger-gcs-sync/', trigger_gcs_sync, name='trigger_gcs_sync'),
    path('validate-gcs-uri/', validate_gcs_uri, name='validate_gcs_uri'),
    path('gcs/upload-success/', validation_success, name='gcs_upload_success'),
    path('gcs/upload-success/<str:folder_name>/', validation_success, name='gcs_upload_success_folder'),

    # URLs pour le connecteur Looker Studio
    path('looker-studio/tables/', TableListView.as_view(), name='looker_studio_tables'),
    path('looker-studio/tables/<str:table_name>/schema/', TableSchemaView.as_view(), name='looker_studio_schema'),
    path('looker-studio/tables/<str:table_name>/data/', TableDataView.as_view(), name='looker_studio_data'),
    path('looker-studio/test-auth/', TestAuthView.as_view(), name='looker_studio_test_auth'),

    # Authentification JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Authentification utilisateurs
    path('client/register/', ClientRegisterController.as_view(), name='client_register'),
    path('client/login/', ClientLoginController.as_view(), name='client_login'),
    path('employee/register/', EmployeeRegisterController.as_view(), name='employee_register'),
    path('employee/login/', EmployeeLoginController.as_view(), name='employee_login'),
    path('password-reset/', PasswordResetController.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         PasswordResetConfirmController.as_view(),
         name='password_reset_confirm'),

    # Gestion des abonnements
    path('abonnements/', AbonnementListView.as_view(), name='abonnement_list'),
    path('abonnements/<int:abonnement_id>/', AbonnementDetailView.as_view(), name='abonnement_detail'),
    path('abonnements/<int:abonnement_id>/toggle/', AbonnementToggleActiveView.as_view(), name='abonnement_toggle'),
    path('client/subscribe/', ClientSubscriptionView.as_view(), name='client_subscribe'),

    # Gestion des clients
    path('clients/', ClientListController.as_view(), name='client_list'),
    path('clients/<int:pk>/', ClientDetailController.as_view(), name='client_detail'),
    path('clients/<int:pk>/update/', ClientUpdateController.as_view(), name='client_update'),    
    path('clients/<int:pk>/deactivate/', ClientDeactivateController.as_view(), name='client_deactivate'),
    path('clients/<int:pk>/activate/', ClientActivateController.as_view(), name='client_activate'),
    path('clients/<int:user_id>/set-status/', set_client_status, name='set_client_status'),

    # Gestion des employés
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/<int:pk>/', EmployeeDetailController.as_view(), name='employee_detail'),
    path('employees/<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/<int:pk>/deactivate/', EmployeeDeactivateController.as_view(), name='employee_deactivate'),
    path('employees/<int:pk>/activate/', EmployeeActivateController.as_view(), name='employee_activate'),


 
]