from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username
