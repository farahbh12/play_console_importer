from django.db import models

class google_play_invoice(models.Model):
    # Types de transactions
    TRANSACTION_TYPES = [
        ('sale', 'Sale'),
        ('refund', 'Refund'),
        ('chargeback', 'Chargeback'),
        ('reversal', 'Reversal'),
    ]

    # Types de SKU
    SKU_TYPES = [
        ('inapp', 'In-app Product'),
        ('subs', 'Subscription'),
        ('one_time', 'One-time Purchase'),
    ]

    # Types de taxes
    TAX_TYPES = [
        ('VAT', 'VAT'),
        ('GST', 'GST'),
        ('HST', 'HST'),
        ('PST', 'PST'),
        ('QST', 'QST'),
        ('RST', 'RST'),
        ('JCT', 'JCT'),
        ('SST', 'SST'),
        ('none', 'No Tax'),
    ]

    # Informations de facturation
    invoice_id = models.CharField(max_length=50, db_index=True)
    program = models.CharField(max_length=50, blank=True, null=True)
    external_transaction_id = models.CharField(max_length=100, db_index=True)
    
    # Dates et horodatages
    transaction_date = models.DateField(db_index=True)
    transaction_time = models.TimeField()
    transaction_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    transaction_timestamp = models.BigIntegerField(db_index=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    
    # Informations sur le produit
    sku_type = models.CharField(max_length=20, choices=SKU_TYPES)
    package_id = models.CharField(max_length=100, db_index=True)
    sale_country = models.CharField(max_length=5, db_index=True)
    
    # Montants et devises
    item_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    sale_currency = models.CharField(max_length=5)
    amount_due_sale_currency = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6)
    billing_currency = models.CharField(max_length=5)
    amount_due_billing_currency = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Taxes
    tax_type = models.CharField(max_length=10, choices=TAX_TYPES, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Frais et remises
    group_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    first_million_eligible = models.BooleanField(null=True, blank=True)
    service_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    service_fee_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    fee_description = models.CharField(max_length=100, blank=True, null=True)
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='invoices',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_invoice'
        verbose_name = "Google Play Invoice"
        verbose_name_plural = "Google Play Invoices"
        unique_together = (
            'tenant',
            'invoice_id',
            'external_transaction_id',
            'transaction_timestamp'
        )
        indexes = [
            models.Index(fields=['tenant', 'transaction_date']),
            models.Index(fields=['package_id', 'transaction_date']),
            models.Index(fields=['sale_country', 'transaction_date']),
            models.Index(fields=['transaction_type', 'transaction_date']),
            models.Index(fields=['sku_type']),
            models.Index(fields=['billing_currency']),
        ]
        ordering = ['-transaction_date', '-transaction_time']

    def save(self, *args, **kwargs):
        # Créer un champ datetime combiné pour faciliter les requêtes
        if self.transaction_date and self.transaction_time:
            self.transaction_datetime = f"{self.transaction_date} {self.transaction_time}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_id} - {self.get_transaction_type_display()} - {self.amount_due_billing_currency} {self.billing_currency}"