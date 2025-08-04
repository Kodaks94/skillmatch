from django.test import TestCase
from rest_framework.test import APIClient
from .models import User, Skill, UserSkill, Team
from unittest.mock import patch

class SkillMatchTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Register a test user and get auth token
        res = self.client.post('/api/register/', {
            'username': 'testuser',
            'password': 'testpass',
            'email': 'test@example.com',
            'display_name': 'Testy'
        }, format='json')

        self.assertEqual(res.status_code, 200)
        self.token = res.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        #print("Token being used:", self.token)
        #check = self.client.get('/api/users/')
        #print("Token test response:", check.status_code, check.data)
        self.user = User.objects.get(username='testuser')
        self.user.is_active = True
        self.user.save()

        # Create skills
        self.python = Skill.objects.create(name='python')
        self.django = Skill.objects.create(name='django')
        self.docker = Skill.objects.create(name='docker')

        # Assign skills to user
        UserSkill.objects.create(user=self.user, skill=self.python, level='advanced', experience_years=3)
        UserSkill.objects.create(user=self.user, skill=self.django, level='intermediate', experience_years=2)

    def test_get_user_skills(self):
        res = self.client.get(f'/api/users/{self.user.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('skills', res.data)
        self.assertEqual(len(res.data['skills']), 2)

    def test_set_skills(self):
        payload = {
            "skills": [
                {"name": "docker", "level": "beginner", "experience_years": 1, "is_active": True}
            ]
        }
        res = self.client.post(f'/api/users/{self.user.id}/set-skills/', payload, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Skills updated successfully", res.data['message'])

        skills = UserSkill.objects.filter(user=self.user)
        self.assertEqual(skills.count(), 1)
        self.assertEqual(skills[0].skill.name, 'docker')

    def test_match_users_by_skills(self):
        res = self.client.get('/api/match/?skills=python,django')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)
        self.assertEqual(res.data[0]['match_score'], 5)
        self.assertEqual(len(res.data[0]['skills_matched']), 2)
        self.assertIn('readiness_score', res.data[0])
        self.assertEqual(res.data[0]['readiness_score'], '100%')

    def test_match_excludes_unskilled_users(self):
        User.objects.create_user(username='unskilled', password='nopass')
        res = self.client.get('/api/match/?skills=python')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)
        usernames = [u['username'] for u in res.data if isinstance(u, dict) and 'username' in u]
        self.assertIn('testuser', usernames)
        self.assertNotIn('unskilled', usernames)

    @patch("team.views.genai.GenerativeModel.generate_content")
    def test_skill_gap_analysis(self, mock_gemini_response):
        # Prepare mock Gemini response
        mock_gemini_response.return_value.text = "You are 66% ready. Learn Docker."

        team = Team.objects.create(name="Data Team")
        team.required_skills.set([self.python, self.django, self.docker])

        res = self.client.post('/api/skill-gap/', {
            "user_id": self.user.id,
            "team_id": team.id
        }, format='json')

        self.assertEqual(res.status_code, 200)
        self.assertIn('summary', res.data)
        self.assertIn('matched_skills', res.data)
        self.assertIn('missing_skills', res.data)
        self.assertIn('docker', res.data['missing_skills'])
    @patch("team.views.genai.GenerativeModel.generate_content", side_effect=Exception("Simulated API Failure"))
    def test_skill_gap_ai_fallback(self,mock_failure):
        team = Team.objects.create(name= "AI Team")
        team.required_skills.set([self.python,self.django,self.docker])
        res = self.client.post("/api/skill-gap/", {
            "user_id": self.user.id,
            "team_id": team.id
        }, format= 'json')

        self.assertEqual(res.status_code, 200)
        self.assertIn("Gemini AI summary failed", res.data['summary'])
        self.assertIn("simulated api failure", res.data["summary"].lower())
