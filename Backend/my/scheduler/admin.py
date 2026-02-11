from django.contrib import admin
from .models import Teacher, Subject, ScheduleResult, Room, StudentGroup, MasterSubject

# --- 1. จัดการหน้า Master Data (หลักสูตร) *สำคัญมากสำหรับ Dropdown* ---
@admin.register(MasterSubject)
class MasterSubjectAdmin(admin.ModelAdmin):
    # แสดงคอลัมน์: รหัส, ชื่อ, ท-ป-น
    list_display = ('code', 'name', 'theory_hours', 'practical_hours', 'credits')
    search_fields = ('code', 'name')
    ordering = ('code',) # เรียงตามรหัสวิชา

# --- 2. จัดการหน้า Room ---
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# --- 3. จัดการหน้า StudentGroup ---
@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# --- 4. จัดการหน้า Teacher ---
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# --- 5. จัดการหน้า Subject (รายวิชาที่ลงตารางสอน) ---
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    # คอลัมน์ที่โชว์ในหน้ารายการรวม
    list_display = ('code', 'name', 'group', 'credits', 'hours_per_week', 'teacher', 'fixed_room')
    list_filter = ('group', 'teacher')
    search_fields = ('code', 'name')

    # จัด Layout ให้สวยงาม
    fieldsets = (
        ('ข้อมูลทั่วไป (Basic Info)', {
            'fields': (
                ('code', 'name'),   # บรรทัด 1: รหัส + ชื่อ
                'group'             # บรรทัด 2: กลุ่มเรียน
            )
        }),
        ('โครงสร้างหลักสูตร (Structure: ท-ป-น-ช)', {
            'fields': (
                # บรรทัด 3: เรียง 4 ช่องติดกัน
                ('theory_hours', 'practical_hours', 'credits', 'hours_per_week'),
            )
        }),
        ('ผู้สอนและสถานที่ (Instructor & Location)', {
            'fields': (
                ('teacher', 'fixed_room'), # บรรทัด 4: ครู + ห้อง
            )
        }),
        ('การล็อกตารางเรียน (Fixed Schedule)', {
            'classes': ('collapse',), 
            'fields': (
                'is_fixed', 
                ('fix_day', 'fix_slot')
            )
        }),
    )

    # สั่งลบปุ่ม + / แก้ไข / ลบ ออกจาก Dropdown (เพื่อกันไม่ให้แก้ Master Data จากหน้านี้)
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # รายชื่อช่องที่เราจะเอาปุ่มออก
        targets = ['group', 'teacher', 'fixed_room']
        
        for field_name in targets:
            if field_name in form.base_fields:
                field = form.base_fields[field_name]
                # สั่งปิดปุ่มเครื่องมือทั้งหมด
                field.widget.can_add_related = False      # ปิดปุ่มบวก (+)
                field.widget.can_change_related = False   # ปิดปุ่มดินสอ (แก้ไข)
                field.widget.can_delete_related = False   # ปิดปุ่มกากบาท (ลบ)
                field.widget.can_view_related = False     # ปิดปุ่มลูกตา (ดู)
                
        return form

# --- 6. จัดการหน้า ScheduleResult (ผลลัพธ์ตารางสอน) ---
@admin.register(ScheduleResult)
class ScheduleResultAdmin(admin.ModelAdmin):
    list_display = ('day', 'slot', 'subject_code', 'subject_name', 'teacher_name', 'room', 'group_id')
    list_filter = ('day', 'room', 'group_id')
    ordering = ('day', 'slot')