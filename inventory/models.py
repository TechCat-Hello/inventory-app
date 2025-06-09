from django.db import models

# class Item(models.Model):
#     name = models.CharField(max_length=100)
#     description = models.TextField(blank=True)
#     quantity = models.PositiveIntegerField(default=0)
#     location = models.CharField(max_length=100, blank=True)
#     added_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name

class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    location = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity})"