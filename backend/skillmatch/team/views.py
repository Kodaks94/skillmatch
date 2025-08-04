from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.conf import settings
from decouple import config
from django.contrib.auth.decorators import login_required
import google.generativeai as genai
import os
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
from .models import User, Skill, Team, UserSkill
from .serializers import (
    SkillSerializer,
    TeamSerializer,
    UserSerializer,
    UserSkillSerializer,
    RegisterSerializer,
)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='set-skills')
    def set_skills(self, request, pk=None):
        """
        POST /api/users/<id>/set-skills/
        Accepts list like:
        [{"name": "python", "level": "advanced", "experience_years": 2}]
        """
        user = self.get_object()
        skills_data = request.data.get("skills", [])

        if not isinstance(skills_data, list):
            return Response({"error": "skills must be a list of skill dicts"}, status=400)

        UserSkill.objects.filter(user=user).delete()

        for entry in skills_data:
            name = entry.get("name")
            level = entry.get("level", "beginner").lower()
            years = entry.get("experience_years", 0)
            active = entry.get("is_active", True)

            if not name:
                continue

            skill, _ = Skill.objects.get_or_create(name=name.lower())
            UserSkill.objects.create(
                user=user,
                skill=skill,
                level=level,
                experience_years=years,
                is_active=active
            )

        return Response({"message": "Skills updated successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def match_user_by_skills(request):
    """
    GET /api/match/?skills=python,django
    Returns users with score, matched skill details, and readiness %.
    """
    permission_classes = [IsAuthenticated]
    skill_names = request.GET.get('skills')
    if not skill_names:
        return Response({
            "error": "Please provide a comma-separated list of skills, e.g. ?skills=python,django"
        }, status=400)

    skill_list = [s.strip().lower() for s in skill_names.split(',')]
    matching_skills = Skill.objects.filter(name__in=skill_list)
    skill_ids = matching_skills.values_list('id', flat=True)

    LEVEL_SCORES = {'beginner': 1, 'intermediate': 2, 'advanced': 3}

    matched_users = {}
    user_skills = UserSkill.objects.filter(skill__id__in=skill_ids).select_related('user', 'skill')

    for us in user_skills:
        uid = us.user.id
        if uid not in matched_users:
            matched_users[uid] = {'user': us.user, 'score': 0, 'skills_matched': []}

        score = LEVEL_SCORES.get(us.level.lower(), 0)
        matched_users[uid]['score'] += score
        matched_users[uid]['skills_matched'].append({
            'skill': us.skill.name,
            'level': us.level,
            'score': score
        })

    sorted_users = sorted(matched_users.values(), key=lambda x: x['score'], reverse=True)

    result = []
    total_required = len(skill_list)
    for match in sorted_users:
        matched_count = len(match['skills_matched'])
        serializer = UserSerializer(
            match['user'],
            context={'matched_count': matched_count, 'required_count': total_required}
        )
        user_data = serializer.data
        user_data['match_score'] = match['score']
        user_data['skills_matched'] = match['skills_matched']
        result.append(user_data)

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def skill_gap_analysis(request):
    user_id = request.data.get('user_id')
    team_id = request.data.get('team_id')

    if not user_id or not team_id:
        return Response({'error': 'user_id and team_id required'}, status=400)

    try:
        user = User.objects.get(id= user_id)
        team = Team.objects.get(id= team_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status = 400)

    except Team.DoesNotExist:
        return Response({'error': 'Team not found'}, status = 400)

    user_skills = set(UserSkill.objects.filter(user=user).values_list('skill__name', flat=True))
    team_skills = set(team.required_skills.values_list('name', flat=True))

    matched = list(user_skills & team_skills)
    missing = list(team_skills - user_skills)

    prompt = (
        f"User has the following skills: {', '.join(matched)}.\n"
        f"Team requires: {', '.join(team_skills)}.\n"
        f"Write a short summary of the user's readiness, skills they still need, and an encouraging message. "
        f"Include an estimated readiness percentage."
    )

    try:
        genai.configure(api_key = GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        summary = response.text
    except Exception as e:
        summary = f"Gemini AI summary failed: {e}"

    return Response({
        'user': user.username,
        'team': team.name,
        'matched_skills': matched,
        "missing_skills": missing,
        "summary": summary
    })

class SkillViewSet(viewsets.ModelViewSet):
    """
     Standard CRUD API for Skill objects
     GET, POST, PUT, DELETE /api/skills/
     """
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]

class TeamViewSet(viewsets.ModelViewSet):
    """
    Standard CRUD API for Team objects
    GET, POST, PUT, DELETE /api/teams/
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

class RegisterView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data= request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status = 400)


import ast
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class SkillExtractionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "Missing 'text' field"}, status=400)

        prompt = (
            "Extract and return a list of programming and technical skills mentioned in this text.\n\n"
            f"{text}\n\n"
            "Return ONLY a Python list of lowercase skill names, like: ['django', 'react', 'gcp'].\n"
            "Do not explain or add formatting — just output the list."
        )

        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            raw_output = response.text.strip()

            # Debug: print Gemini's response in console
            print("\n Gemini raw output:", raw_output)

            # Try strict parsing first
            try:
                skills = ast.literal_eval(raw_output)
                if not isinstance(skills, list):
                    raise ValueError("Not a list")
            except Exception:
                # Fallback: match list-like patterns
                skills = re.findall(r"['\"]?([a-zA-Z0-9_+\-.#]+)['\"]?", raw_output)

            cleaned = sorted(set(s.lower() for s in skills if isinstance(s, str) and s.strip()))
            return Response({"skills": cleaned})

        except Exception as e:
            return Response({"error": f"Gemini AI failed: {str(e)}"}, status=500)




@login_required
def dashboard_view(request):
    return render(request, "dashboard.html")

@login_required
def skill_match_view(request):
    return render(request, "skill_match.html")

@login_required
def gap_analysis_view(request):
    return render(request, "gap_analysis.html")

@login_required
def extract_skills_view(request):
    return render(request, "extract_skills.html")
