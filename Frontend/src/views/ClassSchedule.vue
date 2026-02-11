<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

const router = useRouter()
const API_URL = 'http://127.0.0.1:8000/api'

// --- State ---
const groups = ref([])
const selectedGroup = ref('')
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

// ตัวกรองกลุ่มเรียน
const filteredGroups = computed(() => {
    return groups.value.filter(g => !g.name.includes(','))
})

// --- Table Configuration ---
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
    { id: 1, name: "จันทร์" },
    { id: 2, name: "อังคาร" },
    { id: 3, name: "พุธ" },
    { id: 4, name: "พฤหัส" },
    { id: 5, name: "ศุกร์" }
]

// --- Lifecycle ---
onMounted(() => {
    fetchGroups()
})

watch(selectedGroup, () => {
    if (selectedGroup.value) fetchSchedule()
})

const fetchGroups = async () => {
    try {
        const res = await axios.get(`${API_URL}/groups/`)
        groups.value = res.data.data 
    } catch (e) { console.error("Error fetching groups:", e) }
}

const fetchSchedule = async () => {
    if (!selectedGroup.value) return;
    isLoading.value = true
    scheduleData.value = []
    
    try {
        const encodedName = encodeURIComponent(selectedGroup.value)
        const res = await axios.get(`${API_URL}/schedule/group/${encodedName}/`)
        scheduleData.value = Array.isArray(res.data.data) ? res.data.data : []
    } catch (e) {
        console.error("Error fetching schedule:", e)
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
                    if (nextClass && nextClass.subject_code === currentClass.subject_code) {
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

// --- Export Functions (Color Fix: White Background) ---
const prepareClone = async (element) => {
    const clone = element.cloneNode(true);
    const exportWidth = '2000px'; 

    Object.assign(clone.style, { 
        position: 'fixed', top: '-9999px', left: '0', zIndex: '-9999', 
        width: exportWidth, minWidth: exportWidth, 
        padding: '30px', backgroundColor: '#ffffff', boxSizing: 'border-box', display: 'block'
    });

    const rows = clone.querySelectorAll('tr');
    rows.forEach(row => { if (!row.querySelector('th')) row.style.height = '130px'; });

    const cells = clone.querySelectorAll('td');
    cells.forEach(cell => {
        // Reset Cell Style
        cell.style.height = '100%';
        cell.style.verticalAlign = 'top';
        cell.style.padding = '0';
        cell.style.border = '1px solid #000';
        cell.style.backgroundColor = '#ffffff'; // *** บังคับสีขาวเป็นค่าเริ่มต้น ***
        
        const cellText = cell.innerText.trim();

        // --- 1. จัดการช่องพักเที่ยง ---
        if (cellText === 'พักเที่ยง') {
            cell.style.backgroundColor = '#e5e7eb'; // สีเทา
            
            const innerDiv = cell.querySelector('div');
            if (innerDiv) {
                innerDiv.style.display = 'flex';
                innerDiv.style.alignItems = 'center';     
                innerDiv.style.justifyContent = 'center'; 
                innerDiv.style.height = '100%';
                innerDiv.style.width = '100%';
                
                const span = innerDiv.querySelector('span');
                if (span) {
                    span.style.fontSize = '14px';
                    span.style.fontWeight = 'bold';
                }
            }
            return; 
        }

        // --- 2. จัดการช่องที่มีวิชาเรียน ---
        const innerDiv = cell.querySelector('div');
        if (innerDiv && innerDiv.querySelector('.text-center')) {
            // *** บังคับพื้นหลังเป็นสีขาวชัดเจน ***
            cell.style.backgroundColor = '#ffffff'; 
            
            const hoverDiv = cell.querySelector('.hover\\:bg-cyan-50'); 
            if (hoverDiv) {
                 hoverDiv.style.backgroundColor = '#ffffff'; // เปลี่ยนเป็นสีขาว
                 hoverDiv.classList.remove('hover:bg-cyan-50');
            } else if (cell.querySelector('.bg-white')) {
                 cell.querySelector('.bg-white').style.backgroundColor = '#ffffff';
            }

            // --- 3. จัด Layout (ดันครู/ห้อง ลงล่างสุด) ---
            if (!innerDiv.innerText.includes('พักเที่ยง')) {
                // ดึง Elements
                const absolutes = innerDiv.querySelectorAll('.absolute');
                let teacherEl = null;
                let roomEl = null;

                absolutes.forEach(el => {
                    if (el.className.includes('left-1')) teacherEl = el;
                    if (el.className.includes('right-1')) roomEl = el;
                });

                const textEl = innerDiv.querySelector('.text-center');

                // ปลดล็อค Text
                if (textEl) {
                    const subjectName = textEl.querySelector('.line-clamp-2');
                    if (subjectName) {
                        subjectName.classList.remove('line-clamp-2');
                        subjectName.style.whiteSpace = 'normal';
                        subjectName.style.height = 'auto';
                        subjectName.style.fontSize = '13px';
                        subjectName.style.lineHeight = '1.4';
                    }
                }

                // สร้าง Footer ใหม่
                if (teacherEl && roomEl) {
                    teacherEl.className = ''; 
                    roomEl.className = '';
                    
                    teacherEl.style.fontSize = '11px';
                    teacherEl.style.color = '#4b5563';
                    teacherEl.style.fontWeight = '600';
                    teacherEl.style.whiteSpace = 'nowrap';

                    roomEl.style.fontSize = '12px';
                    roomEl.style.fontWeight = 'bold';
                    roomEl.style.color = '#000';

                    const footerDiv = document.createElement('div');
                    footerDiv.style.display = 'flex';
                    footerDiv.style.justifyContent = 'space-between';
                    footerDiv.style.alignItems = 'flex-end'; 
                    footerDiv.style.width = '100%';
                    footerDiv.style.paddingTop = '10px'; 
                    
                    footerDiv.appendChild(teacherEl);
                    footerDiv.appendChild(roomEl);

                    innerDiv.appendChild(footerDiv);
                }

                // จัด Layout หลัก
                innerDiv.style.display = 'flex';
                innerDiv.style.flexDirection = 'column';
                innerDiv.style.justifyContent = 'space-between'; 
                innerDiv.style.height = '100%'; 
                innerDiv.style.padding = '8px 6px'; 
                innerDiv.style.boxSizing = 'border-box';
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
        const fileName = `ตารางเรียน_${selectedGroup.value}`;

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

    <div class="relative z-10 flex flex-wrap justify-between items-center bg-white p-4 rounded-xl shadow-md mb-6 border-t-4 border-cyan-500">
        <h1 class="font-bold text-lg text-slate-800 flex items-center gap-3">
            <div class="w-10 h-10 bg-cyan-500 rounded-full flex items-center justify-center text-white shadow-sm">
                <i class="fa-solid fa-users"></i>
            </div>
            <div>
                <span class="block leading-none">ตารางเรียนตามกลุ่ม</span>
                <span class="text-xs text-slate-500 font-normal">ดูตารางเรียนแยกตามชั้นปี/ห้อง</span>
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
                <label class="block text-xs font-bold text-slate-500 mb-1">เลือกกลุ่มเรียน / ชั้นปี</label>
                <div class="relative">
                    <select v-model="selectedGroup" class="w-full pl-3 pr-10 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-cyan-500">
                        <option value="" disabled>-- เลือกกลุ่มเรียน --</option>
                        <option v-for="g in filteredGroups" :key="g.id" :value="g.name">{{ g.name }}</option>
                    </select>
                    <i class="fa-solid fa-chevron-down absolute right-3 top-3 text-slate-400 text-xs"></i>
                </div>
            </div>

            <div class="flex gap-2 justify-end">
                <button @click="handleExport('pdf')" :disabled="!selectedGroup || scheduleData.length === 0 || isDownloading" 
                    class="btn-export bg-red-50 text-red-600 border-red-200 hover:bg-red-100 disabled:opacity-50">
                    <i v-if="isDownloading" class="fa-solid fa-spinner animate-spin"></i>
                    <i v-else class="fa-solid fa-file-pdf"></i> PDF
                </button>
                <button @click="handleExport('img')" :disabled="!selectedGroup || scheduleData.length === 0 || isDownloadingImg"
                    class="btn-export bg-green-50 text-green-600 border-green-200 hover:bg-green-100 disabled:opacity-50">
                    <i v-if="isDownloadingImg" class="fa-solid fa-spinner animate-spin"></i>
                    <i v-else class="fa-solid fa-image"></i> IMG
                </button>
            </div>
        </div>
    </div>

    <div ref="pdfSection" v-if="selectedGroup && scheduleData.length > 0" class="relative z-10 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden font-sarabun text-black p-6">
        
        <div class="mb-6 text-center">
             <h2 class="text-xl font-bold text-cyan-600">ตารางเรียน</h2>
             <h3 class="text-2xl font-bold text-slate-800 mt-1">{{ selectedGroup }}</h3>
             
             <p class="text-sm text-slate-600 mt-2 font-medium">
                 ภาคเรียนที่ {{ selectedTermNumber }} ปีการศึกษา {{ selectedAcademicYear }}
             </p>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full border-collapse border border-black text-sm text-center table-fixed min-w-[1200px]">
                <thead>
                    <tr class="bg-white text-black h-12">
                        <th class="border border-black w-24 bg-[#ecfeff]">
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
                        <td class="border border-black font-bold text-lg bg-[#f0fdfa]">
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

                            <div v-else-if="cell.type === 'class'" class="w-full h-full relative bg-white hover:bg-cyan-50 cursor-pointer px-1 pt-1 pb-0">
                                <div class="w-full text-center pt-2 px-1">
                                    <div class="font-bold text-sm text-blue-700 leading-tight">
                                        {{ cell.data.subject_code }}
                                    </div>
                                    <div class="text-[11px] font-bold text-black leading-tight mt-1 line-clamp-2">
                                        {{ cell.data.subject_name }}
                                    </div>
                                </div>
                                
                                <div class="absolute bottom-0.5 left-1 max-w-[70%] truncate text-[10px] text-gray-600 font-semibold leading-none" :title="cell.data.teacher_name">
                                    {{ cell.data.teacher_name }}
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

    <div v-else-if="selectedGroup && !isLoading" class="text-center text-slate-400 py-20 border-2 border-dashed border-slate-300 rounded-2xl m-4 bg-white">
        <i class="fa-regular fa-calendar-xmark text-5xl mb-4 opacity-50 block text-slate-300"></i>
        <p class="text-lg text-slate-600">ไม่พบตารางเรียน</p>
    </div>

    <div v-else-if="!selectedGroup" class="text-center text-slate-400 py-20 border-2 border-dashed border-slate-300 rounded-2xl m-4 bg-white">
        <i class="fa-solid fa-users-viewfinder text-5xl mb-4 opacity-50 block text-slate-300"></i>
        <p class="text-lg text-slate-600">กรุณาเลือกกลุ่มเรียน</p>
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