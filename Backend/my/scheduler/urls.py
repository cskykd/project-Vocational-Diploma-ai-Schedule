from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # =========================================
    # 1. Authentication (ระบบล็อกอิน/สมัครสมาชิก)
    # =========================================
    path('register/', views.register_api, name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # =========================================
    # 2. Schedule Actions (ระบบจัดตารางสอน)
    # =========================================
    # ดึงตารางทั้งหมด (สำหรับหน้า Dashboard รวม)
    path('schedule/list/', views.schedule_list_api, name='schedule_list'),
    
    # สั่ง AI คำนวณตารางใหม่
    path('generate/', views.generate_schedule_api, name='generate_schedule'),
    
    # ล้างตารางสอนทั้งหมด
    path('schedule/reset/', views.reset_schedule_api, name='reset_schedule'),

    # ✅ ส่วนสำคัญที่เพิ่มเข้ามา (เพื่อให้เลือกดูตามครู/กลุ่มเรียนได้)
    path('schedule/teacher/<str:teacher_name>/', views.get_schedule_by_teacher_api, name='schedule_by_teacher'),
    path('schedule/group/<str:group_name>/', views.get_schedule_by_group_api, name='schedule_by_group'),

    # =========================================
    # 3. Master Data (สำหรับ Dropdown ต่างๆ)
    # =========================================
    path('master-subjects/', views.master_subjects_api, name='master_subjects'),
    path('teachers/', views.teacher_list_api, name='teacher_list'),
    path('groups/', views.group_list_api, name='group_list'),
    path('rooms/', views.room_list_api, name='room_list'),

    # =========================================
    # 4. Subject Management (จัดการรายวิชา CRUD)
    # =========================================
    path('subjects/', views.subject_list_api, name='subject_list'),              # ดูทั้งหมด
    path('subjects/<int:pk>/', views.subject_detail_api, name='subject_detail'), # ดูรายตัว
    path('subjects/add/', views.add_subject_api, name='add_subject'),            # เพิ่ม
    path('subjects/update/<int:pk>/', views.update_subject_api, name='update_subject'), # แก้ไข
    path('subjects/delete/<int:pk>/', views.delete_subject_api, name='delete_subject'), # ลบ
]