<template>
  <div class="grade-management">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">成绩管理</h1>
          <div class="breadcrumb">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item>首页</el-breadcrumb-item>
              <el-breadcrumb-item>课程管理</el-breadcrumb-item>
              <el-breadcrumb-item>成绩管理</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
        </div>
        <div class="header-right">
          <el-select
            v-model="selectedCourseId"
            placeholder="选择课程"
            size="large"
            style="width: 300px"
            @change="handleCourseChange"
          >
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="`${course.name} (${course.code})`"
              :value="course.id"
            />
          </el-select>
        </div>
      </div>
    </div>

    <!-- Course Info Card -->
    <div v-if="selectedCourse" class="course-info-card">
      <el-card>
        <div class="course-info">
          <div class="course-basic">
            <h2>{{ selectedCourse.name }}</h2>
            <p class="course-code">课程代码: {{ selectedCourse.code }}</p>
            <p class="course-details">
              学分: {{ selectedCourse.credit }} |
              学期: {{ selectedCourse.semester }} |
              教师: {{ selectedCourse.teacherName }}
            </p>
          </div>
          <div class="course-stats">
            <div class="stat-item">
              <div class="stat-value">{{ gradeStore.getters.totalRows }}</div>
              <div class="stat-label">学生总数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ gradeStore.getters.totalColumns }}</div>
              <div class="stat-label">成绩项目</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ gradeStore.getters.modifiedRows.length }}</div>
              <div class="stat-label">已修改</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ gradeStore.getters.errorCount }}</div>
              <div class="stat-label">验证错误</div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Grade Spreadsheet -->
    <div v-if="selectedCourseId" class="spreadsheet-container">
      <GradeSpreadsheet
        :course-id="selectedCourseId"
        :height="spreadsheetHeight"
      />
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <el-empty description="请选择一个课程开始管理成绩">
        <el-button type="primary" @click="showCourseSelector = true">
          选择课程
        </el-button>
      </el-empty>
    </div>

    <!-- Course Selector Dialog -->
    <el-dialog
      v-model="showCourseSelector"
      title="选择课程"
      width="600px"
    >
      <div class="course-selector">
        <el-input
          v-model="courseSearchKeyword"
          placeholder="搜索课程..."
          prefix-icon="Search"
          clearable
          class="search-input"
        />
        <div class="course-list">
          <div
            v-for="course in filteredCourses"
            :key="course.id"
            class="course-item"
            @click="selectCourse(course.id)"
          >
            <div class="course-item-info">
              <h3>{{ course.name }}</h3>
              <p>{{ course.code }} | {{ selectedCourse?.semester }}</p>
            </div>
            <div class="course-item-meta">
              <el-tag>{{ course.credit }}学分</el-tag>
              <el-tag type="info">{{ course.studentCount || 0 }}学生</el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- Statistics Dialog -->
    <el-dialog
      v-model="showStatistics"
      title="成绩统计"
      width="800px"
      top="5vh"
    >
      <GradeStatistics
        v-if="selectedCourseId"
        :course-id="selectedCourseId"
      />
    </el-dialog>

    <!-- Settings Dialog -->
    <el-dialog
      v-model="showSettings"
      title="表格设置"
      width="500px"
    >
      <SpreadsheetSettings
        v-model="gradeStore.state.config"
        @update="updateSettings"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGradeStore } from '@/stores/grade'
import { courseApi } from '@/lib/api'
import GradeSpreadsheet from '@/components/GradeSpreadsheet.vue'
import GradeStatistics from '@/components/GradeStatistics.vue'
import SpreadsheetSettings from '@/components/SpreadsheetSettings.vue'
import type { CourseInfo } from '@/types/grade'

// Router
const route = useRoute()
const router = useRouter()

// Store
const gradeStore = useGradeStore()

// State
const selectedCourseId = ref<number | null>(null)
const courses = ref<CourseInfo[]>([])
const showCourseSelector = ref(false)
const showStatistics = ref(false)
const showSettings = ref(false)
const courseSearchKeyword = ref('')

// Computed
const selectedCourse = computed(() => {
  return courses.value.find(course => course.id === selectedCourseId.value)
})

const filteredCourses = computed(() => {
  if (!courseSearchKeyword.value) return courses.value

  const keyword = courseSearchKeyword.value.toLowerCase()
  return courses.value.filter(course =>
    course.name.toLowerCase().includes(keyword) ||
    course.code.toLowerCase().includes(keyword) ||
    course.teacherName?.toLowerCase().includes(keyword)
  )
})

const spreadsheetHeight = computed(() => {
  return window.innerHeight - 320 // Account for headers and margins
})

// Methods
const loadCourses = async () => {
  try {
    const response = await courseApi.getCourses()
    courses.value = response.data
  } catch (error) {
    console.error('Error loading courses:', error)
  }
}

const handleCourseChange = (courseId: number) => {
  selectedCourseId.value = courseId
  // Update URL
  router.push({ query: { courseId } })
}

const selectCourse = (courseId: number) => {
  selectedCourseId.value = courseId
  showCourseSelector.value = false
  router.push({ query: { courseId } })
}

const updateSettings = (config: any) => {
  gradeStore.actions.updateConfig(config)
}

// Keyboard shortcuts
const setupKeyboardShortcuts = () => {
  document.addEventListener('keydown', handleGlobalKeydown)
}

const removeKeyboardShortcuts = () => {
  document.removeEventListener('keydown', handleGlobalKeydown)
}

const handleGlobalKeydown = (event: KeyboardEvent) => {
  // Only handle shortcuts when not in input fields
  const target = event.target as HTMLElement
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return

  if (event.ctrlKey || event.metaKey) {
    switch (event.key) {
      case 'o':
        event.preventDefault()
        showCourseSelector.value = true
        break
      case 's':
        event.preventDefault()
        if (gradeStore.getters.canSave) {
          gradeStore.actions.saveGrades({})
        }
        break
      case 'z':
        if (event.shiftKey) {
          event.preventDefault()
          if (gradeStore.getters.canRedo) {
            gradeStore.actions.redo()
          }
        } else {
          event.preventDefault()
          if (gradeStore.getters.canUndo) {
            gradeStore.actions.undo()
          }
        }
        break
      case ',':
        event.preventDefault()
        showSettings.value = true
        break
    }
  }

  // F1 for help
  if (event.key === 'F1') {
    event.preventDefault()
    // Show help dialog
  }
}

// Lifecycle
onMounted(() => {
  loadCourses()
  setupKeyboardShortcuts()

  // Load course from URL if present
  const courseIdFromUrl = route.query.courseId
  if (courseIdFromUrl) {
    selectedCourseId.value = parseInt(courseIdFromUrl as string)
  }
})

// Auto-save before page unload
window.addEventListener('beforeunload', (event) => {
  if (gradeStore.getters.hasUnsavedChanges) {
    event.preventDefault()
    event.returnValue = '您有未保存的更改，确定要离开吗？'
  }
})

// Cleanup
onUnmounted(() => {
  removeKeyboardShortcuts()
})
</script>

<style scoped lang="scss">
.grade-management {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 24px;
  }

  .header-left {
    flex: 1;

    .page-title {
      margin: 0 0 8px 0;
      font-size: 28px;
      font-weight: 600;
      color: #303133;
    }

    .breadcrumb {
      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: #909399;
          font-weight: normal;
        }

        &:last-child .el-breadcrumb__inner {
          color: #606266;
          font-weight: 500;
        }
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.course-info-card {
  margin-bottom: 24px;

  .course-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 32px;

    .course-basic {
      h2 {
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 600;
        color: #303133;
      }

      .course-code {
        margin: 0 0 4px 0;
        font-size: 14px;
        color: #606266;
      }

      .course-details {
        margin: 0;
        font-size: 13px;
        color: #909399;
      }
    }

    .course-stats {
      display: flex;
      gap: 32px;

      .stat-item {
        text-align: center;

        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: #409eff;
          line-height: 1;
        }

        .stat-label {
          margin-top: 4px;
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }
}

.spreadsheet-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.course-selector {
  .search-input {
    margin-bottom: 16px;
  }

  .course-list {
    max-height: 400px;
    overflow-y: auto;

    .course-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.2s;

      &:hover {
        background: #f5f7fa;
        border-color: #409eff;
      }

      .course-item-info {
        h3 {
          margin: 0 0 4px 0;
          font-size: 16px;
          font-weight: 500;
          color: #303133;
        }

        p {
          margin: 0;
          font-size: 13px;
          color: #909399;
        }
      }

      .course-item-meta {
        display: flex;
        gap: 8px;
      }
    }
  }
}

// Mobile responsive
@media (max-width: 768px) {
  .grade-management {
    padding: 16px;
  }

  .page-header {
    .header-content {
      flex-direction: column;
      gap: 16px;
    }

    .header-right {
      width: 100%;
      justify-content: stretch;

      :deep(.el-select) {
        width: 100% !important;
      }
    }
  }

  .course-info-card {
    .course-info {
      flex-direction: column;
      gap: 20px;

      .course-stats {
        justify-content: space-around;
        gap: 16px;

        .stat-item {
          .stat-value {
            font-size: 20px;
          }
        }
      }
    }
  }
}

// High contrast mode support
@media (prefers-contrast: high) {
  .grade-management {
    background: #fff;
  }

  .course-info-card,
  .spreadsheet-container,
  .empty-state {
    border: 2px solid #303133;
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .course-item {
    transition: none;
  }
}
</style>