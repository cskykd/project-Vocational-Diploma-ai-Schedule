from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from .models import Subject, Teacher, Room, StudentGroup, MasterSubject, ScheduleResult
from .serializers import (
    TeacherSerializer, RoomSerializer, StudentGroupSerializer, 
    MasterSubjectSerializer, SubjectSerializer, RegisterSerializer
)

from .ai_logic import run_scheduler_ai 

# ==========================================
# 1. Authentication
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    try:
        data = request.data
        if User.objects.filter(username=data['email']).exists():
            return Response({'error': 'อีเมลนี้ถูกใช้งานแล้ว'}, status=400)

        user = User.objects.create(
            username=data['email'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            password=make_password(data['password'])
        )
        return Response({"status": "success", "message": "สมัครสมาชิกสำเร็จ"}, status=201)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)

# ==========================================
# 2. Master Data (แก้ไขให้รองรับ POST เพื่อเพิ่มข้อมูลได้)
# ==========================================

@api_view(['GET'])
@permission_classes([AllowAny])
def master_subjects_api(request):
    subjects = MasterSubject.objects.all().order_by('code')
    serializer = MasterSubjectSerializer(subjects, many=True)
    return Response({"status": "success", "data": serializer.data})

# --- แก้ไข Teacher ให้รับ POST ได้ ---
@api_view(['GET', 'POST']) 
@permission_classes([AllowAny])
def teacher_list_api(request):
    if request.method == 'GET':
        teachers = Teacher.objects.all()
        serializer = TeacherSerializer(teachers, many=True)
        return Response({"status": "success", "data": serializer.data})
    elif request.method == 'POST':
        serializer = TeacherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=201)
        return Response(serializer.errors, status=400)

# --- แก้ไข Room ให้รับ POST ได้ ---
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def room_list_api(request):
    if request.method == 'GET':
        rooms = Room.objects.all()
        serializer = RoomSerializer(rooms, many=True)
        return Response({"status": "success", "data": serializer.data})
    elif request.method == 'POST':
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=201)
        return Response(serializer.errors, status=400)

# --- แก้ไข Group ให้รับ POST ได้ ---
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def group_list_api(request):
    if request.method == 'GET':
        groups = StudentGroup.objects.all()
        serializer = StudentGroupSerializer(groups, many=True)
        return Response({"status": "success", "data": serializer.data})
    elif request.method == 'POST':
        serializer = StudentGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=201)
        return Response(serializer.errors, status=400)

# ==========================================
# 3. CRUD Subjects (Manage Course)
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def add_subject_api(request):
    data = request.data
    try:
        # ใช้ get_or_create เพื่อป้องกัน Error ถ้าข้อมูลไม่ตรง
        teacher_obj, _ = Teacher.objects.get_or_create(name=data.get('teacher'))
        
        # กรณี group ส่งมาเป็น ID (จาก Frontend ที่แก้ใหม่) หรือ ชื่อ
        group_input = data.get('group')
        group_obj = None
        
        if isinstance(group_input, int):
            group_obj = StudentGroup.objects.get(pk=group_input)
        else:
            group_obj, _ = StudentGroup.objects.get_or_create(name=str(group_input))

        room_obj = None
        if data.get('room'):
            room_obj, _ = Room.objects.get_or_create(name=data.get('room'))

        theory = int(data.get('theory', 0))
        practice = int(data.get('practice', 0))
        total_hours = theory + practice 
        if total_hours <= 0: total_hours = 1
        
        is_fixed_val = data.get('isFixed') or data.get('is_fixed') or False
        if str(is_fixed_val).lower() == 'true': is_fixed_val = True
        else: is_fixed_val = bool(is_fixed_val)

        Subject.objects.create(
            code=data.get('code'), name=data.get('name'),
            teacher=teacher_obj, group=group_obj, fixed_room=room_obj,
            theory_hours=theory, practical_hours=practice,
            credits=data.get('credit', 0), hours_per_week=total_hours,
            is_fixed=is_fixed_val, fix_day=data.get('day', 1), fix_slot=data.get('startSlot', 1)
        )
        return Response({"status": "success", "message": "บันทึกข้อมูลสำเร็จ"}, status=201)
    except Exception as e:
        print(f"Error Add Subject: {e}") # print error ใน console เพื่อ debug
        return Response({"status": "error", "message": str(e)}, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def subject_list_api(request):
    subjects = Subject.objects.all().order_by('-id')
    serializer = SubjectSerializer(subjects, many=True)
    return Response({"status": "success", "data": serializer.data})

@api_view(['GET'])
@permission_classes([AllowAny])
def subject_detail_api(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    serializer = SubjectSerializer(subject)
    return Response({"status": "success", "data": serializer.data})

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_subject_api(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    data = request.data
    try:
        if data.get('teacher'):
            teacher_obj, _ = Teacher.objects.get_or_create(name=data.get('teacher'))
            subject.teacher = teacher_obj
        
        if data.get('group'):
            group_input = data.get('group')
            if isinstance(group_input, int):
                group_obj = StudentGroup.objects.get(pk=group_input)
            else:
                group_obj, _ = StudentGroup.objects.get_or_create(name=str(group_input))
            subject.group = group_obj

        if data.get('room'):
            room_obj, _ = Room.objects.get_or_create(name=data.get('room'))
            subject.fixed_room = room_obj
        else:
            subject.fixed_room = None

        subject.code = data.get('code', subject.code)
        subject.name = data.get('name', subject.name)
        subject.credits = data.get('credit', subject.credits)
        
        t = int(data.get('theory', subject.theory_hours))
        p = int(data.get('practice', subject.practical_hours))
        subject.theory_hours = t
        subject.practical_hours = p
        total = t + p
        if total <= 0: total = 1
        subject.hours_per_week = total

        is_fixed_val = data.get('isFixed') 
        if is_fixed_val is None: is_fixed_val = data.get('is_fixed')
        
        if is_fixed_val is not None:
            if str(is_fixed_val).lower() == 'true': is_fixed_val = True
            else: is_fixed_val = bool(is_fixed_val)
            subject.is_fixed = is_fixed_val

        subject.fix_day = data.get('day', subject.fix_day)
        subject.fix_slot = data.get('startSlot', subject.fix_slot)

        subject.save()
        return Response({"status": "success", "message": "อัปเดตข้อมูลสำเร็จ"})
    except Exception as e:
        print(e)
        return Response({"status": "error", "message": str(e)}, status=400)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_subject_api(request, pk):
    try:
        subject = get_object_or_404(Subject, pk=pk)
        ScheduleResult.objects.filter(subject_code=subject.code).delete()
        subject.delete()
        return Response({"status": "success", "message": "ลบข้อมูลสำเร็จ"})
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)

# ==========================================
# 4. Schedule Logic
# ==========================================
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_schedule_api(request):
    try:
        ScheduleResult.objects.all().delete()
        subjects = Subject.objects.all()
        if not subjects.exists():
            return Response({"status": "error", "message": "ไม่มีรายวิชาให้จัดตาราง"}, status=400)

        best_schedule_events = run_scheduler_ai(subjects)
        
        results_to_save = []
        for event in best_schedule_events:
            start_day = event.assigned_day + 1
            start_slot_idx = event.assigned_slot
            for i in range(event.duration):
                current_slot = start_slot_idx + i + 1
                results_to_save.append(ScheduleResult(
                    subject_code=event.course_id, subject_name=event.subject_name,
                    teacher_name=event.teacher_id, room=event.fixed_room,
                    group_id=event.group_id, day=start_day, slot=current_slot
                ))

        ScheduleResult.objects.bulk_create(results_to_save)
        return Response({"status": "success", "message": f"AI จัดตารางเสร็จสิ้น"})
    except Exception as e:
        print(f"Error in Generate: {e}")
        return Response({"status": "error", "message": str(e)}, status=400)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def reset_schedule_api(request):
    ScheduleResult.objects.all().delete()
    return Response({"status": "success", "message": "ล้างข้อมูลเรียบร้อย"})

# ==========================================
# 5. Fetch Schedule APIs
# ==========================================
@api_view(['GET'])
@permission_classes([AllowAny])
def schedule_list_api(request):
    results = ScheduleResult.objects.all()
    data = [
        {
            "subject_code": r.subject_code, "subject_name": r.subject_name,
            "teacher_name": r.teacher_name, "room": r.room,
            "group_id": r.group_id, "day": r.day, "slot": r.slot
        } for r in results
    ]
    return Response({"status": "success", "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def get_schedule_by_group_api(request, group_name):
    results = ScheduleResult.objects.filter(group_id__contains=group_name)
    data = [
        {
            "subject_code": r.subject_code, "subject_name": r.subject_name,
            "teacher_name": r.teacher_name, "room": r.room,
            "group_id": r.group_id, "day": r.day, "slot": r.slot
        } for r in results
    ]
    return Response({"status": "success", "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def get_schedule_by_teacher_api(request, teacher_name):
    results = ScheduleResult.objects.filter(teacher_name=teacher_name)
    data = [
        {
            "subject_code": r.subject_code, "subject_name": r.subject_name,
            "teacher_name": r.teacher_name, "room": r.room,
            "group_id": r.group_id, "day": r.day, "slot": r.slot
        } for r in results
    ]
    return Response({"status": "success", "data": data})