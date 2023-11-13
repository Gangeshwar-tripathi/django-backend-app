from django.db import models
from django.contrib.auth.models import User
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()

    def __str__(self):
        return self.user.username


class Collections(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name="collection",
                             related_query_name="collection")
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    movies = models.JSONField()

    def set_user(self, user):
        self.user = user
        self.save()

    def get_id(self):
        return self.uuid
