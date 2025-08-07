from django.db import models

class google_play_estimatedSales(models.Model):
    order_number = models.CharField(max_length=255)
    order_charged_date = models.DateField()
    order_charged_timestamp = models.BigIntegerField()
    financial_status = models.CharField(max_length=255)
    device_model = models.CharField(max_length=255)
    product_title = models.CharField(max_length=255)
    product_id = models.CharField(max_length=255)
    product_type = models.CharField(max_length=255)
    sku_id = models.CharField(max_length=255)
    currency_of_sale = models.CharField(max_length=10)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    taxes_collected = models.DecimalField(max_digits=10, decimal_places=2)
    charged_amount = models.DecimalField(max_digits=10, decimal_places=2)
    city_of_buyer = models.CharField(max_length=255)
    state_of_buyer = models.CharField(max_length=255)
    postcode_of_buyer = models.CharField(max_length=20)
    country_of_buyer = models.CharField(max_length=255)
    base_plan_id = models.CharField(max_length=255)
    offer_id = models.CharField(max_length=255)
    group_id = models.IntegerField()
    first_usd_1m_eligible = models.CharField(max_length=255)
    promotion_id = models.CharField(max_length=255)
    coupon_value = models.DecimalField(max_digits=10, decimal_places=2)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2)
    featured_products_id = models.IntegerField()
    price_experiment_id = models.CharField(max_length=255)
    
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='estimated_sales_data')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'order_number', 'order_charged_date') # order_number should be unique per tenant
        verbose_name = "Vente Estimée"
        verbose_name_plural = "Ventes Estimées"

    def __str__(self):
        return f"Order {self.order_number} - {self.product_title} - Tenant: {self.tenant.name}"


