import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/lib/api'
import type { User, LoginCredentials, RegisterData } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const userRole = computed(() => user.value?.role || null)
  const userName = computed(() => user.value?.full_name || user.value?.username || '')
  const userEmail = computed(() => user.value?.email || '')

  // Check if token is expired
  const isTokenExpired = (token: string): boolean => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const now = Date.now() / 1000
      return payload.exp < now
    } catch {
      return true
    }
  }

  // Initialize auth state from localStorage
  const initializeAuth = () => {
    const storedAccessToken = localStorage.getItem('accessToken')
    const storedRefreshToken = localStorage.getItem('refreshToken')
    const storedUser = localStorage.getItem('user')

    if (storedAccessToken && !isTokenExpired(storedAccessToken)) {
      accessToken.value = storedAccessToken
      refreshToken.value = storedRefreshToken
      if (storedUser) {
        user.value = JSON.parse(storedUser)
      }
    } else {
      // Clear invalid tokens
      clearAuth()
    }
  }

  // Store auth state to localStorage
  const persistAuth = () => {
    if (accessToken.value) {
      localStorage.setItem('accessToken', accessToken.value)
    }
    if (refreshToken.value) {
      localStorage.setItem('refreshToken', refreshToken.value)
    }
    if (user.value) {
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  }

  // Clear auth state
  const clearAuth = () => {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    error.value = null
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
  }

  // Set new tokens
  const setTokens = (access: string, refresh: string) => {
    accessToken.value = access
    refreshToken.value = refresh
    persistAuth()
  }

  // Set user data
  const setUser = (userData: User) => {
    user.value = userData
    persistAuth()
  }

  // Auto-refresh token
  const refreshAccessToken = async (): Promise<boolean> => {
    if (!refreshToken.value) {
      return false
    }

    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken.value
      })

      const { access_token, refresh_token } = response.data
      setTokens(access_token, refresh_token || refreshToken.value)
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearAuth()
      return false
    }
  }

  // Setup automatic token refresh
  const setupTokenRefresh = () => {
    if (!accessToken.value) return

    // Check token expiration every minute
    setInterval(async () => {
      if (accessToken.value && isTokenExpired(accessToken.value)) {
        await refreshAccessToken()
      }
    }, 60000) // Check every minute
  }

  // Login
  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      const { access_token, refresh_token, expires_in } = response.data
      setTokens(access_token, refresh_token)

      // Get user info
      await fetchCurrentUser()

      // Setup automatic token refresh
      setupTokenRefresh()

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  // Register
  const register = async (userData: RegisterData): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.post('/auth/register', userData)
      setUser(response.data)
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Registration failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  // Logout
  const logout = async (): Promise<void> => {
    try {
      if (accessToken.value) {
        await api.post('/auth/logout')
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
    }
  }

  // Fetch current user
  const fetchCurrentUser = async (): Promise<void> => {
    if (!accessToken.value) return

    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      // Try to refresh token
      if (await refreshAccessToken()) {
        // Retry fetching user
        try {
          const response = await api.get('/auth/me')
          setUser(response.data)
        } catch (retryError) {
          console.error('Failed to fetch user after token refresh:', retryError)
          clearAuth()
        }
      } else {
        clearAuth()
      }
    }
  }

  // Change password
  const changePassword = async (currentPassword: string, newPassword: string): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Password change failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  // Request password reset
  const requestPasswordReset = async (email: string): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      await api.post('/auth/password-reset', { email })
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Password reset request failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  // Confirm password reset
  const confirmPasswordReset = async (token: string, newPassword: string): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      await api.post('/auth/password-reset/confirm', {
        token,
        new_password: newPassword,
      })
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Password reset failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  // Check permissions
  const hasPermission = (permission: string): boolean => {
    if (!user.value) return false

    // This would be based on the user's role and permissions from the backend
    // For now, return basic role-based permissions
    const role = user.value.role
    const permissions: Record<string, string[]> = {
      admin: ['read_users', 'create_users', 'update_users', 'delete_users', 'manage_courses', 'manage_grades'],
      teacher: ['manage_courses', 'manage_grades', 'view_students'],
      student: ['view_grades', 'enroll_courses', 'view_profile'],
    }

    return permissions[role]?.includes(permission) || false
  }

  // Check role
  const hasRole = (role: string): boolean => {
    return user.value?.role === role
  }

  // Initialize on store creation
  initializeAuth()

  return {
    // State
    user,
    accessToken,
    refreshToken,
    isLoading,
    error,

    // Getters
    isAuthenticated,
    userRole,
    userName,
    userEmail,

    // Actions
    login,
    register,
    logout,
    fetchCurrentUser,
    changePassword,
    requestPasswordReset,
    confirmPasswordReset,
    refreshAccessToken,
    hasPermission,
    hasRole,
    clearAuth,
    initializeAuth,
  }
})