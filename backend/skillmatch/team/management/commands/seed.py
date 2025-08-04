from django.core.management.base import BaseCommand
from ....team.models import User, Skill, UserSkill, Team, TeamRole

class Command(BaseCommand):
    help = 'Seed the database with mock users, skills, and a team'

    def handle(self, *args, **kwargs):
        skill_names = ['python', 'django', 'javascript', 'gcp', 'react', 'sql']
        skills = {name: Skill.objects.get_or_create(name=name)[0] for name in skill_names}

        user_specs = [
            {'username': 'alice', 'display_name': 'Alice Dev', 'skills': ['python', 'django', 'sql']},
            {'username': 'bob', 'display_name': 'Bob PM', 'skills': ['gcp', 'javascript']},
            {'username': 'charlie', 'display_name': 'Charlie QA', 'skills': ['react', 'sql']},
        ]

        users = []
        for spec in user_specs:
            user, created = User.objects.get_or_create(username=spec['username'], defaults={'display_name': spec['display_name']})
            if created:
                user.set_password('test1234')
                user.save()
            for s in spec['skills']:
                UserSkill.objects.get_or_create(user=user, skill=skills[s], defaults={
                    'level': 'intermediate',
                    'experience_years': 2,
                    'is_active': True
                })
            users.append(user)

        team, _ = Team.objects.get_or_create(name='Alpha Squad', defaults={'description': 'Test Team for Matching'})
        team.required_skills.set([skills['python'], skills['gcp'], skills['react']])
        team.save()

        TeamRole.objects.get_or_create(user=users[0], team=team, role='dev')
        TeamRole.objects.get_or_create(user=users[1], team=team, role='pm')
        TeamRole.objects.get_or_create(user=users[2], team=team, role='qa')

        self.stdout.write(self.style.SUCCESS("\n✅ Mock users, skills, and team created successfully.\n"))