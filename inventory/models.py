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
    return_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')

    def __str__(self):
        return f"{self.item.name} : {self.user.username} : {self.rental_date.strftime('%Y/%m/%d')} :（{self.get_status_display()}）"