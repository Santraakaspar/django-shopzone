from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, max_length=300)

    def __str__(self):
        return f'{self.user.username} Profile'

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/images/default_avatar.png'
