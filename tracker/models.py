from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    date = models.DateField()
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.user.username})"

