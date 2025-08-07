from django.db import models
from django.core.validators import MinValueValidator

class play_balance_krw(models.Model):
    """
    Modèle représentant les transactions de solde Play en KRW (Won coréen).
    Correspond aux fichiers play_balance_krw_*.csv
    """
    
    # Types de statuts financiers
    FINANCIAL_STATUS_CHOICES = [
        ('CHARGED', 'Chargé'),
        ('REFUNDED', 'Remboursé'),
        ('PENDING', 'En attente'),
        ('CANCELLED', 'Annulé'),
        ('VOIDED', 'Annulé (remboursé)'),
    ]

    # Informations de base
    order_number = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Format: GPA.XXXX-XXXX-XXXX-XXXXX ou GPA.XXXX-XXXX-XXXX-XXXXX..N"
    )
    
    billing_date = models.DateField(
        db_index=True,
        help_text="Date de la transaction au format YYYY-MM-DD (UTC)"
    )
    
    financial_status = models.CharField(
        max_length=20,
        choices=FINANCIAL_STATUS_CHOICES,
        db_index=True,
        help_text="Statut financier de la transaction"
    )
    
    # Montants et devises
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Montant de la transaction"
    )
    
    currency = models.CharField(
        max_length=3,
        default="KRW",
        help_text="Devise de la transaction (toujours KRW)"
    )
    
    # Horodatage
    billing_timestamp = models.BigIntegerField(
        db_index=True,
        help_text="Horodatage UNIX de la transaction"
    )
    
    # Informations supplémentaires
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="ID de transaction Google"
    )
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='krw_balances',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date de traitement de la transaction"
    )

    class Meta:
        db_table = 'google_play_krw_balance'
        verbose_name = "Solde KRW Google Play"
        verbose_name_plural = "Soldes KRW Google Play"
        ordering = ['-billing_date', '-billing_timestamp']
        unique_together = ('tenant', 'order_number', 'billing_timestamp')
        indexes = [
            models.Index(fields=['tenant', 'billing_date']),
            models.Index(fields=['financial_status', 'billing_date']),
            models.Index(fields=['amount']),
        ]