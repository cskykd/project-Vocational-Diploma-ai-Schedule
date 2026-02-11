<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import Swal from 'sweetalert2'
import { useRouter } from 'vue-router'

const router = useRouter()
const API_URL = 'http://127.0.0.1:8000/api'

const subjects = ref([])
const teachersList = ref([]) 
const roomsList = ref([])   // เพิ่มตัวแปรเก็บรายชื่อห้อง
const groupsList = ref([])  // เพิ่มตัวแปรเก็บรายชื่อกลุ่ม
const searchQuery = ref('')
const selectedTeacher = ref('') 
const isLoading = ref(false)

onMounted(async () => {
    await fetchInitialData()
})

const fetchInitialData = async () => {
    isLoading.value = true
    try {
        // ดึงข้อมูลวิชา, ครู, ห้อง, กลุ่มเรียน พร้อมกัน
        const [resSubjects, resTeachers, resRooms, resGroups] = await Promise.all([
            axios.get(`${API_URL}/subjects/`),
            axios.get(`${API_URL}/teachers/`),
            axios.get(`${API_URL}/rooms/`),
            axios.get(`${API_URL}/groups/`)
        ])

        if (resSubjects.data.status === 'success') {
            subjects.value = resSubjects.data.data
        }
        if (resTeachers.data.status === 'success') {
            teachersList.value = resTeachers.data.data
        }
        // เก็บข้อมูลห้องและกลุ่มเรียน
        if (resRooms.data.status === 'success') {
            roomsList.value = resRooms.data.data
        }
        if (resGroups.data.status === 'success') {
            groupsList.value = resGroups.data.data
        }

    } catch (e) {
        console.error(e)
    } finally {
        isLoading.value = false
    }
}

// --- Helper Functions สำหรับดึงชื่อ ---
const getTeacherName = (teacherData) => {
    if (!teacherData) return '-'
    if (typeof teacherData === 'object' && teacherData.name) return teacherData.name
    if (typeof teacherData === 'number' || (typeof teacherData === 'string' && !isNaN(teacherData))) {
        const found = teachersList.value.find(t => t.id == teacherData)
        return found ? found.name : '-'
    }
    return teacherData
}

const getRoomName = (roomData) => {
    if (!roomData) return null
    if (typeof roomData === 'object' && roomData.name) return roomData.name
    // ค้นหาจาก ID
    const found = roomsList.value.find(r => r.id == roomData || r.name == roomData)
    return found ? found.name : roomData
}

const getGroupName = (groupData) => {
    if (!groupData) return null
    if (typeof groupData === 'object' && groupData.name) return groupData.name
    // ค้นหาจาก ID
    const found = groupsList.value.find(g => g.id == groupData || g.name == groupData)
    return found ? found.name : groupData
}

// --- Computed ---
const uniqueTeachers = computed(() => {
    const names = subjects.value
        .map(s => getTeacherName(s.teacher))
        .filter(name => name !== '-')
    return [...new Set(names)].sort()
})

const filteredSubjects = computed(() => {
    let result = subjects.value

    if (selectedTeacher.value) {
        result = result.filter(s => getTeacherName(s.teacher) === selectedTeacher.value)
    }

    if (searchQuery.value) {
        const lowerQuery = searchQuery.value.toLowerCase()
        result = result.filter(s => {
            const tName = getTeacherName(s.teacher).toLowerCase()
            const sName = s.name.toLowerCase()
            const sCode = s.code.toLowerCase()
            return sCode.includes(lowerQuery) || sName.includes(lowerQuery) || tName.includes(lowerQuery)
        })
    }
    
    return result
})

// --- Navigation ---
const goToAddCourse = () => router.push('/add-course')
const editSubject = (id) => router.push(`/edit-course/${id}`)
const goToSchedule = () => router.push('/schedule') 

const deleteSubject = async (id) => {
    const result = await Swal.fire({
        title: 'คุณแน่ใจหรือไม่?',
        text: "ต้องการลบรายวิชานี้ใช่หรือไม่?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'ใช่, ลบเลย',
        cancelButtonText: 'ยกเลิก',
        reverseButtons: true
    })

    if (result.isConfirmed) {
        try {
            const res = await axios.delete(`${API_URL}/subjects/delete/${id}/`)
            if (res.data.status === 'success') {
                Swal.fire('ลบสำเร็จ!', '', 'success')
                fetchInitialData()
            }
        } catch (e) {
            console.error(e)
            Swal.fire('Error', 'ลบข้อมูลไม่สำเร็จ (ตรวจสอบ Server)', 'error')
        }
    }
}
</script>

<template>
<div class="min-h-screen bg-slate-50 p-6 font-sans flex justify-center">
    <div class="w-full max-w-5xl">
        
        <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-6 flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white shadow-md">
                    <i class="fa-solid fa-list"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold text-slate-800">จัดการรายวิชา</h1>
                    <p class="text-xs text-slate-500">แสดง {{ filteredSubjects.length }} รายการ</p>
                </div>
            </div>

            <div class="flex gap-3 w-full md:w-auto">
                <button @click="goToSchedule" class="px-4 py-2 bg-slate-100 text-slate-600 rounded-lg text-sm font-bold hover:bg-slate-200 transition border border-slate-200">
                    <i class="fa-solid fa-house mr-2"></i> หน้าหลัก
                </button>
                <button @click="goToAddCourse" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition shadow-md flex items-center gap-2">
                    <i class="fa-solid fa-plus"></i> เพิ่มวิชาใหม่
                </button>
            </div>
        </div>

        <div class="bg-white p-3 rounded-xl shadow-sm border border-slate-200 mb-4">
            <div class="flex flex-col md:flex-row gap-3">
                <div class="relative min-w-[250px]">
                     <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                        <i class="fa-solid fa-filter text-slate-400 text-sm"></i>
                    </div>
                    <select v-model="selectedTeacher" class="w-full pl-9 pr-8 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white cursor-pointer hover:bg-slate-50">
                        <option value="">แสดงครูผู้สอนทั้งหมด</option>
                        <option v-for="t in uniqueTeachers" :key="t" :value="t">{{ t }}</option>
                    </select>
                    <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                        <i class="fa-solid fa-chevron-down text-slate-400 text-xs"></i>
                    </div>
                </div>

                <div class="relative w-full">
                    <i class="fa-solid fa-magnifying-glass absolute left-3 top-3 text-slate-400 text-sm"></i>
                    <input v-model="searchQuery" type="text" placeholder="ค้นหา รหัส, ชื่อวิชา..." class="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition">
                </div>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-50 text-slate-600 text-xs uppercase font-bold tracking-wider border-b border-slate-200">
                            <th class="p-4 w-32">รหัส</th>
                            <th class="p-4">วิชา</th>
                            <th class="p-4">ผู้สอน</th>
                            <th class="p-4 text-center">ห้อง / กลุ่ม</th>
                            <th class="p-4 text-center w-32">จัดการ</th>
                        </tr>
                    </thead>
                    <tbody class="text-sm divide-y divide-slate-100">
                        <tr v-if="isLoading">
                            <td colspan="5" class="p-8 text-center text-slate-400">
                                <i class="fa-solid fa-spinner animate-spin mr-2"></i> กำลังโหลดข้อมูล...
                            </td>
                        </tr>
                        <tr v-else-if="filteredSubjects.length === 0">
                            <td colspan="5" class="p-8 text-center text-slate-400">
                                ไม่พบข้อมูลรายวิชา
                            </td>
                        </tr>
                        <tr v-else v-for="subject in filteredSubjects" :key="subject.id" class="hover:bg-slate-50 transition">
                            <td class="p-4 font-bold text-blue-600">
                                {{ subject.code }}
                            </td>
                            <td class="p-4 font-medium text-slate-800">
                                {{ subject.name }}
                                <div class="text-[10px] text-slate-400 mt-1">
                                    {{ subject.theory_hours }}ท {{ subject.practical_hours }}ป {{ subject.credits }}น 
                                    (รวม {{ subject.hours_per_week }} ชม.)
                                </div>
                            </td>
                            <td class="p-4 text-slate-600">
                                <div class="flex items-center gap-2">
                                    <div class="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-[10px] text-slate-500">
                                        <i class="fa-solid fa-user"></i>
                                    </div>
                                    {{ getTeacherName(subject.teacher) }}
                                </div>
                            </td>
                            <td class="p-4 text-center">
                                <div class="flex flex-col gap-1 items-center">
                                    <span v-if="getRoomName(subject.fixed_room)" class="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-[10px] font-bold border border-blue-100">
                                        <i class="fa-solid fa-door-open mr-1"></i> 
                                        {{ getRoomName(subject.fixed_room) }}
                                    </span>
                                    
                                    <span v-if="getGroupName(subject.group)" class="px-2 py-0.5 bg-purple-50 text-purple-600 rounded text-[10px] font-bold border border-purple-100">
                                        <i class="fa-solid fa-users mr-1"></i> 
                                        {{ getGroupName(subject.group) }}
                                    </span>
                                </div>
                            </td>
                            <td class="p-4 text-center">
                                <div class="flex justify-center gap-2">
                                    <button @click="editSubject(subject.id)" class="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition flex items-center justify-center border border-blue-200" title="แก้ไข">
                                        <i class="fa-solid fa-pen text-xs"></i>
                                    </button>
                                    <button @click="deleteSubject(subject.id)" class="w-8 h-8 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition flex items-center justify-center border border-red-200" title="ลบ">
                                        <i class="fa-solid fa-trash text-xs"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
</template>