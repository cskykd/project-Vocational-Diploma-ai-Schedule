from django.db import models

# --- 1. ข้อมูลหลัก (Master Data) สำหรับ Dropdown ---
class MasterSubject(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="รหัสวิชา")
    name = models.CharField(max_length=100, verbose_name="ชื่อวิชา")
    theory_hours = models.IntegerField(default=0, verbose_name="ทฤษฎี (ชม.)")
    practical_hours = models.IntegerField(default=0, verbose_name="ปฏิบัติ (ชม.)")
    credits = models.IntegerField(default=0, verbose_name="หน่วยกิต")

    def __str__(self):
        return f"{self.code} - {self.name}"

# --- 2. ข้อมูลพื้นฐาน (ครู, ห้อง, กลุ่ม) ---
class Room(models.Model):
    name = models.CharField(max_length=50, verbose_name="ชื่อห้อง")
    def __str__(self): return self.name

class Teacher(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อครูผู้สอน")
    def __str__(self): return self.name

class StudentGroup(models.Model):
    name = models.CharField(max_length=50, verbose_name="ชื่อกลุ่มเรียน")
    def __str__(self): return self.name

# --- 3. รายวิชาที่เปิดสอนจริง (Scheduled Course) ---
class Subject(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    
    # ความสัมพันธ์ (Foreign Keys)
    group = models.ForeignKey(StudentGroup, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    fixed_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    
    # ข้อมูลหน่วยกิต
    theory_hours = models.IntegerField(default=0)
    practical_hours = models.IntegerField(default=0)
    credits = models.IntegerField(default=0)
    hours_per_week = models.IntegerField(default=1)
    
    # การล็อกวันเวลา (Fixed Schedule)
    is_fixed = models.BooleanField(default=False)
    fix_day = models.IntegerField(default=1) # 1=จันทร์, 7=อาทิตย์
    fix_slot = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.code} ({self.name})"

class ScheduleResult(models.Model):
    subject_code = models.CharField(max_length=20)
    subject_name = models.CharField(max_length=100)
    teacher_name = models.CharField(max_length=100, null=True, blank=True)
    room = models.CharField(max_length=50, null=True, blank=True)
    group_id = models.CharField(max_length=50, null=True, blank=True)
    day = models.IntegerField()
    slot = models.IntegerField()