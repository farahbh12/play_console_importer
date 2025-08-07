from django.db import models

class google_play_sales(models.Model):
    # Types de produits
    PRODUCT_TYPES = [
        ('inapp', 'In-app Purchase'),
        ('subs', 'Subscription'),
        ('subs_cancel', 'Subscription Canceled'),
        ('subs_pause', 'Subscription Paused'),
        ('subs_defer', 'Subscription Deferred'),
        ('subs_revoked', 'Subscription Revoked'),
        ('subs_renewed', 'Subscription Renewed'),
    ]

    # Statuts financiers
    FINANCIAL_STATUSES = [
        ('charged', 'Charged'),
        ('refunded', 'Refunded'),
        ('voided', 'Voided'),
        ('pending', 'Pending'),
        ('charged_but_not_shown', 'Charged but Not Shown'),
    ]

    # Informations de commande
    order_number = models.CharField(max_length=100, db_index=True)
    billing_date = models.DateField(db_index=True)
    billing_timestamp = models.BigIntegerField(db_index=True)
    financial_status = models.CharField(max_length=30, choices=FINANCIAL_STATUSES)

    # Informations produit
    device_model = models.CharField(max_length=100, blank=True, null=True)
    product_title = models.CharField(max_length=255)
    package_id = models.CharField(max_length=100, db_index=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    product_id = models.CharField(max_length=100, db_index=True)

    # Informations financières
    sale_currency = models.CharField(max_length=5)
    item_price = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    charged_amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Informations acheteur
    buyer_city = models.CharField(max_length=100, null=True, blank=True)
    buyer_state = models.CharField(max_length=50, null=True, blank=True)
    buyer_postal_code = models.CharField(max_length=20, null=True, blank=True)
    buyer_country = models.CharField(max_length=5, db_index=True)

    # Abonnements
    subscription_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    base_plan_id = models.CharField(max_length=100, null=True, blank=True)
    offer_id = models.CharField(max_length=100, null=True, blank=True)

    # Regroupement
    group_id = models.CharField(max_length=100, null=True, blank=True)
    first_million_eligible = models.BooleanField(null=True, blank=True)

    # Promotions
    promotion_id = models.CharField(max_length=100, null=True, blank=True)
    coupon_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Autres
    featured_products_id = models.CharField(max_length=100, null=True, blank=True)
    price_experiment_id = models.CharField(max_length=100, null=True, blank=True)

    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='sales',
        db_index=True
    )

    # Métadonnées automatiques
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_sales'
        verbose_name = "Google Play Sale"
        verbose_name_plural = "Google Play Sales"
        unique_together = ('tenant', 'order_number', 'billing_timestamp')
        indexes = [
            models.Index(fields=['tenant', 'billing_date']),
            models.Index(fields=['product_type']),
            models.Index(fields=['financial_status']),
            models.Index(fields=['package_id', 'billing_date']),
            models.Index(fields=['product_id', 'billing_date']),
        ]
        ordering = ['-billing_date', '-billing_timestamp']

    def __str__(self):
        return f"Sale {self.order_number} - {self.product_title} ({self.charged_amount} {self.sale_currency})"