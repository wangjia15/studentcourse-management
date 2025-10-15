import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: false }
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false, guest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { requiresAuth: false, guest: true }
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/ForgotPasswordView.vue'),
      meta: { requiresAuth: false, guest: true }
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('../views/ResetPasswordView.vue'),
      meta: { requiresAuth: false, guest: true }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/change-password',
      name: 'change-password',
      component: () => import('../views/ChangePasswordView.vue'),
      meta: { requiresAuth: true }
    },
    // Student routes
    {
      path: '/student',
      name: 'student-dashboard',
      component: () => import('../views/student/DashboardView.vue'),
      meta: { requiresAuth: true, roles: ['student'] }
    },
    {
      path: '/student/courses',
      name: 'student-courses',
      component: () => import('../views/student/CoursesView.vue'),
      meta: { requiresAuth: true, roles: ['student'] }
    },
    {
      path: '/student/grades',
      name: 'student-grades',
      component: () => import('../views/student/GradesView.vue'),
      meta: { requiresAuth: true, roles: ['student'] }
    },
    {
      path: '/student/transcript',
      name: 'student-transcript',
      component: () => import('../views/student/TranscriptView.vue'),
      meta: { requiresAuth: true, roles: ['student'] }
    },
    // Teacher routes
    {
      path: '/teacher',
      name: 'teacher-dashboard',
      component: () => import('../views/teacher/DashboardView.vue'),
      meta: { requiresAuth: true, roles: ['teacher', 'admin'] }
    },
    {
      path: '/teacher/courses',
      name: 'teacher-courses',
      component: () => import('../views/teacher/CoursesView.vue'),
      meta: { requiresAuth: true, roles: ['teacher', 'admin'] }
    },
    {
      path: '/teacher/course/:id',
      name: 'teacher-course-detail',
      component: () => import('../views/teacher/CourseDetailView.vue'),
      meta: { requiresAuth: true, roles: ['teacher', 'admin'] }
    },
    {
      path: '/teacher/grades',
      name: 'teacher-grades',
      component: () => import('../views/teacher/GradesView.vue'),
      meta: { requiresAuth: true, roles: ['teacher', 'admin'] }
    },
    // Admin routes
    {
      path: '/admin',
      name: 'admin-dashboard',
      component: () => import('../views/admin/DashboardView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] }
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('../views/admin/UsersView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] }
    },
    {
      path: '/admin/users/:id',
      name: 'admin-user-detail',
      component: () => import('../views/admin/UserDetailView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] }
    },
    {
      path: '/admin/courses',
      name: 'admin-courses',
      component: () => import('../views/admin/CoursesView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] }
    },
    {
      path: '/admin/system',
      name: 'admin-system',
      component: () => import('../views/admin/SystemView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] }
    },
    // Legacy routes for backward compatibility
    {
      path: '/students',
      name: 'students',
      component: () => import('../views/StudentListView.vue'),
      meta: { requiresAuth: true, roles: ['teacher', 'admin'] }
    }
  ]
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Initialize auth state if not already done
  if (!authStore.accessToken && localStorage.getItem('accessToken')) {
    authStore.initializeAuth()
  }

  const requiresAuth = to.meta.requiresAuth !== false // Default to true
  const isGuestRoute = to.meta.guest === true
  const requiredRoles = to.meta.roles as string[] | undefined

  // If route requires authentication and user is not authenticated
  if (requiresAuth && !authStore.isAuthenticated) {
    next({
      name: 'login',
      query: { redirect: to.fullPath }
    })
    return
  }

  // If user is authenticated and trying to access guest routes (login, register)
  if (isGuestRoute && authStore.isAuthenticated) {
    // Redirect based on user role
    const role = authStore.userRole
    if (role === 'admin') {
      next({ name: 'admin-dashboard' })
    } else if (role === 'teacher') {
      next({ name: 'teacher-dashboard' })
    } else {
      next({ name: 'student-dashboard' })
    }
    return
  }

  // If route requires specific roles
  if (requiredRoles && requiredRoles.length > 0) {
    const userRole = authStore.userRole
    if (!userRole || !requiredRoles.includes(userRole)) {
      // User doesn't have required role, redirect to appropriate dashboard
      if (userRole === 'admin') {
        next({ name: 'admin-dashboard' })
      } else if (userRole === 'teacher') {
        next({ name: 'teacher-dashboard' })
      } else if (userRole === 'student') {
        next({ name: 'student-dashboard' })
      } else {
        // If no role, redirect to login
        next({
          name: 'login',
          query: { redirect: to.fullPath }
        })
      }
      return
    }
  }

  // Check if user is verified (for routes that require verification)
  if (requiresAuth && authStore.user && !authStore.user.is_verified) {
    // Allow access to profile and change-password pages so user can get verified
    if (to.name !== 'profile' && to.name !== 'change-password') {
      next({ name: 'profile' })
      return
    }
  }

  next()
})

// Handle route errors
router.onError((error) => {
  console.error('Router error:', error)
  // You could redirect to an error page here
})

export default router