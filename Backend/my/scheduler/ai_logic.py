import random
import copy

# ==========================================
# 1. CONFIGURATION
# ==========================================
DAYS = 5
SLOTS_PER_DAY = 12       # 12 คาบ (0-11)
LUNCH_BREAK_SLOT = 4     # พักเที่ยงคาบที่ 5 (Index 4)

POPULATION_SIZE = 50     
MAX_GENERATIONS = 100    

# ค่าคะแนน (Penalty)
PENALTY_LUNCH = 500             
PENALTY_GROUP_CONFLICT = 2000   
PENALTY_TEACHER_CONFLICT = 5000 
PENALTY_FIXED_CONFLICT = 5000   

# ==========================================
# 2. DATA MODEL
# ==========================================
class Event:
    def __init__(self, course_id, teacher_id, fixed_room, group_id, duration, 
                 is_fixed=False, fix_day=None, fix_slot=None, subject_name=""):
        
        self.course_id = str(course_id).strip() if course_id else "Unknown"
        self.teacher_id = str(teacher_id).strip() if teacher_id else "N/A"
        self.fixed_room = str(fixed_room).strip() if fixed_room else "-"
        self.group_id = str(group_id).strip() if group_id else "General"
        self.subject_name = str(subject_name).strip() if subject_name else ""
        
        # duration ต้องไม่ต่ำกว่า 1
        self.duration = int(duration) if duration and int(duration) > 0 else 1
        
        # Logic การ Lock
        self.is_fixed = is_fixed
        self.fix_day = fix_day      
        self.fix_slot = fix_slot    
        
        self.assigned_day = None
        self.assigned_slot = None

# ==========================================
# 3. GENETIC ALGORITHM CORE
# ==========================================

def get_valid_start_slots(duration):
    """หา Slot เริ่มต้นที่ลงได้โดยไม่เกินวันและไม่ทับพักเที่ยง"""
    valid = []
    # ป้องกัน duration เกินจำนวนคาบ
    if duration > SLOTS_PER_DAY: duration = SLOTS_PER_DAY

    # เช็คทุก Slot ที่เป็นไปได้
    for start in range(SLOTS_PER_DAY - duration + 1):
        span = range(start, start + duration)
        # ถ้าช่วงเวลานี้ ไม่ทับพักเที่ยง ให้ถือว่าใช้ได้
        if LUNCH_BREAK_SLOT not in span:
            valid.append(start)
            
    # กรณีหาที่ลงไม่ได้เลย (เช่นวิชายาวมาก) ให้ยอมคืนค่าช่วงเวลาปกติไป (ดีกว่า Error)
    if not valid:
        valid = list(range(SLOTS_PER_DAY - duration + 1))
        
    return valid

def initialize_population(events, pop_size):
    population = []
    for _ in range(pop_size):
        chromosome = []
        for event in events:
            new_event = copy.deepcopy(event)
            
            # ตรวจสอบการ Lock
            if new_event.is_fixed and new_event.fix_day is not None:
                new_event.assigned_day = new_event.fix_day
                new_event.assigned_slot = new_event.fix_slot if new_event.fix_slot is not None else 0
            else:
                # สุ่มวันและเวลา
                new_event.assigned_day = random.randint(0, DAYS - 1)
                valid_slots = get_valid_start_slots(new_event.duration)
                new_event.assigned_slot = random.choice(valid_slots) if valid_slots else 0
            
            chromosome.append(new_event)
        population.append(chromosome)
    return population

def calculate_fitness(chromosome):
    fitness = 0
    time_slot_map = {}

    for event in chromosome:
        fitness += 100 # คะแนนพื้นฐานของการได้ลงตาราง
        
        # วนลูปทุก Slot ที่วิชานี้กินเวลา
        for i in range(event.duration):
            slot = event.assigned_slot + i
            
            # 1. ห้ามเลยเวลาเรียน
            if slot >= SLOTS_PER_DAY: 
                fitness -= 1000; break
            
            # 2. ห้ามทับพักเที่ยง
            if slot == LUNCH_BREAK_SLOT:
                fitness -= PENALTY_LUNCH

            # บันทึกการใช้งาน Slot เพื่อเช็คชน
            key = (event.assigned_day, slot)
            if key not in time_slot_map: time_slot_map[key] = []
            time_slot_map[key].append(event)

    # ตรวจสอบการชนกัน (Conflict)
    for key, events_in_slot in time_slot_map.items():
        if len(events_in_slot) > 1:
            conflict_count = len(events_in_slot) - 1
            
            # ครูคนเดียวกันสอนพร้อมกันไม่ได้
            teachers = [e.teacher_id for e in events_in_slot if e.teacher_id != "N/A"]
            if len(teachers) != len(set(teachers)):
                fitness -= (PENALTY_TEACHER_CONFLICT * conflict_count)

            # นักเรียนกลุ่มเดียวกันเรียนพร้อมกันไม่ได้
            all_groups = []
            for e in events_in_slot:
                groups = [g.strip() for g in e.group_id.split(',')] # เผื่อมีหลายกลุ่ม
                all_groups.extend(groups)
            if len(all_groups) != len(set(all_groups)):
                fitness -= (PENALTY_GROUP_CONFLICT * conflict_count)

            # ห้องเรียน (ถ้าระบุ) ใช้ซ้ำไม่ได้
            rooms = [e.fixed_room for e in events_in_slot if e.fixed_room not in ["-", "Any", ""]]
            if len(rooms) != len(set(rooms)):
                fitness -= (100 * conflict_count)
                
    return fitness

def crossover_and_mutate(population):
    # จัดอันดับตามคะแนน
    scored_pop = sorted([(calculate_fitness(c), c) for c in population], key=lambda x: x[0], reverse=True)
    best_score = scored_pop[0][0]
    best_schedule = scored_pop[0][1]
    
    # Elitism: เก็บตัวที่ดีที่สุดไว้ 20%
    new_pop = [c for s, c in scored_pop[:int(POPULATION_SIZE*0.2)]]
    
    # สร้างลูกหลานใหม่จนครบจำนวนประชากร
    while len(new_pop) < POPULATION_SIZE:
        # เลือกพ่อแม่จากกลุ่มหัวกะทิ (Top 50%)
        parent = random.choice(scored_pop[:int(POPULATION_SIZE*0.5)])[1]
        child = copy.deepcopy(parent)
        
        # Mutation: สุ่มเปลี่ยนตำแหน่ง
        if random.random() < 0.4: # โอกาสกลายพันธุ์ 40%
            target = random.choice(child)
            if not target.is_fixed: # ห้ามยุ่งกับวิชาที่ Lock
                if random.random() < 0.5:
                    target.assigned_day = random.randint(0, DAYS - 1)
                else:
                    valid = get_valid_start_slots(target.duration)
                    if valid: target.assigned_slot = random.choice(valid)
        new_pop.append(child)
        
    return new_pop, best_schedule, best_score

# ฟังก์ชันหลักที่ Views.py จะเรียกใช้
def run_scheduler_ai(subjects_queryset):
    # 1. แปลงข้อมูลจาก Django QuerySet -> Event Objects
    events_objects = []
    
    for subj in subjects_queryset:
        # รวมเวลาเรียน ทฤษฎี+ปฏิบัติ เป็น duration เดียว
        total_hours = subj.hours_per_week
        if total_hours <= 0: total_hours = 1
        
        # ดึงข้อมูลจาก Relation (จัดการกรณีเป็น Null)
        t_name = subj.teacher.name if subj.teacher else "N/A"
        r_name = subj.fixed_room.name if subj.fixed_room else "-"
        g_name = subj.group.name if subj.group else "General"
        
        # แปลงข้อมูล Lock (Django เก็บ 1-based แต่ AI ใช้ 0-based)
        fix_d = (subj.fix_day - 1) if subj.fix_day else None
        fix_s = (subj.fix_slot - 1) if subj.fix_slot else None
        
        evt = Event(
            course_id=subj.code,
            teacher_id=t_name,
            fixed_room=r_name,
            group_id=g_name,
            duration=total_hours,
            is_fixed=subj.is_fixed,
            fix_day=fix_d,
            fix_slot=fix_s,
            subject_name=subj.name
        )
        events_objects.append(evt)

    if not events_objects:
        return []

    # 2. เริ่มกระบวนการ Genetic Algorithm
    print(f"🧬 AI Starting... Generating schedule for {len(events_objects)} subjects over {MAX_GENERATIONS} generations.")
    
    population = initialize_population(events_objects, POPULATION_SIZE)
    best_schedule = population[0]
    
    for gen in range(MAX_GENERATIONS):
        population, best_schedule, score = crossover_and_mutate(population)
        # ถ้าคะแนนเต็มหรือสูงมาก อาจจะ break loop ก่อนได้ตรงนี้

    print("✅ AI Finished.")
    return best_schedule