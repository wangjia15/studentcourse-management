import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// Create axios instance
export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // If error is 401 and we haven't tried to refresh token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const authStore = useAuthStore()

      // Try to refresh the token
      if (await authStore.refreshAccessToken()) {
        // Retry the original request with new token
        return api(originalRequest)
      } else {
        // Refresh failed, logout user
        authStore.clearAuth()
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

// API response types
export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// Generic API methods
export const apiClient = {
  // GET request
  get: async <T = any>(url: string, params?: any): Promise<ApiResponse<T>> => {
    const response = await api.get(url, { params })
    return {
      data: response.data,
      status: response.status,
    }
  },

  // POST request
  post: async <T = any>(url: string, data?: any): Promise<ApiResponse<T>> => {
    const response = await api.post(url, data)
    return {
      data: response.data,
      status: response.status,
    }
  },

  // PUT request
  put: async <T = any>(url: string, data?: any): Promise<ApiResponse<T>> => {
    const response = await api.put(url, data)
    return {
      data: response.data,
      status: response.status,
    }
  },

  // PATCH request
  patch: async <T = any>(url: string, data?: any): Promise<ApiResponse<T>> => {
    const response = await api.patch(url, data)
    return {
      data: response.data,
      status: response.status,
    }
  },

  // DELETE request
  delete: async <T = any>(url: string): Promise<ApiResponse<T>> => {
    const response = await api.delete(url)
    return {
      data: response.data,
      status: response.status,
    }
  },

  // File upload
  upload: async <T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<ApiResponse<T>> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })

    return {
      data: response.data,
      status: response.status,
    }
  },
}

// Authentication API endpoints
export const authApi = {
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login', credentials),

  register: (userData: any) =>
    api.post('/auth/register', userData),

  logout: () =>
    api.post('/auth/logout'),

  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),

  getCurrentUser: () =>
    api.get('/auth/me'),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post('/auth/change-password', data),

  requestPasswordReset: (email: string) =>
    api.post('/auth/password-reset', { email }),

  confirmPasswordReset: (token: string, newPassword: string) =>
    api.post('/auth/password-reset/confirm', { token, new_password: newPassword }),

  getUserPermissions: () =>
    api.get('/users/permissions'),
}

// User API endpoints
export const userApi = {
  getUsers: (params?: { skip?: number; limit?: number; role?: string }) =>
    api.get('/users', { params }),

  getUser: (userId: number) =>
    api.get(`/users/${userId}`),

  createUser: (userData: any) =>
    api.post('/users', userData),

  updateUser: (userId: number, userData: any) =>
    api.put(`/users/${userId}`, userData),

  deleteUser: (userId: number) =>
    api.delete(`/users/${userId}`),

  activateUser: (userId: number) =>
    api.post(`/users/${userId}/activate`),

  deactivateUser: (userId: number) =>
    api.post(`/users/${userId}/deactivate`),

  getCurrentUserProfile: () =>
    api.get('/users/me'),

  updateCurrentUserProfile: (userData: any) =>
    api.put('/users/me', userData),
}

// Course API endpoints
export const courseApi = {
  getCourses: (params?: any) =>
    api.get('/courses', { params }),

  getCourse: (courseId: number) =>
    api.get(`/courses/${courseId}`),

  createCourse: (courseData: any) =>
    api.post('/courses', courseData),

  updateCourse: (courseId: number, courseData: any) =>
    api.put(`/courses/${courseId}`, courseData),

  deleteCourse: (courseId: number) =>
    api.delete(`/courses/${courseId}`),

  enrollInCourse: (courseId: number) =>
    api.post(`/courses/${courseId}/enroll`),

  dropCourse: (courseId: number) =>
    api.post(`/courses/${courseId}/drop`),

  getCourseEnrollments: (courseId: number) =>
    api.get(`/courses/${courseId}/enrollments`),
}

// Grade API endpoints
export const gradeApi = {
  getGrades: (params?: any) =>
    api.get('/grades', { params }),

  getGrade: (gradeId: number) =>
    api.get(`/grades/${gradeId}`),

  createGrade: (gradeData: any) =>
    api.post('/grades', gradeData),

  updateGrade: (gradeId: number, gradeData: any) =>
    api.put(`/grades/${gradeId}`, gradeData),

  deleteGrade: (gradeId: number) =>
    api.delete(`/grades/${gradeId}`),

  getStudentGrades: (studentId?: number) =>
    api.get('/grades', { params: { student_id: studentId } }),

  getCourseGrades: (courseId: number) =>
    api.get('/grades', { params: { course_id: courseId } }),

  updateGrades: (courseId: number, updates: { updates: any[] }) =>
    api.put(`/courses/${courseId}/grades/batch`, updates),

  getCourse: (courseId: number) =>
    api.get(`/courses/${courseId}`),

  importGrades: (courseId: number, file: File) =>
    apiClient.upload(`/courses/${courseId}/grades/import`, file),

  exportGrades: (courseId: number) =>
    api.get(`/courses/${courseId}/grades/export`, { responseType: 'blob' }),
}

export default api