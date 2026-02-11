<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

const router = useRouter()
const API_URL = 'http://127.0.0.1:8000/api'

// --- State ---
const teachers = ref([])
const selectedTeacher = ref('')
const scheduleData = ref([])
const isLoading = ref(false)
const isDownloading = ref(false);
const isDownloadingImg = ref(false);
const pdfSection = ref(null);

// --- Date / Year Config ---
const currentYearAD = new Date().getFullYear()
const currentYearBE = currentYearAD + 543

const savedTerm = localStorage.getItem('ai_selectedTerm');
const savedYear = localStorage.getItem('ai_selectedYear');

const selectedTermNumber = ref(savedTerm || '1');
const selectedAcademicYear = ref(savedYear || currentYearBE.toString());

const fullTermString = computed(() => `${selectedTermNumber.value}/${selectedAcademicYear.value}`)

// --- Table Configuration ---
const timeHeaders = [
    { slot: 1, time: "08:30-09:30" },
    { slot: 2, time: "09:30-10:30" },
    { slot: 3, time: "10:30-11:30" },
    { slot: 4, time: "11:30-12:30" },
    { slot: 5, time: "12:30-13:30" },
    { slot: 6, time: "13:30-14:30" },
    { slot: 7, time: "14:30-15:30" },
    { slot: 8, time: "15:30-16:30" },
    { slot: 9, time: "16:30-17:30" },
    { slot: 10, time: "17:30-18:30" },
    { slot: 11, time: "18:30-19:30" },
    { slot: 12, time: "19:30-20:30" },
]

const days = [
    { id: 1, name: "จันทร์" },
    { id: 2, name: "อังคาร" },
    { id: 3, name: "พุธ" },
    { id: 4, name: "พฤหัส" },
    { id: 5, name: "ศุกร์" }
]

// --- Lifecycle ---
onMounted(() => {
    fetchTeachers()
})

watch(selectedTeacher, () => {
    if (selectedTeacher.value) fetchSchedule()
})

const fetchTeachers = async () => {
    try {
        const res = await axios.get(`${API_URL}/teachers/`)
        teachers.value = res.data.data 
    } catch (e) { console.error(e) }
}

const fetchSchedule = async () => {
    if (!selectedTeacher.value) return;
    isLoading.value = true
    scheduleData.value = []
    
    try {
        const encodedName = encodeURIComponent(selectedTeacher.value)
        const res = await axios.get(`${API_URL}/schedule/teacher/${encodedName}/`)
        scheduleData.value = Array.isArray(res.data.data) ? res.data.data : []
    } catch (e) {
        console.error(e)
        scheduleData.value = []
    } finally {
        isLoading.value = false
    }
}

const findClass = (d, s) => {
    if (!scheduleData.value) return null;
    return scheduleData.value.find(i => Number(i.day) === d && Number(i.slot) === s);
}

const scheduleRows = computed(() => {
    return days.map(day => {
        const rowSlots = [];
        let i = 1;
        while (i <= 12) {
            if (i === 5) {
                rowSlots.push({ type: 'lunch', colspan: 1, slot: 5 });
                i++; continue;
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
                    } else { break; }
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

// --- Export Functions (ปรับปรุง Layout ใหม่) ---
const prepareClone = async (element) => {
    const clone = element.cloneNode(true);
    const exportWidth = '1600px'; 

    Object.assign(clone.style, { 
        position: 'fixed', top: '-9999px', left: '0', zIndex: '-9999', 
        width: exportWidth, minWidth: exportWidth, 
        padding: '30px', backgroundColor: '#ffffff', boxSizing: 'border-box', display: 'block'
    });

    const rows = clone.querySelectorAll('tr');
    rows.forEach(row => { if (!row.querySelector('th')) row.style.height = '120px'; });

    const cells = clone.querySelectorAll('td');
    cells.forEach(cell => {
        cell.style.height = '100%';
        cell.style.verticalAlign = 'top';
        cell.style.position = 'relative';
        cell.style.padding = '0';
        cell.style.border = '1px solid #000';

        // Fix Background
        if (cell.classList.contains('bg-white')) cell.style.backgroundColor = '#ffffff';
        if (cell.querySelector('.bg-blue-50')) {
             const inner = cell.querySelector('.bg-blue-50');
             inner.classList.remove('hover:bg-blue-50'); 
             inner.style.backgroundColor = '#eff6ff';
        }

        // *** จัดระเบียบเนื้อหาใหม่ (ไม่ใช้ Absolute) ***
        const innerDiv = cell.querySelector('div');
        if (innerDiv) {
            if (!innerDiv.innerText.includes('พักเที่ยง')) {
                // 1. ดึง Elements เดิมออกมา
                const groupEl = innerDiv.querySelector('.absolute.bottom-0\\.5.left-1');
                const roomEl = innerDiv.querySelector('.absolute.bottom-0\\.5.right-1');
                const textEl = innerDiv.querySelector('.text-center');

                // 2. ปลดล็อค Text
                if (textEl) {
                    const subjectName = textEl.querySelector('.line-clamp-2');
                    if (subjectName) {
                        subjectName.classList.remove('line-clamp-2');
                        subjectName.style.whiteSpace = 'normal';
                        subjectName.style.height = 'auto';
                        subjectName.style.fontSize = '12px';
                    }
                }

                // 3. สร้าง Footer Container สำหรับ Group และ Room
                if (groupEl && roomEl) {
                    // ลบ Class Absolute ออก
                    groupEl.className = ''; 
                    roomEl.className = '';
                    
                    // ปรับแต่ง Style ของ Group/Room ให้สวยงาม
                    groupEl.style.fontSize = '10px';
                    groupEl.style.fontWeight = 'bold';
                    groupEl.style.padding = '2px 6px';
                    groupEl.style.backgroundColor = '#f3f4f6'; // gray-100
                    groupEl.style.borderRadius = '4px';
                    groupEl.style.border = '1px solid #d1d5db';

                    roomEl.style.fontSize = '11px';
                    roomEl.style.fontWeight = 'bold';

                    // สร้างกล่อง Footer
                    const footerDiv = document.createElement('div');
                    footerDiv.style.display = 'flex';
                    footerDiv.style.justifyContent = 'space-between';
                    footerDiv.style.alignItems = 'center';
                    footerDiv.style.marginTop = 'auto'; // ดันลงล่างสุด
                    footerDiv.style.paddingTop = '8px';
                    
                    footerDiv.appendChild(groupEl);
                    footerDiv.appendChild(roomEl);

                    // ยัดกลับเข้าไป
                    innerDiv.appendChild(footerDiv);
                }

                // 4. จัด Layout หลักของ Cell
                innerDiv.style.display = 'flex';
                innerDiv.style.flexDirection = 'column';
                innerDiv.style.justifyContent = 'space-between';
                innerDiv.style.height = '100%';
                innerDiv.style.padding = '8px';
            } else {
                cell.style.backgroundColor = '#e5e7eb';
            }
        }
    });

    document.body.appendChild(clone);
    await document.fonts.ready; 
    await new Promise(r => setTimeout(r, 800)); 
    return clone;
};

const handleExport = async (type) => {
    if (!pdfSection.value || scheduleData.value.length === 0) return;
    const isPDF = type === 'pdf';
    isPDF ? isDownloading.value = true : isDownloadingImg.value = true;
    
    try {
        const clone = await prepareClone(pdfSection.value);
        const canvas = await html2canvas(clone, { 
            scale: 2, backgroundColor: "#ffffff", useCORS: true, allowTaint: true, logging: false,
            width: clone.offsetWidth, height: clone.scrollHeight,
            windowWidth: clone.offsetWidth, windowHeight: clone.scrollHeight
        });
        
        document.body.removeChild(clone);
        const imgData = canvas.toDataURL("image/png");
        const fileName = `ตารางสอน_${selectedTeacher.value}`;

        if (isPDF) {
            const pdf = new jsPDF("l", "mm", "a4");
            const pdfWidth = 297, pdfHeight = 210;
            const imgProps = pdf.getImageProperties(imgData);
            const ratio = imgProps.width / imgProps.height;
            let pW = pdfWidth - 20, pH = pW / ratio;
            if (pH > pdfHeight - 20) { pH = pdfHeight - 20; pW = pH * ratio; }
            const x = (pdfWidth - pW) / 2, y = (pdfHeight - pH) / 2;
            pdf.addImage(imgData, "PNG", x, y, pW, pH);
            pdf.save(`${fileName}.pdf`);
        } else {
            const link = document.createElement("a");
            link.href = imgData; link.download = `${fileName}.png`; link.click();
        }
    } catch (e) { console.error(e); alert("เกิดข้อผิดพลาดในการดาวน์โหลด"); } 
    finally { isPDF ? isDownloading.value = false : isDownloadingImg.value = false; }
}

const goBack = () => router.push('/schedule')
</script>

<template>
<div class="min-h-screen bg-slate-50 p-4 font-sans relative overflow-x-hidden text-slate-800 flex flex-col">
    <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <div class="relative z-10 flex flex-wrap justify-between items-center bg-white p-4 rounded-xl shadow-md mb-6 border-t-4 border-orange-500">
        <h1 class="font-bold text-lg text-slate-800 flex items-center gap-3">
            <div class="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center text-white shadow-sm">
                <i class="fa-solid fa-chalkboard-user"></i>
            </div>
            <div>
                <span class="block leading-none">ตารางสอนรายบุคคล</span>
                <span class="text-xs text-slate-500 font-normal">ระบบค้นหาตารางเรียนสำหรับอาจารย์</span>
            </div>
        </h1>
        <div class="flex gap-2 mt-4 sm:mt-0">
             <button @click="goBack" class="btn-nav text-slate-600 border-slate-200 hover:bg-slate-50">
                <i class="fa-solid fa-arrow-left"></i> กลับหน้าหลัก
            </button>
        </div>
    </div>
    
    <div class="relative z-10 bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
            <div class="w-full">
                <label class="block text-xs font-bold text-slate-500 mb-1">ชื่ออาจารย์ผู้สอน</label>
                <div class="relative">
                    <select v-model="selectedTeacher" class="w-full pl-3 pr-10 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-orange-500">
                        <option value="" disabled>-- เลือกอาจารย์ --</option>
                        <option v-for="t in teachers" :key="t.id" :value="t.name">{{ t.name }}</option>
                    </select>
                    <i class="fa-solid fa-chevron-down absolute right-3 top-3 text-slate-400 text-xs"></i>
                </div>
            </div>

            <div class="flex gap-2 justify-end">
                <button @click="handleExport('pdf')" :disabled="!selectedTeacher || scheduleData.length === 0 || isDownloading" 
                    class="btn-export bg-red-50 text-red-600 border-red-200 hover:bg-red-100 disabled:opacity-50">
                    <i v-if="isDownloading" class="fa-solid fa-spinner animate-spin"></i>
                    <i v-else class="fa-solid fa-file-pdf"></i> PDF
                </button>
                <button @click="handleExport('img')" :disabled="!selectedTeacher || scheduleData.length === 0 || isDownloadingImg"
                    class="btn-export bg-green-50 text-green-600 border-green-200 hover:bg-green-100 disabled:opacity-50">
                    <i v-if="isDownloadingImg" class="fa-solid fa-spinner animate-spin"></i>
                    <i v-else class="fa-solid fa-image"></i> IMG
                </button>
            </div>
        </div>
    </div>

    <div ref="pdfSection" v-if="selectedTeacher && scheduleData.length > 0" class="relative z-10 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden font-sarabun text-black p-6">
        
        <div class="mb-6 text-center">
             <h2 class="text-xl font-bold text-orange-600">ตารางสอน</h2>
             <h3 class="text-2xl font-bold text-slate-800 mt-1">{{ selectedTeacher }}</h3>
             <p class="text-sm text-slate-600 mt-2 font-medium">
                 ภาคเรียนที่ {{ selectedTermNumber }} ปีการศึกษา {{ selectedAcademicYear }}
             </p>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full border-collapse border border-black text-sm text-center table-fixed min-w-[1200px]">
                <thead>
                    <tr class="bg-white text-black h-12">
                        <th class="border border-black w-24 bg-[#ffedd5]">
                            <div class="flex flex-col justify-center h-full text-xs font-bold">
                                <span>เวลา</span>
                                <div class="w-full h-px bg-black my-0.5"></div>
                                <span>วัน/คาบ</span>
                            </div>
                        </th>
                        <th v-for="h in timeHeaders" :key="h.slot" class="border border-black text-[10px] px-1 h-full relative" 
                            :class="{'bg-gray-200': h.slot === 5}">
                            <div class="font-bold">{{ h.time }}</div>
                            <div class="font-bold text-sm">{{ h.slot === 5 ? 'พักเที่ยง' : h.slot }}</div>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="day in scheduleRows" :key="day.id" class="h-28">
                        <td class="border border-black font-bold text-lg bg-[#fff7ed]">
                            {{ day.name }}
                        </td>
                        <td v-for="(cell, index) in day.slots" :key="index" 
                            :colspan="cell.colspan"
                            class="border border-black p-0 relative transition"
                            :class="{ 'bg-gray-200': cell.type === 'lunch' }"
                            style="height: 1px;"
                        >
                            <div v-if="cell.type === 'lunch'" class="w-full h-full flex items-center justify-center bg-gray-300/50">
                                <span class="text-gray-600 font-bold text-sm">พักเที่ยง</span>
                            </div>

                            <div v-else-if="cell.type === 'class'" class="w-full h-full relative bg-white hover:bg-blue-50 cursor-pointer">
                                <div class="w-full text-center pt-2 px-1">
                                    <div class="font-bold text-sm text-blue-700 leading-tight">
                                        {{ cell.data.subject_code }}
                                    </div>
                                    <div class="text-[11px] font-bold text-black leading-tight mt-1 line-clamp-2">
                                        {{ cell.data.subject_name }}
                                    </div>
                                </div>
                                
                                <div class="absolute bottom-0.5 left-1">
                                    <span class="bg-gray-100 px-1 py-0.5 rounded border border-gray-200 text-[10px] font-semibold text-gray-600">
                                        {{ cell.data.group_id }}
                                    </span>
                                </div>

                                <div class="absolute bottom-0.5 right-1 text-right font-bold text-black text-[10px] leading-none">
                                    {{ cell.data.room || '-' }}
                                </div>
                            </div>

                            <div v-else class="flex items-center justify-center h-full text-gray-300">-</div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div v-else-if="selectedTeacher && !isLoading" class="text-center text-slate-400 py-20 border-2 border-dashed border-slate-300 rounded-2xl m-4 bg-white">
        <i class="fa-regular fa-calendar-xmark text-5xl mb-4 opacity-50 block text-slate-300"></i>
        <p class="text-lg text-slate-600">ไม่พบตารางสอน</p>
    </div>

    <div v-else-if="!selectedTeacher" class="text-center text-slate-400 py-20 border-2 border-dashed border-slate-300 rounded-2xl m-4 bg-white">
        <i class="fa-solid fa-magnifying-glass text-5xl mb-4 opacity-50 block text-slate-300"></i>
        <p class="text-lg text-slate-600">กรุณาเลือกอาจารย์</p>
    </div>
</div>
</template>

<style scoped>
.font-sarabun { font-family: 'Sarabun', sans-serif; }
.btn-nav { display: flex; align-items: center; gap: 0.5rem; padding: 6px 12px; border-radius: 0.5rem; border-width: 1px; font-size: 0.875rem; transition: all 0.2s; cursor: pointer; }
.btn-export { display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 8px 16px; border-radius: 0.5rem; border-width: 1px; font-weight: 600; font-size: 0.875rem; transition: all 0.2s; cursor: pointer; }
.overflow-x-auto::-webkit-scrollbar { height: 8px; }
.overflow-x-auto::-webkit-scrollbar-track { background: #f1f5f9; }
.overflow-x-auto::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.overflow-x-auto::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>