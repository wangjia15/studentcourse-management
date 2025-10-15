import { test, expect } from '@playwright/test'

test.describe('Course Management', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[placeholder="请输入用户名"]', 'teacher')
    await page.fill('input[type="password"]', 'Teacher123!')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL('/dashboard')
  })

  test('should display course list', async ({ page }) => {
    await page.click('text=课程管理')
    await expect(page.locator('h1')).toContainText('课程管理')
    await expect(page.locator('.course-list')).toBeVisible()
  })

  test('should create new course', async ({ page }) => {
    await page.click('text=课程管理')
    await page.click('button:has-text("创建课程")')

    await expect(page.locator('text=创建新课程')).toBeVisible()

    // Fill course form
    await page.fill('input[placeholder="请输入课程代码"]', 'CS101')
    await page.fill('input[placeholder="请输入课程名称"]', '计算机科学导论')
    await page.fill('textarea[placeholder="请输入课程描述"]', '这是一门计算机科学基础课程')
    await page.fill('input[placeholder="请输入学分"]', '3')
    await page.fill('input[placeholder="请输入容量"]', '50')
    await page.selectOption('select[name="department"]', '计算机科学与技术')
    await page.fill('input[placeholder="请输入学期"]', '2023-2024-1')

    await page.click('button:has-text("创建课程")')

    await expect(page.locator('.el-message--success')).toBeVisible()
    await expect(page.locator('text=课程创建成功')).toBeVisible()

    // Should redirect to course detail page
    await expect(page.locator('h1')).toContainText('CS101 - 计算机科学导论')
  })

  test('should edit existing course', async ({ page }) => {
    await page.click('text=课程管理')

    // Click on first course edit button
    await page.click('.course-list .el-button:has-text("编辑")')

    await expect(page.locator('text=编辑课程')).toBeVisible()

    // Update course information
    await page.fill('input[placeholder="请输入课程名称"]', '更新后的课程名称')
    await page.fill('textarea[placeholder="请输入课程描述"]', '更新后的课程描述')

    await page.click('button:has-text("保存修改")')

    await expect(page.locator('.el-message--success')).toBeVisible()
    await expect(page.locator('text=课程更新成功')).toBeVisible()
  })

  test('should delete course with confirmation', async ({ page }) => {
    await page.click('text=课程管理')

    // Get initial course count
    const initialCount = await page.locator('.course-list .course-item').count()

    // Click delete button on first course
    await page.click('.course-list .el-button:has-text("删除")')

    // Should show confirmation dialog
    await expect(page.locator('.el-message-box')).toBeVisible()
    await expect(page.locator('text=确认删除此课程？')).toBeVisible()

    await page.click('.el-message-box__btns .el-button--primary')

    await expect(page.locator('.el-message--success')).toBeVisible()
    await expect(page.locator('text=课程删除成功')).toBeVisible()

    // Verify course count decreased
    const finalCount = await page.locator('.course-list .course-item').count()
    expect(finalCount).toBe(initialCount - 1)
  })

  test('should search courses', async ({ page }) => {
    await page.click('text=课程管理')

    // Use search functionality
    await page.fill('input[placeholder="搜索课程"]', '计算机')
    await page.keyboard.press('Enter')

    // Should show filtered results
    await expect(page.locator('.course-list')).toBeVisible()
    const courseItems = await page.locator('.course-list .course-item').allTextContents()
    courseItems.forEach(item => {
      expect(item.toLowerCase()).toContain('计算机'.toLowerCase())
    })
  })

  test('should filter courses by department', async ({ page }) => {
    await page.click('text=课程管理')

    // Select department filter
    await page.selectOption('select[name="department"]', '计算机科学与技术')

    // Should show filtered courses
    await expect(page.locator('.course-list')).toBeVisible()
  })

  test('should filter courses by semester', async ({ page }) => {
    await page.click('text=课程管理')

    // Select semester filter
    await page.selectOption('select[name="semester"]', '2023-2024-1')

    // Should show filtered courses
    await expect(page.locator('.course-list')).toBeVisible()
  })

  test('should display course details', async ({ page }) => {
    await page.click('text=课程管理')

    // Click on first course
    await page.click('.course-list .course-item')

    // Should show course detail page
    await expect(page.locator('.course-detail')).toBeVisible()
    await expect(page.locator('.course-info')).toBeVisible()
    await expect(page.locator('.course-stats')).toBeVisible()
  })

  test('should manage course enrollment', async ({ page }) => {
    await page.click('text=课程管理')

    // Go to course detail
    await page.click('.course-list .course-item')

    // Click on enrollment tab
    await page.click('text=学生管理')

    await expect(page.locator('.student-list')).toBeVisible()
    await expect(page.locator('button:has-text("添加学生")')).toBeVisible()

    // Add student to course
    await page.click('button:has-text("添加学生")')

    // Select student from list
    await page.click('.student-selector .el-checkbox:first-child')
    await page.click('button:has-text("确认添加")')

    await expect(page.locator('.el-message--success')).toBeVisible()
    await expect(page.locator('text=学生添加成功')).toBeVisible()
  })

  test('should manage course materials', async ({ page }) => {
    await page.click('text=课程管理')

    // Go to course detail
    await page.click('.course-list .course-item')

    // Click on materials tab
    await page.click('text=课程资料')

    await expect(page.locator('.material-list')).toBeVisible()
    await expect(page.locator('button:has-text("上传资料")')).toBeVisible()

    // Upload course material
    await page.click('button:has-text("上传资料")')

    // Fill material form
    await page.fill('input[placeholder="请输入资料标题"]', '课程大纲')
    await page.fill('textarea[placeholder="请输入资料描述"]', '本课程的教学大纲')
    await page.selectOption('select[name="type"]', '文档')

    // Mock file upload
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'syllabus.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('mock pdf content')
    })

    await page.click('button:has-text("上传")')

    await expect(page.locator('.el-message--success')).toBeVisible()
    await expect(page.locator('text=资料上传成功')).toBeVisible()
  })

  test('should export course data', async ({ page }) => {
    await page.click('text=课程管理')

    // Go to course detail
    await page.click('.course-list .course-item')

    // Export course data
    await page.click('button:has-text("导出数据")')

    // Should start download
    const downloadPromise = page.waitForEvent('download')
    await page.click('text=导出Excel')
    const download = await downloadPromise

    expect(download.suggestedFilename()).toContain('.xlsx')
  })

  test('should view course analytics', async ({ page }) => {
    await page.click('text=课程管理')

    // Go to course detail
    await page.click('.course-list .course-item')

    // Click analytics tab
    await page.click('text=数据分析')

    await expect(page.locator('.analytics-dashboard')).toBeVisible()
    await expect(page.locator('.grade-distribution')).toBeVisible()
    await expect(page.locator('.performance-trends')).toBeVisible()
    await expect(page.locator('.student-progress')).toBeVisible()
  })

  test('should handle course pagination', async ({ page }) => {
    await page.click('text=课程管理')

    // If there are many courses, test pagination
    const pagination = page.locator('.el-pagination')
    if (await pagination.isVisible()) {
      await page.click('.el-pagination .btn-next')
      await expect(page.locator('.course-list')).toBeVisible()

      await page.click('.el-pagination .btn-prev')
      await expect(page.locator('.course-list')).toBeVisible()
    }
  })

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await page.click('text=课程管理')

    // Mobile-specific elements should be visible
    await expect(page.locator('.course-list')).toBeVisible()
    await expect(page.locator('.mobile-menu')).toBeVisible()

    // Test mobile course card layout
    const courseCards = page.locator('.course-card')
    if (await courseCards.count() > 0) {
      await expect(courseCards.first()).toBeVisible()
    }
  })
})

test.describe('Student Course View', () => {
  test.beforeEach(async ({ page }) => {
    // Login as student
    await page.goto('/login')
    await page.fill('input[placeholder="请输入用户名"]', 'student')
    await page.fill('input[type="password"]', 'Student123!')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL('/dashboard')
  })

  test('should display enrolled courses', async ({ page }) => {
    await page.click('text=我的课程')

    await expect(page.locator('h1')).toContainText('我的课程')
    await expect(page.locator('.enrolled-courses')).toBeVisible()
  })

  test('should enroll in new course', async ({ page }) => {
    await page.click('text=课程目录')

    await expect(page.locator('h1')).toContainText('课程目录')
    await expect(page.locator('.available-courses')).toBeVisible()

    // Click on enroll button for first available course
    const enrollButton = page.locator('.course-card .el-button:has-text("选课")')
    if (await enrollButton.count() > 0) {
      await enrollButton.first().click()

      await expect(page.locator('.el-message--success')).toBeVisible()
      await expect(page.locator('text=选课成功')).toBeVisible()
    }
  })

  test('should view course details as student', async ({ page }) => {
    await page.click('text=我的课程')

    // Click on first enrolled course
    const courseCard = page.locator('.enrolled-courses .course-card')
    if (await courseCard.count() > 0) {
      await courseCard.first().click()

      await expect(page.locator('.course-detail')).toBeVisible()
      await expect(page.locator('.course-materials')).toBeVisible()
      await expect(page.locator('.course-grades')).toBeVisible()
    }
  })

  test('should drop course with confirmation', async ({ page }) => {
    await page.click('text=我的课程')

    // Find drop button
    const dropButton = page.locator('.enrolled-courses .el-button:has-text("退课")')
    if (await dropButton.count() > 0) {
      await dropButton.first().click()

      // Should show confirmation dialog
      await expect(page.locator('.el-message-box')).toBeVisible()
      await expect(page.locator('text=确认退选此课程？')).toBeVisible()

      await page.click('.el-message-box__btns .el-button--primary')

      await expect(page.locator('.el-message--success')).toBeVisible()
      await expect(page.locator('text=退课成功')).toBeVisible()
    }
  })
})