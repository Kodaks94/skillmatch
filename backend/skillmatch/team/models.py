from django.db import models
from django.contrib.auth.models import AbstractUser

'''
Models:
User, SKill, UserSkill(level), Team, Team Role

'''

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
class User(AbstractUser):

    display_name = models.CharField(max_length=100, blank= True)

    def __str__(self):
        return self.username

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    users = models.ManyToManyField(User, related_name='skills')
    def __str__(self):
        return self.name
class UserSkill(models.Model):
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE)
    skill = models.ForeignKey('Skill', on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=SKILL_LEVELS)
    experience_years = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    class Meta:
        unique_together = ('user', 'skill')

    def __str__(self):
        return f"self.user.username - {self.skill.name} ({self.level})"


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank = True)
    members = models.ManyToManyField(User, through='TeamRole')
    required_skills = models.ManyToManyField(Skill, blank=True)

    def __str__(self):
        return self.name
class TeamRole(models.Model):
    ROLE_CHOICES = [
        ('dev', 'Developer'),
        ('pm', 'Product Manager'),
        ('qa', 'QA')
    ]
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.user.username} on {self.team.name} as {self.get_role_display()}"