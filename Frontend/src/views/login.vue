<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import Swal from 'sweetalert2'; // ต้อง install ก่อน: npm install sweetalert2

const router = useRouter();
const API_URL = 'http://127.0.0.1:8000/api'; 
const isLoginMode = ref(true);
const isLoading = ref(false);
const form = ref({ email: '', password: '', name: '', confirmPassword: '' });

// ฟังก์ชันแจ้งเตือนสวยๆ
const showToast = (icon, title) => {
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
    })
    Toast.fire({ icon, title })
}

const handleAuth = async () => {
    isLoading.value = true;
    try {
        if (isLoginMode.value) {
            // --- เข้าสู่ระบบ ---
            const res = await axios.post(`${API_URL}/login/`, {
                username: form.value.email,
                password: form.value.password
            });
            localStorage.setItem('access_token', res.data.access);
            localStorage.setItem('refresh_token', res.data.refresh);
            
            showToast('success', 'เข้าสู่ระบบสำเร็จ!');
            setTimeout(() => router.push('/schedule'), 1000);
            
        } else {
            // --- สมัครสมาชิก ---
            if (form.value.password !== form.value.confirmPassword) {
                throw new Error("รหัสผ่านไม่ตรงกัน");
            }

            await axios.post(`${API_URL}/register/`, {
                username: form.value.email,
                email: form.value.email,
                password: form.value.password,
                first_name: form.value.name
            });
            
            Swal.fire({
                title: 'สมัครสมาชิกสำเร็จ!',
                text: 'กรุณาเข้าสู่ระบบด้วยบัญชีใหม่ของคุณ',
                icon: 'success',
                confirmButtonColor: '#4f46e5'
            });
            
            isLoginMode.value = true;
            form.value.password = '';
            form.value.confirmPassword = '';
        }
    } catch (err) {
        console.error(err);
        let msg = "เกิดข้อผิดพลาด";
        if (err.response && err.response.data) {
             msg = Object.values(err.response.data).flat()[0];
        } else if (err.message) {
             msg = err.message;
        }
        showToast('error', msg);
    } finally {
        isLoading.value = false;
    }
};

const toggleMode = () => {
    isLoginMode.value = !isLoginMode.value;
    form.value = { email: '', password: '', name: '', confirmPassword: '' }; // เคลียร์ฟอร์ม
}
</script>

<template>
<div class="min-h-screen w-full flex items-center justify-center bg-[#f8fafc] font-kanit overflow-hidden relative">
    
    <div class="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-purple-400 rounded-full mix-blend-multiply filter blur-[100px] opacity-40 animate-blob"></div>
    <div class="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] bg-indigo-400 rounded-full mix-blend-multiply filter blur-[100px] opacity-40 animate-blob animation-delay-2000"></div>
    <div class="absolute bottom-[-20%] left-[20%] w-[600px] h-[600px] bg-pink-400 rounded-full mix-blend-multiply filter blur-[100px] opacity-40 animate-blob animation-delay-4000"></div>

    <div class="relative w-full max-w-[1000px] h-auto lg:h-[600px] m-4 bg-white/60 backdrop-blur-xl rounded-[30px] shadow-2xl border border-white/50 flex overflow-hidden">
        
        <div class="hidden lg:flex w-1/2 flex-col justify-center items-center relative p-12 bg-gradient-to-br from-indigo-600 to-violet-600 text-white overflow-hidden">
            <div class="absolute top-10 left-10 w-20 h-20 bg-white/10 rounded-full blur-xl"></div>
            <div class="absolute bottom-10 right-10 w-32 h-32 bg-white/10 rounded-full blur-xl"></div>
            
            <div class="relative z-10 text-center">
                <div class="w-24 h-24 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-6 backdrop-blur-sm shadow-lg border border-white/30">
                    <i class="fa-solid fa-calendar-check text-5xl text-white drop-shadow-md"></i>
                </div>
                <h2 class="text-4xl font-bold mb-4 tracking-wide">Class Schedule</h2>
                <p class="text-indigo-100 text-lg font-light leading-relaxed">
                    วางแผนการเรียน จัดการเวลา <br>
                    และตรวจสอบตารางสอนได้ง่ายๆ ด้วย AI
                </p>
            </div>
            
            <div class="absolute bottom-0 w-full h-1/3 bg-gradient-to-t from-black/20 to-transparent"></div>
        </div>

        <div class="w-full lg:w-1/2 p-8 sm:p-12 flex flex-col justify-center bg-white/40">
            
            <div class="mb-6 text-center lg:text-left">
                <h1 class="text-3xl font-bold text-slate-800 mb-2">
                    {{ isLoginMode ? 'ยินดีต้อนรับ!' : 'เริ่มต้นใช้งานฟรี' }}
                </h1>
                <p class="text-slate-500">
                    {{ isLoginMode ? 'กรอกข้อมูลเพื่อเข้าสู่ระบบ' : 'สมัครสมาชิกเพื่อสร้างตารางเรียนของคุณ' }}
                </p>
            </div>

            <form @submit.prevent="handleAuth" class="space-y-5">
                
                <div v-if="!isLoginMode" class="animate-fade-in-down">
                    <div class="relative">
                        <input v-model="form.name" type="text" id="name" class="peer w-full px-4 py-3 rounded-xl bg-white border-2 border-slate-200 placeholder-transparent focus:outline-none focus:border-indigo-500 text-slate-700 transition-all" placeholder="Name" required />
                        <label for="name" class="absolute left-4 -top-2.5 bg-white px-1 text-sm text-slate-500 transition-all peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-base peer-placeholder-shown:text-slate-400 peer-focus:-top-2.5 peer-focus:text-sm peer-focus:text-indigo-500">ชื่อ-นามสกุล</label>
                        <i class="fa-solid fa-user absolute right-4 top-4 text-slate-400"></i>
                    </div>
                </div>

                <div class="relative">
                    <input v-model="form.email" type="email" id="email" class="peer w-full px-4 py-3 rounded-xl bg-white border-2 border-slate-200 placeholder-transparent focus:outline-none focus:border-indigo-500 text-slate-700 transition-all" placeholder="Email" required />
                    <label for="email" class="absolute left-4 -top-2.5 bg-white px-1 text-sm text-slate-500 transition-all peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-base peer-placeholder-shown:text-slate-400 peer-focus:-top-2.5 peer-focus:text-sm peer-focus:text-indigo-500">อีเมล</label>
                    <i class="fa-solid fa-envelope absolute right-4 top-4 text-slate-400"></i>
                </div>

                <div class="relative">
                    <input v-model="form.password" type="password" id="password" class="peer w-full px-4 py-3 rounded-xl bg-white border-2 border-slate-200 placeholder-transparent focus:outline-none focus:border-indigo-500 text-slate-700 transition-all" placeholder="Password" required />
                    <label for="password" class="absolute left-4 -top-2.5 bg-white px-1 text-sm text-slate-500 transition-all peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-base peer-placeholder-shown:text-slate-400 peer-focus:-top-2.5 peer-focus:text-sm peer-focus:text-indigo-500">รหัสผ่าน</label>
                    <i class="fa-solid fa-lock absolute right-4 top-4 text-slate-400"></i>
                </div>

                <div v-if="!isLoginMode" class="animate-fade-in-down">
                    <div class="relative">
                        <input v-model="form.confirmPassword" type="password" id="confirmPassword" class="peer w-full px-4 py-3 rounded-xl bg-white border-2 border-slate-200 placeholder-transparent focus:outline-none focus:border-indigo-500 text-slate-700 transition-all" placeholder="Confirm Password" required />
                        <label for="confirmPassword" class="absolute left-4 -top-2.5 bg-white px-1 text-sm text-slate-500 transition-all peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-base peer-placeholder-shown:text-slate-400 peer-focus:-top-2.5 peer-focus:text-sm peer-focus:text-indigo-500">ยืนยันรหัสผ่าน</label>
                        <i class="fa-solid fa-shield-halved absolute right-4 top-4 text-slate-400"></i>
                    </div>
                </div>

                <div v-if="isLoginMode" class="flex justify-between items-center text-sm">
                    <label class="flex items-center text-slate-500 cursor-pointer hover:text-indigo-600">
                        <input type="checkbox" class="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 mr-2">
                        จดจำฉันไว้
                    </label>
                    <a href="#" class="text-indigo-600 font-semibold hover:underline">ลืมรหัสผ่าน?</a>
                </div>

                <button :disabled="isLoading" class="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-lg shadow-lg shadow-indigo-500/40 transition-all transform hover:-translate-y-1 active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed flex justify-center items-center gap-2">
                    <span v-if="isLoading" class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>{{ isLoginMode ? 'เข้าสู่ระบบ' : 'สมัครสมาชิก' }}</span>
                </button>
            </form>

            <div class="relative my-6">
                <div class="absolute inset-0 flex items-center">
                    <div class="w-full border-t border-slate-300"></div>
                </div>
            </div>
            <div class="mt-8 text-center text-sm text-slate-600">
                {{ isLoginMode ? 'ยังไม่มีบัญชีใช่ไหม?' : 'มีบัญชีอยู่แล้ว?' }}
                <button @click="toggleMode" class="text-indigo-600 font-bold hover:underline ml-1">
                    {{ isLoginMode ? 'สมัครสมาชิกที่นี่' : 'เข้าสู่ระบบเลย' }}
                </button>
            </div>
        </div>
    </div>
</div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap');

.font-kanit {
    font-family: 'Kanit', sans-serif;
}

/* Animation for Background Blobs */
@keyframes blob {
    0% { transform: translate(0px, 0px) scale(1); }
    33% { transform: translate(30px, -50px) scale(1.1); }
    66% { transform: translate(-20px, 20px) scale(0.9); }
    100% { transform: translate(0px, 0px) scale(1); }
}
.animate-blob {
    animation: blob 7s infinite;
}
.animation-delay-2000 {
    animation-delay: 2s;
}
.animation-delay-4000 {
    animation-delay: 4s;
}

/* Animation for Form Fields */
@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.animate-fade-in-down {
    animation: fadeInDown 0.4s ease-out forwards;
}
</style>