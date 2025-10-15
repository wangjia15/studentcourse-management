<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <div class="flex items-center">
            <GraduationCap class="h-8 w-8 text-blue-600 mr-3" />
            <h1 class="text-2xl font-bold text-gray-900">成绩管理系统</h1>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-700">
              欢迎，{{ authStore.userName }}
            </span>
            <span class="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
              {{ getRoleLabel(authStore.userRole) }}
            </span>
            <button
              @click="handleLogout"
              class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <LogOut class="h-4 w-4 mr-1" />
              退出登录
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <!-- User Info Card -->
      <div class="bg-white overflow-hidden shadow rounded-lg mb-6">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
            用户信息
          </h3>
          <dl class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
            <div>
              <dt class="text-sm font-medium text-gray-500">姓名</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ authStore.user?.full_name }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">用户名</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ authStore.user?.username }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">邮箱</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ authStore.user?.email }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">院系</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ authStore.user?.department || '未设置' }}</dd>
            </div>
            <div v-if="authStore.user?.student_id">
              <dt class="text-sm font-medium text-gray-500">学号</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ authStore.user.student_id }}</dd>
            </div>
            <div v-if="authStore.user?.teacher_id">
              <dt class="text-sm font-medium text-gray-500">工号</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ authStore.user.teacher_id }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Role-specific content -->
      <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <!-- Student Features -->
        <PermissionGuard :roles="['student']">
          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-6">
              <div class="flex items-center">
                <BookOpen class="h-8 w-8 text-blue-600 mr-3" />
                <h3 class="text-lg font-medium text-gray-900">我的课程</h3>
              </div>
              <p class="mt-2 text-sm text-gray-500">
                查看已选课程和课程信息
              </p>
              <div class="mt-4">
                <router-link
                  to="/student/courses"
                  class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  查看课程
                  <ArrowRight class="ml-2 h-4 w-4" />
                </router-link>
              </div>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard :roles="['student']">
          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-6">
              <div class="flex items-center">
                <FileText class="h-8 w-8 text-green-600 mr-3" />
                <h3 class="text-lg font-medium text-gray-900">我的成绩</h3>
              </div>
              <p class="mt-2 text-sm text-gray-500">
                查看各科成绩和绩点信息
              </p>
              <div class="mt-4">
                <router-link
                  to="/student/grades"
                  class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  查看成绩
                  <ArrowRight class="ml-2 h-4 w-4" />
                </router-link>
              </div>
            </div>
          </div>
        </PermissionGuard>

        <!-- Teacher Features -->
        <PermissionGuard :roles="['teacher']">
          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-6">
              <div class="flex items-center">
                <Users class="h-8 w-8 text-purple-600 mr-3" />
                <h3 class="text-lg font-medium text-gray-900">课程管理</h3>
              </div>
              <p class="mt-2 text-sm text-gray-500">
                管理课程和学生选课情况
              </p>
              <div class="mt-4">
                <router-link
                  to="/teacher/courses"
                  class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-purple-700 bg-purple-100 hover:bg-purple-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                >
                  管理课程
                  <ArrowRight class="ml-2 h-4 w-4" />
                </router-link>
              </div>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard :roles="['teacher']">
          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-6">
              <div class="flex items-center">
                <Edit class="h-8 w-8 text-orange-600 mr-3" />
                <h3 class="text-lg font-medium text-gray-900">成绩录入</h3>
              </div>
              <p class="mt-2 text-sm text-gray-500">
                录入和管理学生成绩
              </p>
              <div class="mt-4">
                <router-link
                  to="/teacher/grades"
                  class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-orange-700 bg-orange-100 hover:bg-orange-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
                >
                  录入成绩
                  <ArrowRight class="ml-2 h-4 w-4" />
                </router-link>
              </div>
            </div>
          </div>
        </PermissionGuard>

        <!-- Admin Features -->
        <PermissionGuard :roles="['admin']">
          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-6">
              <div class="flex items-center">
                <Settings class="h-8 w-8 text-red-600 mr-3" />
                <h3 class="text-lg font-medium text-gray-900">用户管理</h3>
              </div>
              <p class="mt-2 text-sm text-gray-500">
                管理系统用户和权限
              </p>
              <div class="mt-4">
                <router-link
                  to="/admin/users"
                  class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  管理用户
                  <ArrowRight class="ml-2 h-4 w-4" />
                </router-link>
              </div>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard :roles="['admin']">
          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-6">
              <div class="flex items-center">
                <Shield class="h-8 w-8 text-indigo-600 mr-3" />
                <h3 class="text-lg font-medium text-gray-900">系统设置</h3>
              </div>
              <p class="mt-2 text-sm text-gray-500">
                系统配置和维护
              </p>
              <div class="mt-4">
                <router-link
                  to="/admin/system"
                  class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  系统设置
                  <ArrowRight class="ml-2 h-4 w-4" />
                </router-link>
              </div>
            </div>
          </div>
        </PermissionGuard>
      </div>

      <!-- Quick Actions -->
      <div class="mt-8">
        <h3 class="text-lg font-medium text-gray-900 mb-4">快速操作</h3>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <router-link
            to="/profile"
            class="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow"
          >
            <User class="h-6 w-6 text-blue-600 mb-2" />
            <h4 class="text-sm font-medium text-gray-900">个人资料</h4>
          </router-link>

          <router-link
            to="/change-password"
            class="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow"
          >
            <Key class="h-6 w-6 text-green-600 mb-2" />
            <h4 class="text-sm font-medium text-gray-900">修改密码</h4>
          </router-link>

          <PermissionGuard :roles="['student']">
            <router-link
              to="/student/transcript"
              class="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <FileText class="h-6 w-6 text-purple-600 mb-2" />
              <h4 class="text-sm font-medium text-gray-900">成绩单</h4>
            </router-link>
          </PermissionGuard>

          <PermissionGuard :roles="['teacher', 'admin']">
            <router-link
              to="/admin/courses"
              class="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <BookOpen class="h-6 w-6 text-orange-600 mb-2" />
              <h4 class="text-sm font-medium text-gray-900">课程总览</h4>
            </router-link>
          </PermissionGuard>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  GraduationCap,
  LogOut,
  BookOpen,
  FileText,
  Users,
  Edit,
  Settings,
  Shield,
  User,
  Key,
  ArrowRight,
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const getRoleLabel = (role: string | null) => {
  const roleLabels: Record<string, string> = {
    admin: '管理员',
    teacher: '教师',
    student: '学生',
  }
  return roleLabels[role || ''] || '未知'
}

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>