/**
 * Test setup file for Vue.js testing environment
 */

import { vi } from 'vitest'
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'

// Mock Element Plus components
config.global.plugins = [ElementPlus]

// Mock Vue Router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    currentRoute: { value: { path: '/' } },
    options: {}
  }),
  useRoute: () => ({
    path: '/',
    params: {},
    query: {},
    meta: {}
  })
}))

// Mock Pinia stores
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    user: null,
    token: null,
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshToken: vi.fn()
  })
}))

vi.mock('@/stores/grade', () => ({
  useGradeStore: () => ({
    loading: false,
    saving: false,
    error: null,
    columns: [],
    rows: [],
    loadGrades: vi.fn(),
    saveGrades: vi.fn(),
    updateCell: vi.fn(),
    selectCell: vi.fn()
  })
}))

vi.mock('@/stores/student', () => ({
  useStudentStore: () => ({
    students: [],
    loading: false,
    loadStudents: vi.fn(),
    createStudent: vi.fn(),
    updateStudent: vi.fn(),
    deleteStudent: vi.fn()
  })
}))

// Mock API calls
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn()
  },
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    getProfile: vi.fn()
  },
  courseApi: {
    getCourses: vi.fn(),
    getCourse: vi.fn(),
    createCourse: vi.fn(),
    updateCourse: vi.fn(),
    deleteCourse: vi.fn()
  },
  gradeApi: {
    getGrades: vi.fn(),
    createGrade: vi.fn(),
    updateGrade: vi.fn(),
    deleteGrade: vi.fn(),
    getStatistics: vi.fn()
  }
}))

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
vi.stubGlobal('localStorage', localStorageMock)

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
vi.stubGlobal('sessionStorage', sessionStorageMock)

// Mock console methods for cleaner test output
global.console = {
  ...console,
  warn: vi.fn(),
  error: vi.fn(),
  log: vi.fn(),
}

// Add custom matchers
expect.extend({
  toHaveClass: (received, className) => {
    const pass = received.classList?.contains(className) || false
    return {
      message: () =>
        pass
          ? `expected element not to have class "${className}"`
          : `expected element to have class "${className}"`,
      pass,
    }
  },
  toBeVisible: (received) => {
    const pass = received.style?.display !== 'none' &&
                 !received.classList?.contains('hidden') &&
                 received.offsetParent !== null
    return {
      message: () =>
        pass
          ? `expected element not to be visible`
          : `expected element to be visible`,
      pass,
    }
  }
})

// Global test utilities
declare global {
  namespace Vi {
    interface JestAssertion<T = any> {
      toHaveClass(className: string): T
      toBeVisible(): T
    }
  }
}