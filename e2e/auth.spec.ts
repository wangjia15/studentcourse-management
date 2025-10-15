import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('should display login form', async ({ page }) => {
    await expect(page.locator('h2')).toContainText('用户登录')
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
    await expect(page.locator('input[type="checkbox"]')).toBeVisible()
  })

  test('should show validation errors for empty form', async ({ page }) => {
    await page.click('button[type="submit"]')

    await expect(page.locator('text=请输入用户名')).toBeVisible()
    await expect(page.locator('text=请输入密码')).toBeVisible()
  })

  test('should toggle password visibility', async ({ page }) => {
    const passwordInput = page.locator('input[type="password"]')
    const toggleButton = page.locator('.password-toggle')

    await expect(passwordInput).toHaveAttribute('type', 'password')
    await toggleButton.click()
    await expect(passwordInput).toHaveAttribute('type', 'text')
    await toggleButton.click()
    await expect(passwordInput).toHaveAttribute('type', 'password')
  })

  test('should show error for invalid credentials', async ({ page }) => {
    await page.fill('input[placeholder="请输入用户名"]', 'invaliduser')
    await page.fill('input[type="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')

    await expect(page.locator('.el-alert--error')).toBeVisible()
    await expect(page.locator('text=用户名或密码错误')).toBeVisible()
  })

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.fill('input[placeholder="请输入用户名"]', 'admin')
    await page.fill('input[type="password"]', 'Admin123!')
    await page.check('input[type="checkbox"]') // Remember me
    await page.click('button[type="submit"]')

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard')
    await expect(page.locator('h1')).toContainText('仪表板')
  })

  test('should handle remember me functionality', async ({ page }) => {
    await page.fill('input[placeholder="请输入用户名"]', 'admin')
    await page.fill('input[type="password"]', 'Admin123!')
    await page.check('input[type="checkbox"]')
    await page.click('button[type="submit"]')

    // Check if remember me token is set (simplified test)
    const cookies = await page.context().cookies()
    const rememberCookie = cookies.find(cookie => cookie.name === 'remember_token')
    expect(rememberCookie).toBeTruthy()
  })

  test('should navigate to registration page', async ({ page }) => {
    await page.click('a[href="/register"]')
    await expect(page).toHaveURL('/register')
    await expect(page.locator('h2')).toContainText('用户注册')
  })

  test('should navigate to forgot password page', async ({ page }) => {
    await page.click('a[href="/forgot-password"]')
    await expect(page).toHaveURL('/forgot-password')
  })

  test('should clear error when user starts typing', async ({ page }) => {
    // First trigger an error
    await page.click('button[type="submit"]')
    await expect(page.locator('.el-alert--error')).toBeVisible()

    // Start typing in username field
    await page.fill('input[placeholder="请输入用户名"]', 'testuser')
    await expect(page.locator('.el-alert--error')).not.toBeVisible()
  })

  test('should handle keyboard navigation', async ({ page }) => {
    await page.fill('input[placeholder="请输入用户名"]', 'admin')
    await page.fill('input[type="password"]', 'Admin123!')

    // Press Enter in password field
    await page.press('input[type="password"]', 'Enter')

    // Should submit form
    await expect(page).toHaveURL('/dashboard')
  })

  test('should support email login', async ({ page }) => {
    // Switch to email login
    await page.click('text=使用邮箱登录')

    await expect(page.locator('input[placeholder="请输入用户名"]')).not.toBeVisible()
    await expect(page.locator('input[placeholder="请输入邮箱"]')).toBeVisible()

    // Test email validation
    await page.fill('input[placeholder="请输入邮箱"]', 'invalid-email')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')

    await expect(page.locator('text=请输入有效的邮箱地址')).toBeVisible()
  })

  test('should handle loading state', async ({ page }) => {
    await page.fill('input[placeholder="请输入用户名"]', 'admin')
    await page.fill('input[type="password"]', 'Admin123!')

    // Mock slow response
    await page.route('**/api/v1/auth/login', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access_token: 'mock-token' })
      })
    })

    await page.click('button[type="submit"]')

    // Should show loading state
    await expect(page.locator('button[type="submit"]')).toContainText('登录中')
    await expect(page.locator('.loading-spinner')).toBeVisible()
  })

  test('should be responsive on mobile', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page.locator('.login-container')).toBeVisible()
    await expect(page.locator('.login-form')).toBeVisible()

    // Form should still be functional on mobile
    await page.fill('input[placeholder="请输入用户名"]', 'admin')
    await page.fill('input[type="password"]', 'Admin123!')
    await page.click('button[type="submit"]')

    await expect(page).toHaveURL('/dashboard')
  })

  test('should handle network errors gracefully', async ({ page }) => {
    // Mock network error
    await page.route('**/api/v1/auth/login', route => route.abort())

    await page.fill('input[placeholder="请输入用户名"]', 'admin')
    await page.fill('input[type="password"]', 'Admin123!')
    await page.click('button[type="submit"]')

    await expect(page.locator('.el-alert--error')).toBeVisible()
    await expect(page.locator('text=网络错误')).toBeVisible()
  })
})

test.describe('Registration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register')
  })

  test('should display registration form', async ({ page }) => {
    await expect(page.locator('h2')).toContainText('用户注册')
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入邮箱"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入密码"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请确认密码"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入真实姓名"]')).toBeVisible()
  })

  test('should validate password strength', async ({ page }) => {
    await page.fill('input[placeholder="请输入密码"]', '123')
    await page.blur('input[placeholder="请输入密码"]')

    await expect(page.locator('text=密码强度不足')).toBeVisible()
  })

  test('should validate password confirmation', async ({ page }) => {
    await page.fill('input[placeholder="请输入密码"]', 'Password123!')
    await page.fill('input[placeholder="请确认密码"]', 'DifferentPassword!')
    await page.blur('input[placeholder="请确认密码"]')

    await expect(page.locator('text=两次输入的密码不一致')).toBeVisible()
  })

  test('should register successfully with valid data', async ({ page }) => {
    await page.fill('input[placeholder="请输入用户名"]', 'newuser')
    await page.fill('input[placeholder="请输入邮箱"]', 'newuser@example.com')
    await page.fill('input[placeholder="请输入密码"]', 'Password123!')
    await page.fill('input[placeholder="请确认密码"]', 'Password123!')
    await page.fill('input[placeholder="请输入真实姓名"]', '新用户')

    // Select user role
    await page.selectOption('select[name="role"]', 'student')

    // Fill student-specific fields
    await page.fill('input[placeholder="请输入学号"]', '2023001')
    await page.fill('input[placeholder="请选择专业"]', '计算机科学与技术')

    await page.click('button[type="submit"]')

    await expect(page.locator('.el-message--success')).toBeVisible()
    await expect(page.locator('text=注册成功')).toBeVisible()

    // Should redirect to login
    await expect(page).toHaveURL('/login')
  })

  test('should check username availability', async ({ page }) => {
    // First, create a user through the API
    await page.evaluate(() => {
      fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'existinguser',
          email: 'existing@example.com',
          password: 'Password123!',
          full_name: 'Existing User',
          role: 'student'
        })
      })
    })

    // Try to register with same username
    await page.fill('input[placeholder="请输入用户名"]', 'existinguser')
    await page.blur('input[placeholder="请输入用户名"]')

    await expect(page.locator('text=用户名已存在')).toBeVisible()
  })
})

test.describe('Logout', () => {
  test('should logout successfully', async ({ page }) => {
    // First login
    await page.goto('/login')
    await page.fill('input[placeholder="请输入用户名"]', 'admin')
    await page.fill('input[type="password"]', 'Admin123!')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL('/dashboard')

    // Then logout
    await page.click('button[aria-label="用户菜单"]')
    await page.click('text=退出登录')

    // Should confirm logout
    await page.click('text=确认')

    await expect(page).toHaveURL('/login')

    // Should clear authentication
    const cookies = await page.context().cookies()
    const authCookie = cookies.find(cookie => cookie.name === 'access_token')
    expect(authCookie).toBeFalsy()
  })
})