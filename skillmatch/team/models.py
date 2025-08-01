from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Inherit username, email, password, etc.
    display_name = models.CharField(max_length=100, blank=True)

class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    users = models.ManyToManyField(User, related_name='skills')

class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, through='TeamRole')

class TeamRole(models.Model):
    ROLE_CHOICES = [
        ('dev', 'Developer'),
        ('pm', 'Product Manager'),
        ('qa', 'QA'),
        # Add more as needed
    ]
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)