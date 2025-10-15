import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import LoginView from '../LoginView.vue'
import { useAuthStore } from '@/stores/auth'

// Mock the auth store
vi.mock('@/stores/auth')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } }
  ]
})

describe('LoginView', () => {
  let wrapper: any
  let mockStore: any

  beforeEach(() => {
    // Create a fresh Pinia instance
    const pinia = createPinia()

    // Mock store
    mockStore = {
      loading: false,
      error: null,
      login: vi.fn().mockResolvedValue(undefined),
      clearError: vi.fn()
    }

    vi.mocked(useAuthStore).mockReturnValue(mockStore)

    wrapper = mount(LoginView, {
      global: {
        plugins: [pinia, router],
        stubs: {
          'router-link': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
          'el-checkbox': true,
          'el-card': true
        }
      }
    })
  })

  it('renders login form correctly', () => {
    expect(wrapper.find('h2').text()).toBe('用户登录')
    expect(wrapper.find('form').exists()).toBe(true)
  })

  it('has correct form fields', () => {
    // Check for username input
    const usernameInput = wrapper.find('input[placeholder="请输入用户名"]')
    expect(usernameInput.exists()).toBe(true)

    // Check for password input
    const passwordInput = wrapper.find('input[type="password"]')
    expect(passwordInput.exists()).toBe(true)

    // Check for remember me checkbox
    const rememberCheckbox = wrapper.find('input[type="checkbox"]')
    expect(rememberCheckbox.exists()).toBe(true)

    // Check for login button
    const loginButton = wrapper.find('button[type="submit"]')
    expect(loginButton.exists()).toBe(true)
    expect(loginButton.text()).toBe('登录')
  })

  it('displays loading state correctly', async () => {
    mockStore.loading = true
    await wrapper.vm.$nextTick()

    const loginButton = wrapper.find('button[type="submit"]')
    expect(loginButton.attributes('loading')).toBeDefined()
    expect(loginButton.text()).toContain('登录中')
  })

  it('displays error message when login fails', async () => {
    mockStore.error = '用户名或密码错误'
    await wrapper.vm.$nextTick()

    const errorAlert = wrapper.find('.el-alert')
    expect(errorAlert.exists()).toBe(true)
    expect(wrapper.text()).toContain('用户名或密码错误')
  })

  it('validates form fields', async () => {
    // Try to submit empty form
    const form = wrapper.find('form')
    await form.trigger('submit')

    // Should show validation errors
    expect(wrapper.vm.form.errors.username).toBeDefined()
    expect(wrapper.vm.form.errors.password).toBeDefined()
  })

  it('submits form with valid data', async () => {
    // Fill in form data
    await wrapper.setData({
      form: {
        username: 'testuser',
        password: 'password123',
        remember: true
      }
    })

    const form = wrapper.find('form')
    await form.trigger('submit')

    // Should call login method with correct data
    expect(mockStore.login).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'password123',
      remember: true
    })
  })

  it('clears error when user starts typing', async () => {
    // Set initial error
    mockStore.error = 'Previous error'
    await wrapper.vm.$nextTick()

    // Type in username field
    const usernameInput = wrapper.find('input[placeholder="请输入用户名"]')
    await usernameInput.setValue('testuser')
    await usernameInput.trigger('input')

    // Should clear error
    expect(mockStore.clearError).toHaveBeenCalled()
  })

  it('toggles password visibility', async () => {
    const passwordInput = wrapper.find('input[type="password"]')
    const toggleButton = wrapper.find('.password-toggle')

    // Initially password should be hidden
    expect(passwordInput.attributes('type')).toBe('password')

    // Click toggle button
    await toggleButton.trigger('click')

    // Password should be visible
    expect(passwordInput.attributes('type')).toBe('text')
  })

  it('handles remember me functionality', async () => {
    const rememberCheckbox = wrapper.find('input[type="checkbox"]')

    // Initially unchecked
    expect(wrapper.vm.form.remember).toBe(false)

    // Check the checkbox
    await rememberCheckbox.setChecked(true)
    expect(wrapper.vm.form.remember).toBe(true)
  })

  it('redirects to dashboard on successful login', async () => {
    // Mock successful login
    mockStore.login.mockResolvedValue({ success: true })

    // Fill and submit form
    await wrapper.setData({
      form: {
        username: 'testuser',
        password: 'password123',
        remember: false
      }
    })

    const form = wrapper.find('form')
    await form.trigger('submit')

    // Wait for login to complete
    await wrapper.vm.$nextTick()

    // Should redirect to dashboard
    expect(wrapper.vm.$router.currentRoute.value.path).toBe('/dashboard')
  })

  it('handles keyboard shortcuts', async () => {
    // Test Enter key in password field
    const passwordInput = wrapper.find('input[type="password"]')
    await passwordInput.trigger('keydown.enter')

    // Should trigger form submission
    expect(mockStore.login).toHaveBeenCalled()
  })

  it('validates email format when email login is enabled', async () => {
    // Enable email login
    await wrapper.setData({ isEmailLogin: true })

    // Enter invalid email
    const emailInput = wrapper.find('input[placeholder="请输入邮箱"]')
    await emailInput.setValue('invalid-email')
    await emailInput.trigger('blur')

    // Should show email validation error
    expect(wrapper.vm.form.errors.username).toContain('请输入有效的邮箱地址')
  })

  it('switches between username and email login', async () => {
    // Initially username login
    expect(wrapper.find('input[placeholder="请输入用户名"]').exists()).toBe(true)

    // Switch to email login
    await wrapper.setData({ isEmailLogin: true })
    await wrapper.vm.$nextTick()

    // Should show email input
    expect(wrapper.find('input[placeholder="请输入邮箱"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="请输入用户名"]').exists()).toBe(false)
  })

  it('handles forgot password link', async () => {
    const forgotLink = wrapper.find('a[href="/forgot-password"]')
    expect(forgotLink.exists()).toBe(true)

    await forgotLink.trigger('click')
    // In a real implementation, this would navigate to forgot password page
  })

  it('handles registration link', async () => {
    const registerLink = wrapper.find('a[href="/register"]')
    expect(registerLink.exists()).toBe(true)

    await registerLink.trigger('click')
    // In a real implementation, this would navigate to registration page
  })

  it('shows proper accessibility attributes', () => {
    const form = wrapper.find('form')
    expect(form.attributes('aria-label')).toBe('登录表单')

    const usernameInput = wrapper.find('input[placeholder="请输入用户名"]')
    expect(usernameInput.attributes('aria-required')).toBe('true')
    expect(usernameInput.attributes('aria-describedby')).toBeDefined()
  })

  it('handles form reset', async () => {
    // Fill form with data
    await wrapper.setData({
      form: {
        username: 'testuser',
        password: 'password123',
        remember: true,
        errors: { username: 'Error' }
      }
    })

    // Reset form
    wrapper.vm.resetForm()

    // Should clear all form data and errors
    expect(wrapper.vm.form.username).toBe('')
    expect(wrapper.vm.form.password).toBe('')
    expect(wrapper.vm.form.remember).toBe(false)
    expect(wrapper.vm.form.errors).toEqual({})
  })

  it('displays loading spinner correctly', async () => {
    mockStore.loading = true
    await wrapper.vm.$nextTick()

    const loadingSpinner = wrapper.find('.loading-spinner')
    expect(loadingSpinner.exists()).toBe(true)
  })

  it('prevents multiple submissions during loading', async () => {
    mockStore.loading = true
    await wrapper.vm.$nextTick()

    const form = wrapper.find('form')
    await form.trigger('submit')

    // Should not call login when already loading
    expect(mockStore.login).not.toHaveBeenCalled()
  })
})