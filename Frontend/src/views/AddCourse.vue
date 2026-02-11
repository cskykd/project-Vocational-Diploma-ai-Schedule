<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter, useRoute } from 'vue-router'
import Swal from 'sweetalert2'

const router = useRouter()
const route = useRoute()
const API_URL = 'http://127.0.0.1:8000/api'

// --- State ---
const isEditMode = ref(false)
const currentId = ref(null)

const form = ref({
    code: '',
    name: '',
    teacher: '',
    // group: '',  <-- ใช้ selectedGroups แทน
    room: '',
    theory: 0,
    practice: 0,
    credit: 0,
    day: '1',
    startSlot: '1',
    isFixed: false
})

// ตัวแปรสำหรับเก็บกลุ่มเรียนที่เลือก
const selectedGroups = ref([]) 

// ข้อมูลสำหรับ Dropdown
const masterSubjects = ref([])
const teachers = ref([])
const groups = ref([])
const rooms = ref([])
const existingSubjects = ref([]) 

const totalHours = computed(() => {
    return (Number(form.value.theory) || 0) + (Number(form.value.practice) || 0)
})

// กรองวิชาที่ยังไม่ถูกเลือก
const availableSubjects = computed(() => {
    if (isEditMode.value) return masterSubjects.value
    return masterSubjects.value.filter(subject => !existingSubjects.value.includes(subject.code))
})

// กรองกลุ่มเรียน (ซ่อนกลุ่มที่มีเครื่องหมายจุลภาค , ออกจาก Dropdown)
const availableGroups = computed(() => {
    return groups.value.filter(g => 
        !selectedGroups.value.includes(g.name) && 
        !g.name.includes(',') 
    )
})

// --- Lifecycle ---
onMounted(async () => {
    await fetchDropdowns()
    await fetchExistingSchedule()
    
    if (route.params.id) {
        isEditMode.value = true
        currentId.value = route.params.id
        await fetchSubjectDetail(route.params.id)
    }
})

// --- Functions ---
const fetchDropdowns = async () => {
    try {
        const [resSub, resTea, resGrp, resRoom] = await Promise.all([
            axios.get(`${API_URL}/master-subjects/`),
            axios.get(`${API_URL}/teachers/`),
            axios.get(`${API_URL}/groups/`),
            axios.get(`${API_URL}/rooms/`)
        ])
        masterSubjects.value = resSub.data.data
        teachers.value = resTea.data.data
        groups.value = resGrp.data.data
        rooms.value = resRoom.data.data
    } catch (e) { console.error(e) }
}

const fetchExistingSchedule = async () => {
    try {
        const res = await axios.get(`${API_URL}/subjects/`)
        const currentData = res.data.data || []
        existingSubjects.value = currentData.map(item => item.code)
    } catch (e) { console.error(e) }
}

const fetchSubjectDetail = async (id) => {
    try {
        const res = await axios.get(`${API_URL}/subjects/${id}/`)
        const data = res.data.data
        
        const resolveValue = (source, list) => {
            if (!source) return '';
            if (typeof source === 'object' && source.name) return source.name;
            if (typeof source === 'string' && isNaN(Number(source))) return source;
            const found = list.find(item => item.id == source);
            return found ? found.name : '';
        }

        const teacherName = resolveValue(data.teacher, teachers.value);
        const roomName = resolveValue(data.fixed_room, rooms.value);
        
        // แยกชื่อกลุ่ม "E5, A1" -> ["E5", "A1"] เพื่อแสดงผล
        const rawGroup = resolveValue(data.group, groups.value);
        if (rawGroup) {
            selectedGroups.value = rawGroup.includes(',') 
                ? rawGroup.split(',').map(s => s.trim()) 
                : [rawGroup];
        }

        form.value = {
            code: data.code,
            name: data.name,
            teacher: teacherName, 
            room: roomName,     
            theory: data.theory_hours,
            practice: data.practical_hours,
            credit: data.credits,
            day: data.fix_day ? String(data.fix_day) : '1',
            startSlot: data.fix_slot ? String(data.fix_slot) : '1',
            isFixed: data.is_fixed
        }

    } catch (e) {
        console.error("Load detail error:", e)
        router.push('/subjects')
    }
}

// --- Group Management Functions ---
const addGroup = (event) => {
    const value = event.target.value
    if (value && !selectedGroups.value.includes(value)) {
        selectedGroups.value.push(value)
    }
    event.target.value = "" 
}

const removeGroup = (index) => {
    selectedGroups.value.splice(index, 1)
}

// *** แก้ไข URL ในฟังก์ชันนี้ (ลบ /add/ ออก) ***
const quickAdd = async (type) => {
    let title = '', apiUrl = ''
    
    // เปลี่ยน URL ให้เป็นมาตรฐาน REST API (ไม่มี /add/)
    if (type === 'teacher') { 
        title = 'เพิ่มอาจารย์'; 
        apiUrl = `${API_URL}/teachers/`; // <-- แก้ตรงนี้
    }
    else if (type === 'group') { 
        title = 'เพิ่มกลุ่มเรียน'; 
        apiUrl = `${API_URL}/groups/`; // <-- แก้ตรงนี้
    }
    else if (type === 'room') { 
        title = 'เพิ่มห้องเรียน'; 
        apiUrl = `${API_URL}/rooms/`; // <-- แก้ตรงนี้
    }

    const { value: inputValue } = await Swal.fire({
        title: title, input: 'text', showCancelButton: true, confirmButtonText: 'บันทึก', confirmButtonColor: '#f97316'
    })

    if (inputValue) {
        try {
            await axios.post(apiUrl, { name: inputValue })
            Swal.fire('สำเร็จ', `เพิ่ม "${inputValue}" เรียบร้อย`, 'success')
            await fetchDropdowns()
            
            if (type === 'teacher') form.value.teacher = inputValue
            if (type === 'room') form.value.room = inputValue
            if (type === 'group') {
                if (!selectedGroups.value.includes(inputValue)) {
                    selectedGroups.value.push(inputValue)
                }
            }
        } catch (e) { 
            console.error(e)
            Swal.fire('Error', 'ไม่สามารถเพิ่มข้อมูลได้ (ตรวจสอบชื่อซ้ำ)', 'error') 
        }
    }
}

const onSubjectSelect = () => {
    const selected = masterSubjects.value.find(s => s.code === form.value.code)
    if (selected) {
        form.value.name = selected.name
        const findValue = (obj, keys) => {
            for (const key of keys) if (obj[key] != null) return Number(obj[key]);
            return 0;
        }
        form.value.theory = findValue(selected, ['theory', 'theory_hours', 't'])
        form.value.practice = findValue(selected, ['practice', 'practical_hours', 'p'])
        form.value.credit = findValue(selected, ['credit', 'credits', 'c'])
    }
}

const submitForm = async () => {
    try {
        if (selectedGroups.value.length === 0) {
            Swal.fire('แจ้งเตือน', 'กรุณาเลือกกลุ่มเรียนอย่างน้อย 1 กลุ่ม', 'warning')
            return
        }

        const combinedName = selectedGroups.value.join(', ')
        
        // ค้นหาว่ามีกลุ่มชื่อนี้หรือยัง
        let targetGroupId = null
        const existingGroup = groups.value.find(g => g.name === combinedName)
        
        if (existingGroup) {
            targetGroupId = existingGroup.id
        } else {
            // ถ้าไม่มี ให้ถามเพื่อสร้างใหม่
            const confirm = await Swal.fire({
                title: 'พบกลุ่มเรียนแบบใหม่',
                text: `ยังไม่มีกลุ่ม "${combinedName}" ในระบบ คุณต้องการสร้างกลุ่มเรียนรวมนี้เลยหรือไม่?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'สร้างและบันทึก',
                cancelButtonText: 'ยกเลิก',
                confirmButtonColor: '#10b981'
            })

            if (confirm.isConfirmed) {
                try {
                    // *** แก้ไข URL ตรงนี้ด้วย (ลบ /add/ ออก) ***
                    const res = await axios.post(`${API_URL}/groups/`, { name: combinedName })
                    
                    await fetchDropdowns()
                    const newGroup = groups.value.find(g => g.name === combinedName)
                    if (newGroup) targetGroupId = newGroup.id
                } catch (e) {
                    console.error(e)
                    Swal.fire('Error', 'ไม่สามารถสร้างกลุ่มเรียนใหม่ได้', 'error')
                    return
                }
            } else {
                return 
            }
        }

        if (!targetGroupId) {
            Swal.fire('Error', 'เกิดข้อผิดพลาดในการระบุ ID กลุ่มเรียน', 'error')
            return
        }

        const payload = {
            ...form.value,
            group: targetGroupId, 
            duration: totalHours.value 
        }

        if (isEditMode.value) {
            // *** สำหรับ subjects/update ปกติน่าจะใช้ /subjects/{id}/ ไม่ใช่ /update/ แต่ถ้าคุณตั้งไว้แบบนั้นก็ไม่เป็นไร
            // ถ้าใช้ Default Router ของ Django ให้ลองเปลี่ยนเป็น `${API_URL}/subjects/${currentId.value}/` (Method PUT)
            await axios.put(`${API_URL}/subjects/update/${currentId.value}/`, payload)
            Swal.fire('สำเร็จ', 'บันทึกการแก้ไขเรียบร้อย', 'success')
        } else {
            // *** ถ้า subjects ใช้ /add/ ได้อยู่แล้ว ก็ไม่ต้องแก้ตรงนี้ ***
            await axios.post(`${API_URL}/subjects/add/`, payload)
            Swal.fire('สำเร็จ', 'เพิ่มรายวิชาเรียบร้อย', 'success')
        }
        
        router.push('/subjects')

    } catch (e) {
        console.error("Submit Error:", e.response ? e.response.data : e)
        let msg = 'เกิดข้อผิดพลาดในการบันทึก'
        if (e.response && e.response.data && e.response.data.group) {
            msg = `ข้อมูลกลุ่มเรียนไม่ถูกต้อง: ${e.response.data.group}`
        }
        Swal.fire('Error', msg, 'error')
    }
}

const goBack = () => router.push('/subjects')
</script>

<template>
<div class="min-h-screen bg-slate-50 p-6 font-sans flex justify-center">
    <div class="w-full max-w-3xl">
        <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-6 flex justify-between items-center">
            <div>
                <h1 class="text-xl font-bold text-slate-800">{{ isEditMode ? 'แก้ไขรายวิชาเรียน' : 'เพิ่มรายวิชาเรียน' }}</h1>
                <p class="text-xs text-slate-500">จัดการตารางสอน / {{ isEditMode ? 'แก้ไขข้อมูล' : 'เพิ่มรายวิชาใหม่' }}</p>
            </div>
            <button @click="goBack" class="px-4 py-2 bg-slate-100 text-slate-600 rounded-lg text-sm font-bold hover:bg-slate-200 transition">
                <i class="fa-solid fa-arrow-left mr-2"></i> กลับ
            </button>
        </div>

        <div class="bg-white rounded-xl shadow-lg border-t-4 border-orange-500 overflow-hidden">
            <div class="bg-orange-600 px-6 py-3">
                <h2 class="text-white font-bold text-sm"><i class="fa-solid fa-pen-to-square mr-2"></i> แบบฟอร์มข้อมูลการสอน</h2>
            </div>
            <div class="p-8">
                <div class="bg-orange-50 p-6 rounded-xl border border-orange-100 mb-6">
                    <label class="block text-sm font-bold text-orange-800 mb-2"><i class="fa-solid fa-book mr-1"></i> รายวิชา <span class="text-red-500">*</span></label>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
                        <div>
                            <div v-if="isEditMode" class="grid grid-cols-2 gap-2">
                                 <div><label class="text-xs text-slate-500">รหัสวิชา</label><input v-model="form.code" type="text" class="w-full p-2.5 border rounded bg-slate-200 text-slate-600 text-sm" readonly></div>
                                 <div><label class="text-xs text-slate-500">ชื่อวิชา</label><input v-model="form.name" type="text" class="w-full p-2.5 border rounded bg-slate-200 text-slate-600 text-sm" readonly></div>
                            </div>
                            <select v-else v-model="form.code" @change="onSubjectSelect" class="w-full p-3 border border-orange-200 rounded-lg focus:ring-2 focus:ring-orange-400 focus:outline-none bg-white">
                                <option value="" disabled>-- กรุณาเลือกวิชาจากหลักสูตร --</option>
                                <option v-for="s in availableSubjects" :key="s.id" :value="s.code">{{ s.code }} - {{ s.name }}</option>
                            </select>
                        </div>
                        <div class="grid grid-cols-4 gap-2 text-center">
                            <div class="bg-white p-2 rounded border border-orange-100 shadow-sm"><label class="block text-[10px] text-slate-500 mb-1">ทฤษฎี</label><input v-model="form.theory" class="w-full text-center font-bold text-sm outline-none bg-transparent" readonly></div>
                            <div class="bg-white p-2 rounded border border-orange-100 shadow-sm"><label class="block text-[10px] text-slate-500 mb-1">ปฏิบัติ</label><input v-model="form.practice" class="w-full text-center font-bold text-sm outline-none bg-transparent" readonly></div>
                            <div class="bg-white p-2 rounded border border-orange-100 shadow-sm"><label class="block text-[10px] text-slate-500 mb-1">หน่วยกิต</label><input v-model="form.credit" class="w-full text-center font-bold text-sm outline-none bg-transparent" readonly></div>
                            <div class="bg-orange-500 p-2 rounded border border-orange-600 text-white shadow-sm flex flex-col justify-center"><label class="block text-[9px] opacity-90 leading-tight">รวมชม.</label><div class="font-bold text-lg leading-none mt-1">{{ totalHours }}</div></div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                        <h3 class="text-sm font-bold text-blue-600 mb-4 flex items-center"><i class="fa-regular fa-calendar-days mr-2"></i> วันและเวลาเรียน</h3>
                        <div class="grid grid-cols-2 gap-2 mb-4">
                            <div><label class="text-xs text-slate-500 mb-1 block">วันเรียน</label>
                                <select v-model="form.day" class="w-full p-2 border rounded bg-slate-50">
                                    <option value="1">วันจันทร์</option><option value="2">วันอังคาร</option><option value="3">วันพุธ</option><option value="4">วันพฤหัสบดี</option><option value="5">วันศุกร์</option>
                                </select>
                            </div>
                            <div><label class="text-xs text-slate-500 mb-1 block">เริ่มคาบที่</label>
                                <select v-model="form.startSlot" class="w-full p-2 border rounded bg-slate-50">
                                    <option v-for="n in 12" :key="n" :value="n">คาบที่ {{ n }}</option>
                                </select>
                            </div>
                        </div>
                        <div class="mb-4"><label class="text-xs text-slate-500 mb-1 block">จำนวนคาบ</label><input :value="totalHours" type="text" class="w-full p-2 border rounded bg-slate-100 text-slate-500" readonly></div>
                        <div class="flex items-center gap-2 p-3 bg-slate-50 rounded border border-slate-200 cursor-pointer" @click="form.isFixed = !form.isFixed">
                            <input type="checkbox" v-model="form.isFixed" class="w-4 h-4 text-orange-500 rounded focus:ring-0"><span class="text-sm text-slate-700 font-medium">ล็อกวัน/เวลาตามนี้ (Fixed)</span>
                        </div>
                    </div>

                    <div>
                        <h3 class="text-sm font-bold text-green-600 mb-4 flex items-center"><i class="fa-solid fa-chalkboard-user mr-2"></i> ผู้สอนและกลุ่มเรียน</h3>
                        <div class="space-y-3">
                            <div>
                                <label class="text-xs text-slate-500 mb-1 block">ครูผู้สอน <span class="text-red-500">*</span></label>
                                <div class="flex gap-1">
                                    <select v-model="form.teacher" class="w-full p-2 border rounded bg-white">
                                        <option value="" disabled>-- เลือกครูผู้สอน --</option>
                                        <option v-for="t in teachers" :key="t.id" :value="t.name">{{ t.name }}</option>
                                    </select>
                                    <button @click.prevent="quickAdd('teacher')" class="bg-green-500 text-white px-3 rounded hover:bg-green-600 transition"><i class="fa-solid fa-plus"></i></button>
                                </div>
                            </div>

                            <div>
                                <label class="text-xs text-slate-500 mb-1 block">กลุ่มเรียน (เลือกได้หลายกลุ่ม) <span class="text-red-500">*</span></label>
                                
                                <div class="flex flex-wrap gap-2 mb-2 p-2 bg-slate-50 border border-slate-200 rounded min-h-[42px]">
                                    <span v-if="selectedGroups.length === 0" class="text-xs text-slate-400 italic py-1">ยังไม่ได้เลือกกลุ่มเรียน...</span>
                                    <div v-for="(grp, idx) in selectedGroups" :key="idx" class="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded flex items-center gap-1 shadow-sm">
                                        {{ grp }}
                                        <button @click="removeGroup(idx)" class="text-blue-400 hover:text-red-500 ml-1"><i class="fa-solid fa-times"></i></button>
                                    </div>
                                </div>

                                <div class="flex gap-1">
                                    <select @change="addGroup" class="w-full p-2 border rounded bg-white focus:ring-2 focus:ring-blue-300 outline-none">
                                        <option value="" selected>-- เลือกเพิ่มกลุ่มเรียน --</option>
                                        <option v-for="g in availableGroups" :key="g.id" :value="g.name">{{ g.name }}</option>
                                    </select>
                                    <button @click.prevent="quickAdd('group')" class="bg-blue-500 text-white px-3 rounded hover:bg-blue-600 transition"><i class="fa-solid fa-plus"></i></button>
                                </div>
                            </div>

                            <div>
                                <label class="text-xs text-slate-500 mb-1 block">ห้องเรียน</label>
                                <div class="flex gap-1">
                                    <select v-model="form.room" class="w-full p-2 border rounded bg-white">
                                        <option value="">-- ไม่ระบุ / ระบบจัดให้ --</option>
                                        <option v-for="r in rooms" :key="r.id" :value="r.name">{{ r.name }}</option>
                                    </select>
                                    <button @click.prevent="quickAdd('room')" class="bg-purple-500 text-white px-3 rounded hover:bg-purple-600 transition"><i class="fa-solid fa-plus"></i></button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-slate-50 px-8 py-4 border-t border-slate-200 flex justify-between">
                <button @click="goBack" class="px-6 py-2 bg-white border border-slate-300 text-slate-600 font-bold rounded-lg hover:bg-slate-50 transition">ยกเลิก</button>
                <button @click="submitForm" class="px-8 py-2 bg-orange-500 text-white font-bold rounded-lg shadow-md hover:bg-orange-600 transform hover:scale-105 transition"><i class="fa-solid fa-cloud-arrow-up mr-2"></i> {{ isEditMode ? 'บันทึกการแก้ไข' : 'บันทึกข้อมูลเข้าตาราง' }}</button>
            </div>
        </div>
    </div>
</div>
</template>