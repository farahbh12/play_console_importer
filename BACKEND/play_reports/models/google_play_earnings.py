from django.db import models

class google_play_earnings(models.Model):
    # Types de transactions
    TAX_TYPES = [
        ('VAT', 'VAT'),
        ('GST', 'GST'),
        ('HST', 'HST'),
        ('PST', 'PST'),
        ('QST', 'QST'),
        ('RST', 'RST'),
        ('JCT', 'JCT'),
        ('SST', 'SST'),
    ]

    TRANSACTION_TYPES = [
        ('sale', 'Sale'),
        ('refund', 'Refund'),
        ('chargeback', 'Chargeback'),
        ('chargeback_reversal', 'Chargeback Reversal'),
        ('tax_reversal', 'Tax Reversal'),
    ]

    # Informations de transaction
    transaction_date = models.DateField(db_index=True)
    transaction_time = models.TimeField()
    transaction_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    refund_type = models.CharField(max_length=100, blank=True, null=True)

    # Informations sur le produit
    product_title = models.CharField(max_length=255)
    product_id = models.CharField(max_length=100, db_index=True)
    product_type = models.CharField(max_length=50)  # Peut être un IntegerField selon les besoins
    sku_id = models.CharField(max_length=100, db_index=True)
    hardware = models.CharField(max_length=100, blank=True, null=True)

    # Informations sur l'acheteur
    buyer_country = models.CharField(max_length=10, db_index=True)
    buyer_state = models.CharField(max_length=50, blank=True, null=True)
    buyer_postcode = models.CharField(max_length=20, blank=True, null=True)

    # Montants et devises
    buyer_currency = models.CharField(max_length=10)
    amount_buyer_currency = models.DecimalField(max_digits=15, decimal_places=2)
    merchant_currency = models.CharField(max_length=10)
    amount_merchant_currency = models.DecimalField(max_digits=15, decimal_places=2)
    currency_conversion_rate = models.DecimalField(max_digits=10, decimal_places=5)

    # Taxes et frais
    tax_type = models.CharField(max_length=10, choices=TAX_TYPES, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    service_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    service_fee_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Abonnements et offres
    base_plan_id = models.CharField(max_length=100, blank=True, null=True)
    offer_id = models.CharField(max_length=100, blank=True, null=True)
    group_id = models.CharField(max_length=100, blank=True, null=True)

    # Promotions et remises
    promotion_id = models.CharField(max_length=100, blank=True, null=True)
    first_usd_1m_eligible = models.BooleanField(null=True, blank=True)

    # Métadonnées
    description = models.TextField(blank=True, null=True)
    fee_description = models.CharField(max_length=255, blank=True, null=True)

    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='earnings',
        db_index=True
    )

    # Horodatages
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_earnings'
        verbose_name = "Google Play Earning"
        verbose_name_plural = "Google Play Earnings"
        unique_together = (
            'tenant',
            'transaction_date',
            'transaction_time',
            'product_id',
            'buyer_country',
            'sku_id',
            'amount_buyer_currency'
        )
        indexes = [
            models.Index(fields=['tenant', 'transaction_date']),
            models.Index(fields=['product_id', 'transaction_date']),
            models.Index(fields=['buyer_country', 'transaction_date']),
            models.Index(fields=['transaction_type', 'transaction_date']),
            models.Index(fields=['sku_id']),
        ]
        ordering = ['-transaction_date', '-transaction_time']

    def save(self, *args, **kwargs):
        # Créer un champ datetime combiné pour faciliter les requêtes
        if self.transaction_date and self.transaction_time:
            self.transaction_datetime = f"{self.transaction_date} {self.transaction_time}"
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Earning {self.product_id} - {self.amount_merchant_currency} {self.merchant_currency} - "
            f"{self.transaction_date} - {self.transaction_type}"
        )