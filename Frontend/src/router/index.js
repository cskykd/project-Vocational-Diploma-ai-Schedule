import { createRouter, createWebHistory } from "vue-router";
import LoginView from "../views/Login.vue";
import ScheduleView from "../views/Schedule.vue";
import SubjectListView from "../views/SubjectList.vue";
import AddCourseView from "../views/AddCourse.vue";
import TeacherScheduleView from "../views/TeacherSchedule.vue";

// 1. นำเข้าไฟล์ ClassScheduleView (เพิ่มบรรทัดนี้)
import ClassScheduleView from '../views/ClassSchedule.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", redirect: "/schedule" },
    { path: "/login", name: "login", component: LoginView },

    // หน้าหลัก
    {
      path: "/schedule",
      name: "schedule",
      component: ScheduleView,
      meta: { requiresAuth: true },
    },

    // หน้าจัดการรายวิชา
    {
      path: "/subjects",
      name: "subject-list",
      component: SubjectListView,
      meta: { requiresAuth: true },
    },
    {
      path: "/add-course",
      name: "add-course",
      component: AddCourseView,
      meta: { requiresAuth: true },
    },
    {
      path: "/edit-course/:id",
      name: "edit-course",
      component: AddCourseView,
      meta: { requiresAuth: true },
    },

    // หน้าตารางครู
    {
      path: "/teacher-schedule",
      name: "teacher-schedule",
      component: TeacherScheduleView,
      meta: { requiresAuth: true },
    },

    // 2. เพิ่ม Path สำหรับหน้าตารางห้อง (เพิ่มบรรทัดนี้)
   { 
  path: '/class-schedule', 
  name: 'class-schedule', 
  component: ClassScheduleView, 
  meta: { requiresAuth: true } 
},
  ],
});

export default router;
