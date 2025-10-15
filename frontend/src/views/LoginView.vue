<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <div class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
          <GraduationCap class="h-8 w-8 text-blue-600" />
        </div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          登录到成绩管理系统
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          请使用您的学号或工号登录
        </p>
      </div>

      <form class="mt-8 space-y-6" @submit.prevent="handleLogin">
        <div class="rounded-md shadow-sm -space-y-px">
          <div>
            <label for="username" class="sr-only">用户名</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User class="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="username"
                v-model="form.username.value"
                name="username"
                type="text"
                required
                class="appearance-none rounded-none relative block w-full px-3 py-2 pl-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                :class="{ 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500': form.username.error }"
                placeholder="用户名/学号/工号"
                @blur="validateField('username')"
              />
            </div>
            <p v-if="form.username.error" class="mt-1 text-sm text-red-600">
              {{ form.username.error }}
            </p>
          </div>
          <div>
            <label for="password" class="sr-only">密码</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock class="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="password"
                v-model="form.password.value"
                name="password"
                :type="showPassword ? 'text' : 'password'"
                required
                class="appearance-none rounded-none relative block w-full px-3 py-2 pl-10 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                :class="{ 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500': form.password.error }"
                placeholder="密码"
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
          </div>
        </div>

        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <input
              id="remember"
              v-model="rememberMe"
              name="remember"
              type="checkbox"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label for="remember" class="ml-2 block text-sm text-gray-900">
              记住登录状态
            </label>
          </div>

          <div class="text-sm">
            <router-link
              to="/forgot-password"
              class="font-medium text-blue-600 hover:text-blue-500"
            >
              忘记密码？
            </router-link>
          </div>
        </div>

        <div v-if="authStore.error" class="rounded-md bg-red-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <XCircle class="h-5 w-5 text-red-400" />
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">
                登录失败
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
              <Lock v-if="!authStore.isLoading" class="h-5 w-5 text-blue-500 group-hover:text-blue-400" />
              <div v-else class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
            </span>
            {{ authStore.isLoading ? '登录中...' : '登录' }}
          </button>
        </div>

        <div class="text-center">
          <span class="text-sm text-gray-600">还没有账号？</span>
          <router-link
            to="/register"
            class="ml-1 font-medium text-blue-600 hover:text-blue-500"
          >
            立即注册
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { GraduationCap, User, Lock, Eye, EyeOff, XCircle } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const showPassword = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请输入用户名' },
      { minLength: 3, message: '用户名至少3个字符' },
    ],
  },
  password: {
    value: '',
    error: '',
    rules: [
      { required: true, message: '请输入密码' },
      { minLength: 6, message: '密码至少6个字符' },
    ],
  },
})

const validateField = (fieldName: 'username' | 'password') => {
  const field = form[fieldName]
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
  }

  return true
}

const validateForm = () => {
  const usernameValid = validateField('username')
  const passwordValid = validateField('password')
  return usernameValid && passwordValid
}

const handleLogin = async () => {
  if (!validateForm()) {
    return
  }

  const success = await authStore.login({
    username: form.username.value,
    password: form.password.value,
  })

  if (success) {
    // Redirect based on user role
    const role = authStore.userRole
    if (role === 'admin') {
      router.push('/admin')
    } else if (role === 'teacher') {
      router.push('/teacher')
    } else {
      router.push('/student')
    }
  }
}
</script>