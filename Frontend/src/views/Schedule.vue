<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import Swal from 'sweetalert2'
import { useRouter } from 'vue-router';

const router = useRouter(); 
const API_URL = 'http://127.0.0.1:8000/api';

const scheduleData = ref([])
const statusMessage = ref('')
const isLoading = ref(false)
const generated = ref(false)

// --- Config: ภาคเรียนและปีการศึกษา (แก้ปัญหาค่าถูกล็อก) ---
const currentYear = new Date().getFullYear() + 543; // คำนวณปีปัจจุบัน (พ.ศ.)

// 1. ลองดึงค่าจาก LocalStorage ก่อน (ถ้าเคยเลือกไว้)
const savedTerm = localStorage.getItem('ai_selectedTerm');
const savedYear = localStorage.getItem('ai_selectedYear');

// 2. ถ้าไม่มีใน Storage ให้ใช้ค่า Default
const selectedTerm = ref(savedTerm || '1');
const selectedYear = ref(savedYear || currentYear.toString());

const terms = ['1', '2', 'S']; // ภาคเรียน
const years = [currentYear + 1, currentYear, currentYear - 1].map(String); // ปีหน้า, ปีนี้, ปีที่แล้ว

// 3. Watcher: เมื่อมีการเปลี่ยนค่า ให้บันทึกลง LocalStorage ทันที
watch(selectedTerm, (newVal) => localStorage.setItem('ai_selectedTerm', newVal));
watch(selectedYear, (newVal) => localStorage.setItem('ai_selectedYear', newVal));

// --- State อื่นๆ ---
const currentTeacher = ref('') 
const allTeachersInSchedule = ref([]) 

// --- Navigation ---
const goToSubjects = () => router.push('/subjects')
const goToTeacherSchedule = () => router.push('/teacher-schedule')
const goToClassSchedule = () => router.push('/class-schedule') 

// --- Logout ---
const handleLogout = () => {
    Swal.fire({
        title: 'ยืนยันการออกจากระบบ',
        text: "คุณต้องการออกจากระบบใช่หรือไม่?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'ใช่, ออกจากระบบ',
        cancelButtonText: 'ยกเลิก',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            router.push('/login');
        }
    })
}

// --- Table Config ---
const timeHeaders = [
    { slot: 1, time: "08:30-09:30" },
    { slot: 2, time: "09:30-10:30" },
    { slot: 3, time: "10:30-11:30" },
    { slot: 4, time: "11:30-12:30" },
    { slot: 5, time: "12:30-13:30" }, // พักเที่ยง
    { slot: 6, time: "13:30-14:30" },
    { slot: 7, time: "14:30-15:30" },
    { slot: 8, time: "15:30-16:30" },
    { slot: 9, time: "16:30-17:30" },
    { slot: 10, time: "17:30-18:30" },
    { slot: 11, time: "18:30-19:30" },
    { slot: 12, time: "19:30-20:30" },
]

const days = [
    { id: 1, name: "จันทร์", color: "bg-yellow-100 text-yellow-800 border-yellow-200" }, 
    { id: 2, name: "อังคาร", color: "bg-pink-100 text-pink-800 border-pink-200" }, 
    { id: 3, name: "พุธ", color: "bg-green-100 text-green-800 border-green-200" }, 
    { id: 4, name: "พฤหัส", color: "bg-orange-100 text-orange-800 border-orange-200" }, 
    { id: 5, name: "ศุกร์", color: "bg-blue-100 text-blue-800 border-blue-200" }
]

// --- Initialization ---
onMounted(async () => {
    await fetchScheduleData();
});

// --- API Functions ---
const fetchScheduleData = async () => {
    try {
        const res = await axios.get(`${API_URL}/schedule/list/`);
        if (res.data.status === 'success') {
            const data = Array.isArray(res.data.data) ? res.data.data : [];
            scheduleData.value = data;
            
            if (data.length > 0) {
                const uniqueTeachers = [...new Set(data.map(item => item.teacher_name))];
                allTeachersInSchedule.value = uniqueTeachers;

                if (!currentTeacher.value && uniqueTeachers.length > 0) {
                    randomizeTeacher();
                }
                generated.value = true;
            } else {
                generated.value = false;
                currentTeacher.value = '';
            }
        }
    } catch (e) {
        console.error("Fetch Error:", e);
        statusMessage.value = "ไม่สามารถเชื่อมต่อกับ Server ได้";
    }
}

const randomizeTeacher = () => {
    if (allTeachersInSchedule.value.length > 0) {
        const randomIndex = Math.floor(Math.random() * allTeachersInSchedule.value.length);
        currentTeacher.value = allTeachersInSchedule.value[randomIndex];
    }
}

const startGenerate = async () => {
    const result = await Swal.fire({
        title: 'ยืนยันการจัดตารางใหม่',
        html: `กำลังจัดตารางสำหรับ<br/><b style="color:#f97316">ภาคเรียนที่ ${selectedTerm.value} ปีการศึกษา ${selectedYear.value}</b><br/>ระบบจะล้างข้อมูลเก่าและประมวลผลใหม่`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#f97316',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'เริ่มจัดตาราง',
        cancelButtonText: 'ยกเลิก'
    })

    if (!result.isConfirmed) return;

    isLoading.value = true;
    currentTeacher.value = ''; 
    try {
        // ส่งเทอมและปีไปให้ Backend
        const payload = {
            term: selectedTerm.value,
            academic_year: selectedYear.value
        };

        const res = await axios.post(`${API_URL}/generate/`, payload);
        
        if (res.data.status === 'success') {
            await fetchScheduleData();
            Swal.fire('สำเร็จ', 'AI จัดตารางเรียบร้อยแล้ว', 'success')
        }
    } catch (e) {
        console.error(e);
        Swal.fire('เกิดข้อผิดพลาด', 'ไม่สามารถจัดตารางได้', 'error')
    } finally { 
        isLoading.value = false; 
    }
}

const resetSchedule = async () => {
    const result = await Swal.fire({
        title: 'ล้างข้อมูลตาราง?',
        text: "คุณต้องการลบข้อมูลตารางเรียนทั้งหมดใช่ไหม? (ไม่สามารถกู้คืนได้)",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc2626',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'ใช่, ล้างข้อมูล',
        cancelButtonText: 'ยกเลิก'
    })

    if (!result.isConfirmed) return;

    isLoading.value = true;
    try {
        await axios.delete(`${API_URL}/schedule/reset/`);
        scheduleData.value = [];
        currentTeacher.value = '';
        generated.value = false;
        Swal.fire('เรียบร้อย', 'ล้างข้อมูลตารางเรียนแล้ว', 'success')
    } catch (e) {
        console.error(e);
        Swal.fire('Error', 'เกิดข้อผิดพลาดในการรีเซ็ต', 'error')
    } finally {
        isLoading.value = false;
    }
}

// --- Helper Functions ---
const findClass = (d, s) => {
    if (!scheduleData.value) return null;
    return scheduleData.value.find(i => 
        Number(i.day) === d && 
        Number(i.slot) === s && 
        i.teacher_name === currentTeacher.value
    );
}

const scheduleRows = computed(() => {
    if (!currentTeacher.value) return days.map(d => ({ ...d, slots: [] }));

    return days.map(day => {
        const rowSlots = [];
        let i = 1;
        while (i <= 12) {
            if (i === 5) {
                rowSlots.push({ type: 'lunch', colspan: 1, slot: 5 });
                i++;
                continue;
            }

            const currentClass = findClass(day.id, i);
            
            if (currentClass) {
                let span = 1;
                for (let j = i + 1; j <= 12; j++) {
                    if (j === 5) break; 
                    const nextClass = findClass(day.id, j);
                    
                    if (nextClass && 
                        nextClass.subject_code === currentClass.subject_code && 
                        nextClass.group_id === currentClass.group_id) {
                        span++;
                    } else {
                        break; 
                    }
                }
                
                rowSlots.push({ type: 'class', colspan: span, data: currentClass });
                i += span; 
            } else {
                rowSlots.push({ type: 'empty', colspan: 1 });
                i++;
            }
        }
        return { ...day, slots: rowSlots };
    });
});
</script>

<template>
<div class="min-h-screen bg-slate-50 p-4 font-sans relative overflow-x-hidden text-slate-800 flex flex-col">
    
    <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <div class="relative z-10 flex flex-wrap justify-between items-center bg-white p-4 rounded-xl shadow-md mb-6 border-t-4 border-orange-500">
        <h1 class="font-bold text-lg text-slate-800 flex items-center gap-3">
            <div class="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center text-white shadow-sm">
                <i class="fa-solid fa-calendar-days"></i>
            </div>
            <div>
                <span class="block leading-none">ระบบจัดตารางสอน (AI)</span>
                <span v-if="currentTeacher" class="text-xs text-orange-600 font-medium">
                    กำลังแสดงตารางของ: {{ currentTeacher }}
                </span>
            </div>
        </h1>
        <div class="flex gap-2 mt-4 sm:mt-0 flex-wrap">
            <button @click="goToSubjects" class="btn-nav text-blue-600 border-blue-200 hover:bg-blue-50">
                <i class="fa-solid fa-list-check"></i> วิชา
            </button>
            <button @click="goToTeacherSchedule" class="btn-nav text-purple-600 border-purple-200 hover:bg-purple-50">
                <i class="fa-solid fa-chalkboard-user"></i> ครู
            </button>
            <button @click="goToClassSchedule" class="btn-nav text-cyan-600 border-cyan-200 hover:bg-cyan-50">
                <i class="fa-solid fa-users"></i> ชั้น
            </button>
            
            <button @click="handleLogout" class="btn-nav text-red-600 border-red-200 hover:bg-red-50 ml-2">
                <i class="fa-solid fa-right-from-bracket"></i> ออกจากระบบ
            </button>
        </div>
    </div>
    
    <div class="relative z-10 mb-6">
        <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-col md:flex-row items-center justify-center gap-4">
            
            <div class="flex items-center gap-2 bg-slate-50 p-2 rounded-lg border border-slate-200">
                <div class="flex items-center gap-2">
                    <span class="text-sm font-bold text-slate-600">ภาคเรียน:</span>
                    <select v-model="selectedTerm" class="p-1.5 rounded border border-slate-300 text-sm focus:outline-orange-500 bg-white">
                        <option v-for="t in terms" :key="t" :value="t">{{ t }}</option>
                    </select>
                </div>
                <div class="w-px h-6 bg-slate-300"></div>
                <div class="flex items-center gap-2">
                    <span class="text-sm font-bold text-slate-600">ปีการศึกษา:</span>
                    <select v-model="selectedYear" class="p-1.5 rounded border border-slate-300 text-sm focus:outline-orange-500 bg-white">
                        <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
                    </select>
                </div>
            </div>

            <div class="flex flex-wrap justify-center gap-3">
                <button @click="startGenerate" :disabled="isLoading" class="btn-action bg-gradient-to-r from-orange-500 to-orange-600 shadow-orange-500/30 hover:scale-105">
                    <i v-if="isLoading" class="fa-solid fa-spinner animate-spin"></i>
                    <i v-else class="fa-solid fa-wand-magic-sparkles"></i>
                    {{ isLoading ? 'กำลังประมวลผล...' : 'สั่ง AI จัดตารางใหม่' }}
                </button>

                <button v-if="generated" @click="randomizeTeacher" class="btn-action bg-gradient-to-r from-purple-500 to-purple-600 shadow-purple-500/30 hover:scale-105">
                    <i class="fa-solid fa-shuffle"></i>
                    สุ่มครูท่านอื่น
                </button>

                <button @click="resetSchedule" :disabled="isLoading" class="btn-action bg-gradient-to-r from-red-500 to-red-600 shadow-red-500/30 hover:scale-105">
                    <i class="fa-solid fa-trash-can"></i>
                    รีเซ็ตตาราง
                </button>
            </div>
        </div>
        <p class="mt-2 text-center text-slate-500 text-xs h-4 font-medium">{{ statusMessage }}</p>
    </div>

    <div v-if="generated && currentTeacher" class="relative z-10 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden font-sarabun text-black p-4 md:p-6">
        
        <div class="mb-4 text-center">
            <h2 class="text-xl font-bold text-slate-800">ตารางสอน</h2>
            <p class="text-lg text-orange-600 font-bold">{{ currentTeacher }}</p>
            <p class="text-sm text-slate-500">ภาคเรียนที่ {{ selectedTerm }} ปีการศึกษา {{ selectedYear }}</p>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full border-collapse border border-black text-sm text-center table-fixed min-w-[1200px]">
                <thead>
                    <tr class="bg-gray-100">
                        <th class="border border-black w-24 bg-gray-200">
                            <div class="flex flex-col justify-center h-full">
                                <span>เวลา</span>
                                <div class="w-full h-px bg-black my-0.5"></div>
                                <span>วัน/คาบ</span>
                            </div>
                        </th>
                        
                        <th v-for="h in timeHeaders" :key="h.slot" class="border border-black text-[10px] px-1 font-semibold text-gray-800 relative" 
                            :class="{'bg-gray-200': h.slot === 5}">
                            <div class="font-bold">{{ h.time }}</div>
                            <div class="font-bold text-sm">{{ h.slot === 5 ? 'พักเที่ยง' : h.slot }}</div>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="day in scheduleRows" :key="day.id">
                        <td class="border border-black font-bold text-base h-24 text-black relative">
                            <div :class="day.color" class="absolute inset-0 opacity-20"></div>
                            <span class="relative z-10">{{ day.name }}</span>
                        </td>
                        
                        <td v-for="(cell, index) in day.slots" :key="index" 
                            :colspan="cell.colspan"
                            class="border border-black p-0 align-middle relative hover:bg-blue-50 transition h-24"
                            :class="{'bg-gray-300': cell.type === 'lunch'}">
                            
                            <div v-if="cell.type === 'lunch'" class="absolute inset-0 flex items-center justify-center text-gray-600 font-bold text-sm tracking-wide h-full select-none">
                                พักเที่ยง
                            </div>

                            <div v-else-if="cell.type === 'class'" class="w-full h-full flex flex-col justify-center items-center p-1 bg-white cursor-pointer hover:bg-yellow-50 relative group">
                                <div class="font-bold text-xs text-blue-800">{{ cell.data.subject_code }}</div>
                                <div class="text-[11px] font-semibold text-black leading-tight line-clamp-1 px-1 my-0.5">
                                    {{ cell.data.subject_name }}
                                </div>
                                
                                <div class="text-[10px] text-gray-600 font-medium truncate w-full text-center px-1 mb-0.5">
                                    {{ cell.data.teacher_name || '-' }}
                                </div>

                                <div class="text-[9px] mt-0.5 flex justify-between w-full px-2 text-gray-600 bg-gray-100 py-0.5 rounded-sm border border-gray-200">
                                    <span>{{ cell.data.group_id }}</span>
                                    <span class="font-bold">{{ cell.data.room || 'รอระบุ' }}</span>
                                </div>
                            </div>

                            <div v-else class="text-gray-300 text-xl font-thin select-none">-</div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div v-else class="text-center text-slate-400 py-20 border-2 border-dashed border-slate-300 rounded-2xl m-4 bg-white">
        <i class="fa-solid fa-box-open text-5xl mb-4 opacity-50 block text-slate-300"></i>
        <p class="text-lg text-slate-600">ยังไม่มีตารางเรียน</p>
        <p class="text-sm opacity-70">เลือกภาคเรียน/ปีการศึกษา แล้วกดปุ่ม "สั่ง AI จัดตารางใหม่"</p>
    </div>

</div>
</template>

<style scoped>
.font-sarabun { font-family: 'Sarabun', sans-serif; }

.btn-nav {
  background-color: #f1f5f9; 
  border: 1px solid #e2e8f0; 
  padding: 6px 12px;        
  border-radius: 0.5rem;    
  font-size: 0.75rem;       
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
  cursor: pointer;
}

@media (min-width: 640px) {
  .btn-nav { font-size: 0.875rem; }
}

.btn-action {
  color: white;
  padding: 8px 24px;        
  border-radius: 9999px;    
  font-weight: 700;          
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); 
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s;
  border: none;
  cursor: pointer;
}

.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-action:active { transform: scale(0.95); }

.overflow-x-auto::-webkit-scrollbar { height: 8px; }
.overflow-x-auto::-webkit-scrollbar-track { background: #f1f5f9; }
.overflow-x-auto::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.overflow-x-auto::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>