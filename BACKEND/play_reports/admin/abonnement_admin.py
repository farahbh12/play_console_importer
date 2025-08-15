from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from ..models import DemandeChangementAbonnement

@admin.register(DemandeChangementAbonnement)
class DemandeChangementAbonnementAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_info', 'ancien_abonnement_display', 'nouvel_abonnement_display', 
                   'statut_display', 'date_demande_formatted', 'actions_column')
    list_filter = ('statut', 'date_demande', 'nouvel_abonnement')
    search_fields = ('client__first_name', 'client__last_name', 'client__email')
    list_per_page = 20
    date_hierarchy = 'date_demande'
    readonly_fields = ('date_demande', 'date_traitement', 'traite_par')
    fieldsets = (
        ('Informations de la demande', {
            'fields': ('client', 'ancien_abonnement', 'nouvel_abonnement', 'statut')
        }),
        ('Traitement', {
            'fields': ('traite_par', 'date_traitement', 'commentaire'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_demande',),
            'classes': ('collapse',)
        }),
    )

    def client_info(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name} ({obj.client.email})"
    client_info.short_description = 'Client'
    client_info.admin_order_field = 'client__last_name'

    def ancien_abonnement_display(self, obj):
        return obj.ancien_abonnement.get_type_abonnement_display() if obj.ancien_abonnement else 'Aucun'
    ancien_abonnement_display.short_description = 'Ancien abonnement'
    ancien_abonnement_display.admin_order_field = 'ancien_abonnement__type_abonnement'

    def nouvel_abonnement_display(self, obj):
        return obj.nouvel_abonnement.get_type_abonnement_display()
    nouvel_abonnement_display.short_description = 'Nouvel abonnement demandé'
    nouvel_abonnement_display.admin_order_field = 'nouvel_abonnement__type_abonnement'

    def statut_display(self, obj):
        statut_colors = {
            'EN_ATTENTE': 'orange',
            'APPROUVEE': 'green',
            'REJETEE': 'red'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            statut_colors.get(obj.statut, 'black'),
            obj.get_statut_display()
        )
    statut_display.short_description = 'Statut'
    statut_display.admin_order_field = 'statut'

    def date_demande_formatted(self, obj):
        return obj.date_demande.strftime('%d/%m/%Y %H:%M')
    date_demande_formatted.short_description = 'Date de la demande'
    date_demande_formatted.admin_order_field = 'date_demande'

    def actions_column(self, obj):
        if obj.statut == 'EN_ATTENTE':
            approve_url = reverse('admin:approve_abonnement', args=[obj.id])
            reject_url = reverse('admin:reject_abonnement', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" style="background: green; color: white; padding: 5px 10px; margin-right: 5px;">Approuver</a>'
                '<a class="button" href="{}" style="background: red; color: white; padding: 5px 10px;">Rejeter</a>',
                approve_url, reject_url
            )
        return ''
    actions_column.short_description = 'Actions'
    actions_column.allow_tags = True

    def save_model(self, request, obj, form, change):
        if 'statut' in form.changed_data and obj.statut != 'EN_ATTENTE':
            obj.traite_par = request.user
            obj.date_traitement = timezone.now()
            
            if obj.statut == 'APPROUVEE' and obj.client:
                obj.client.abonnement = obj.nouvel_abonnement
                obj.client.save()
        
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'client', 'ancien_abonnement', 'nouvel_abonnement', 'traite_par'
        )
