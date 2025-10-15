<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-2xl w-full space-y-8">
      <div>
        <div class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
          <GraduationCap class="h-8 w-8 text-blue-600" />
        </div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          注册新账号
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          请填写以下信息完成注册
        </p>
      </div>

      <form class="mt-8 space-y-6" @submit.prevent="handleRegister">
        <!-- Basic Information -->
        <div class="space-y-4">
          <h3 class="text-lg font-medium text-gray-900">基本信息</h3>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label for="email" class="block text-sm font-medium text-gray-700">
                邮箱地址 *
              </label>
              <div class="mt-1 relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail class="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  v-model="form.email.value"
                  name="email"
                  type="email"
                  required
                  class="appearance-none relative block w-full px-3 py-2 pl-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  :class="{ 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500': form.email.error }"
                  placeholder="your.email@edu.cn"
                  @blur="validateField('email')"
                />
              </div>
              <p v-if="form.email.error" class="mt-1 text-sm text-red-600">
                {{ form.email.error }}
              </p>
            </div>

            <div>
              <label for="username" class="block text-sm font-medium text-gray-700">
                用户名 *
              </label>
              <div class="mt-1 relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User class="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="username"
                  v-model="form.username.value"
                  name="username"
                  type="text"
                  required
                  class="appearance-none relative block w-full px-3 py-2 pl-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  :class="{ 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500': form.username.error }"
                  placeholder="用户名"
                  @blur="validateField('username')"
                />
              </div>
              <p v-if="form.username.error" class="mt-1 text-sm text-red-600">
                {{ form.username.error }}
              </p>
            </div>
          </div>

          <div>
            <label for="full_name" class="block text-sm font-medium text-gray-700">
              中文姓名 *
            </label>
            <div class="mt-1 relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User class="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="full_name"
                v-model="form.full_name.value"
                name="full_name"
                type="text"
                required
                class="appearance-none relative block w-full px-3 py-2 pl-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                :class="{ 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500': form.full_name.error }"
                placeholder="张三"
                @blur="validateField('full_name')"
              />
            </div>
            <p v-if="form.full_name.error" class="mt-1 text-sm text-red-600">
              {{ form.full_name.error }}
            </p>
          </div>

          <div>
            <label for="role" class="block text-sm font-medium text-gray-700">
              用户身份 *
            </label>
            <select
              id="role"
              v-model="form.role"
              name="role"
              required
              class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              @change="handleRoleChange"
            >
              <option value="student">学生</option>
              <option value="teacher">教师</option>
            </select>
          </div>
        </div>

        <!-- Academic Information -->
        <div class="space-y-4">
          <h3 class="text-lg font-medium text-gray-900">学术信息</h3>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label for="department" class="block text-sm font-medium text-gray-700">
                院系 *
              </label>
              <input
                id="department"
                v-model="form.department.value"
                name="department"
                type="text"
                required
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                :class="{ 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500': form.department.error }"
                placeholder="计算机科学与技术学院"
                @blur="validateField('department')"
              />
              <p v-if="form.department.error" class="mt-1 text-sm text-red-600">
                {{ form.department.error }}
              </p>
            </div>

            <div v-if="form.role === 'student'">
              <label for="major" class="block text-sm font-medium text-gray-700">
                专业
              </label>
              <input
                id="major"
                v-model="form.major.value"
                name="major"
                type="text"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="计算机科学与技术"
              />
            </div>

            <div v-if="form.role === 'student'">
              <label for="class_name" class="block text-sm font-medium text-gray-700">
                班级
              </label>
              <input
                id="class_name"
                v-model="form.class_name.value"
                name="class_name"
                type="text"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="计科2101班"
              />
            </div>
          </div>

          <!-- Student ID or Teacher ID -->
          <div>
            <label :for="form.role === 'student' ? 'student_id' : 'teacher_id'" class="block text-sm font-medium text-gray-700">
              {{ form.role === 'student' ? '学号' : '工号' }} *
            </label>
            <div class="mt-1 relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <IdCard class="h-5 w-5 text-gray-400" />
              </div>
              <input
                :id="form.role === 'student' ? 'student_id' : 'teacher_id'"
                v-model="idField.value"
                :name="form.role === 'student' ? 'student_id' : 'teacher_id'"
                type="text"
                required
                class="appearance-none relative block w-full px-3 py-2 pl-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                :class="{ 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500': idField.error }"
                :placeholder="form.role === 'student' ? '2021001001' : '123456'"
                @blur="validateIdField"
              />
            </div>
            <p v-if="idField.error" class="mt-1 text-sm text-red-600">
              {{ idField.error }}
            </p>
          </div>

          <div v-if="form.role === 'student'">
            <label for="enrollment_year" class="block text-sm font-medium text-gray-700">
              入学年份
            </label>
            <input
              id="enrollment_year"
              v-model="form.enrollment_year.value"
              name="enrollment_year"
              type="text"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="2021"
            />
          </div>
        </div>

        <!-- Password Information -->
        <div class="space-y-4">
          <h3 class="text-lg font-medium text-gray-900">密码设置</h3>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label for="password" class="block text-sm font-medium text-gray-700">
                密码 *
              </label>
              <div class="mt-1 relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock class="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  v-model="form.password.value"
                  name="password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  class="appearance-none relative block w-full px-3 py-2 pl-10 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  :class="{ 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500': form.password.error }"
                  placeholder="••••••••"
                  @blur="validateField('password')"
                />
                <div class="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <button
                    type="button"
                    class="text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500"
                    @click="showPassword = !showPassword"
                  >
                    <Eye v-if="!showPassword" class="h-5 w-5" />
                    <EyeOff v-else class="h-5 w-5" />
                  </button>
                </div>
              </div>
              <p v-if="form.password.error" class="mt-1 text-sm text-red-600">
                {{ form.password.error }}
              </p>
              <p class="mt-1 text-xs text-gray-500">
                密码需包含大小写字母、数字，至少8位
              </p>
            </div>

            <div>
              <label for="confirm_password" class="block text-sm font-medium text-gray-700">
                确认密码 *
              </label>
              <div class="mt-1 relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock class="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="confirm_password"
                  v-model="form.confirmPassword.value"
                  name="confirm_password"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  required
                  class="appearance-none relative block w-full px-3 py-2 pl-10 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  :class="{ 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500': form.confirmPassword.error }"
                  placeholder="••••••••"
                  @blur="validateField('confirmPassword')"
                />
                <div class="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <button
                    type="button"
                    class="text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500"
                    @click="showConfirmPassword = !showConfirmPassword"
                  >
                    <Eye v-if="!showConfirmPassword" class="h-5 w-5" />
                    <EyeOff v-else class="h-5 w-5" />
                  </button>
                </div>
              </div>
              <p v-if="form.confirmPassword.error" class="mt-1 text-sm text-red-600">
                {{ form.confirmPassword.error }}
              </p>
            </div>
          </div>
        </div>

        <div v-if="authStore.error" class="rounded-md bg-red-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <XCircle class="h-5 w-5 text-red-400" />
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">
                注册失败
              </h3>
              <div class="mt-2 text-sm text-red-700">
                {{ authStore.error }}
              </div>
            </div>
          </div>
        </div>

        <div>
          <button
            type="submit"
            :disabled="authStore.isLoading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="absolute left-0 inset-y-0 flex items-center pl-3">
              <UserPlus v-if="!authStore.isLoading" class="h-5 w-5 text-blue-500 group-hover:text-blue-400" />
              <div v-else class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
            </span>
            {{ authStore.isLoading ? '注册中...' : '注册' }}
          </button>
        </div>

        <div class="text-center">
          <span class="text-sm text-gray-600">已有账号？</span>
          <router-link
            to="/login"
            class="ml-1 font-medium text-blue-600 hover:text-blue-500"
          >
            立即登录
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { GraduationCap, User, Mail, Lock, Eye, EyeOff, IdCard, UserPlus, XCircle } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const showPassword = ref(false)
const showConfirmPassword = ref(false)

const form = reactive({
  email: {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请输入邮箱地址' },
      { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '请输入有效的邮箱地址' },
      { pattern: /^[^\s@]+@(.*\.)?edu\.cn$/, message: '请输入有效的教育邮箱地址' },
    ],
  },
  username: {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请输入用户名' },
      { minLength: 3, message: '用户名至少3个字符' },
      { maxLength: 50, message: '用户名最多50个字符' },
      { pattern: /^[a-zA-Z0-9_-]+$/, message: '用户名只能包含字母、数字、下划线和连字符' },
    ],
  },
  full_name: {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请输入中文姓名' },
      { pattern: /^[\u4e00-\u9fff]+$/, message: '姓名必须包含中文字符' },
    ],
  },
  role: 'student' as 'student' | 'teacher',
  department: {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请输入院系' },
    ],
  },
  major: {
    value: '',
    error: '',
    rules: [],
  },
  class_name: {
    value: '',
    error: '',
    rules: [],
  },
  enrollment_year: {
    value: '',
    error: '',
    rules: [],
  },
  password: {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请输入密码' },
      { minLength: 8, message: '密码至少8个字符' },
      { maxLength: 128, message: '密码最多128个字符' },
      { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: '密码必须包含大小写字母和数字' },
    ],
  },
  confirmPassword: {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请确认密码' },
    ],
  },
})

const idField = computed(() => {
  return form.role === 'student' ? {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请输入学号' },
      { pattern: /^20[0-9]{2}[0-9]{4,8}$/, message: '请输入有效的学号格式' },
    ],
  } : {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请输入工号' },
      { pattern: /^[0-9]{6,10}$/, message: '请输入有效的工号格式' },
    ],
  }
})

const validateField = (fieldName: string) => {
  const field = (form as any)[fieldName]
  if (!field) return true

  field.error = ''

  for (const rule of field.rules) {
    if (rule.required && !field.value.trim()) {
      field.error = rule.message
      return false
    }
    if (rule.minLength && field.value.length < rule.minLength) {
      field.error = rule.message
      return false
    }
    if (rule.maxLength && field.value.length > rule.maxLength) {
      field.error = rule.message
      return false
    }
    if (rule.pattern && !rule.pattern.test(field.value)) {
      field.error = rule.message
      return false
    }
  }

  return true
}

const validateIdField = () => {
  const field = idField.value
  field.error = ''

  for (const rule of field.rules) {
    if (rule.required && !field.value.trim()) {
      field.error = rule.message
      return false
    }
    if (rule.pattern && !rule.pattern.test(field.value)) {
      field.error = rule.message
      return false
    }
  }

  return true
}

const validatePasswordMatch = () => {
  if (form.password.value !== form.confirmPassword.value) {
    form.confirmPassword.error = '两次输入的密码不一致'
    return false
  }
  return true
}

const validateForm = () => {
  const fieldsValid = ['email', 'username', 'full_name', 'department', 'password'].every(validateField)
  const idValid = validateIdField()
  const passwordMatchValid = validatePasswordMatch()

  return fieldsValid && idValid && passwordMatchValid
}

const handleRoleChange = () => {
  // Clear errors when role changes
  idField.value.error = ''
}

const handleRegister = async () => {
  if (!validateForm()) {
    return
  }

  const userData = {
    email: form.email.value,
    username: form.username.value,
    full_name: form.full_name.value,
    password: form.password.value,
    role: form.role,
    department: form.department.value,
    ...(form.role === 'student' ? {
      student_id: idField.value.value,
      major: form.major.value,
      class_name: form.class_name.value,
      enrollment_year: form.enrollment_year.value,
    } : {
      teacher_id: idField.value.value,
    }),
  }

  const success = await authStore.register(userData)

  if (success) {
    router.push('/login')
  }
}
</script>