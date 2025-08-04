
from .models import User, Skill, Team, TeamRole, UserSkill, Skill
from rest_framework import serializers

class SkillSerializer(serializers.ModelSerializer):

    class Meta:
        model = Skill
        fields = ['id', 'name']

class UserSkillSerializer(serializers.ModelSerializer):
    skill = serializers.SlugRelatedField(slug_field='name', queryset=Skill.objects.all())

    class Meta:
        model = UserSkill
        fields = ['skill', 'level', 'experience_years','is_active']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email','password', 'display_name']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    match_score = serializers.IntegerField(read_only=True)
    skills_matched = serializers.ListField(read_only=True)
    readiness_score = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'display_name', 'skills', 'match_score', 'skills_matched',
                  'readiness_score']

    def get_skills(self,obj):
        user_skills = UserSkill.objects.filter(user = obj)
        return UserSkillSerializer(user_skills, many= True).data

    def get_readiness_score(self, obj):
        matched = self.context.get('matched_count', 0)
        required = self.context.get('required_count', 1)  # avoid divide by zero
        score = round((matched / required) * 100)
        return f"{score}%"


class TeamRoleSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeamRole
        fields = ['id', 'user', 'role']

class TeamSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    required_skills = serializers.PrimaryKeyRelatedField(many=True, queryset=Skill.objects.all())
    class Meta:
        model = Team
        fields = ['id', 'name','description', 'members','required_skills']

    def get_members(self,obj):
        roles = TeamRole.objects.filter(team=obj)
        return TeamRoleSerializer(roles, many=True).data

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields =['id', 'username', 'display_name']

