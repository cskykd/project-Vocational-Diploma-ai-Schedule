from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Teacher, Room, StudentGroup, Subject, ScheduleResult, MasterSubject

# --- 1. Authentication ---
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('username', 'password', 'email')
    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )

# --- 2. Master Data Serializers ---
class MasterSubjectSerializer(serializers.ModelSerializer):
    t = serializers.IntegerField(source='theory_hours', read_only=True)
    p = serializers.IntegerField(source='practical_hours', read_only=True)
    c = serializers.IntegerField(source='credits', read_only=True)
    class Meta:
        model = MasterSubject
        fields = ['id', 'code', 'name', 't', 'p', 'c']

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class StudentGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentGroup
        fields = '__all__'

# --- 3. Subject Serializer (ตัวสำคัญสำหรับหน้า List) ---
class SubjectSerializer(serializers.ModelSerializer):
    # เพิ่ม Field พิเศษสำหรับแสดงชื่อ (Read Only)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True, default='-')
    group_name = serializers.CharField(source='group.name', read_only=True, default='-')
    room_name = serializers.CharField(source='fixed_room.name', read_only=True, default='-')

    class Meta:
        model = Subject
        fields = '__all__'