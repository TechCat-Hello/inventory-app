from django.db import models
from django.contrib.auth.models import User


class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    location = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE) 

    def __str__(self):
        return f"{self.name} ({self.quantity})"
    
class Rental(models.Model):
    STATUS_CHOICES = [
        ('borrowed', '貸出中'),
        ('returned', '返却済み'),
    ]

    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField() 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rental_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField(null=False, blank=False)
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')

    def __str__(self):
        return f"{self.item.name} : {self.user.username} : {self.rental_date.strftime('%Y/%m/%d')} :（{self.get_status_display()}）"
    
class ReturnLog(models.Model):
    rental = models.ForeignKey('Rental', on_delete=models.CASCADE, related_name='return_logs')
    returned_quantity = models.PositiveIntegerField()
    returned_at = models.DateTimeField(auto_now_add=True)
    returned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.rental.item.name} - {self.returned_quantity}個返却 ({self.returned_at.strftime('%Y/%m/%d %H:%M')})"
    
