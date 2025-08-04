from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'skills', views.SkillViewSet, basename='skill')
router.register(r'teams', views.TeamViewSet, basename='team')

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Endpoints (DRF ViewSets)
    path('api/', include(router.urls)),

    # Function-based API endpoints
    path('api/match/', views.match_user_by_skills),
    path('api/skill-gap/', views.skill_gap_analysis),
    path('api/extract-skills/', views.SkillExtractionView.as_view()),
    path('api/register/', views.RegisterView.as_view()),

    # Web pages (HTML views)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('match/', views.skill_match_view, name='skill_match'),
    path('gap-analysis/', views.gap_analysis_view, name='gap_analysis'),
    path('extract-skills/', views.extract_skills_view, name='extract_skills'),
]
