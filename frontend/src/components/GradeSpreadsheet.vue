<template>
  <div class="grade-spreadsheet" v-loading="gradeStore.state.loading">
    <!-- Toolbar -->
    <div class="spreadsheet-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button
            size="small"
            :disabled="!gradeStore.getters.canUndo"
            @click="gradeStore.actions.undo()"
          >
            <el-icon><ArrowLeft /></el-icon>
            撤销
          </el-button>
          <el-button
            size="small"
            :disabled="!gradeStore.getters.canRedo"
            @click="gradeStore.actions.redo()"
          >
            <el-icon><ArrowRight /></el-icon>
            重做
          </el-button>
        </el-button-group>

        <el-divider direction="vertical" />

        <el-button-group>
          <el-button
            size="small"
            :disabled="gradeStore.state.selectedCells.length === 0"
            @click="gradeStore.actions.copy()"
          >
            <el-icon><CopyDocument /></el-icon>
            复制
          </el-button>
          <el-button
            size="small"
            :disabled="gradeStore.state.selectedCells.length === 0 || !hasClipboardData"
            @click="gradeStore.actions.paste()"
          >
            <el-icon><Paste /></el-icon>
            粘贴
          </el-button>
          <el-button
            size="small"
            :disabled="gradeStore.state.selectedCells.length === 0"
            @click="gradeStore.actions.clear()"
          >
            <el-icon><Delete /></el-icon>
            清空
          </el-button>
        </el-button-group>

        <el-divider direction="vertical" />

        <el-dropdown @command="handleBulkOperation">
          <el-button size="small">
            批量操作
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="add-points">加分</el-dropdown-item>
              <el-dropdown-item command="multiply">乘以系数</el-dropdown-item>
              <el-dropdown-item command="percentage">设置百分比</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="toolbar-right">
        <el-button
          type="primary"
          size="small"
          :loading="gradeStore.state.saving"
          :disabled="!gradeStore.getters.canSave"
          @click="saveGrades"
        >
          <el-icon><Check /></el-icon>
          保存
        </el-button>

        <el-button
          size="small"
          @click="validateAll"
        >
          <el-icon><Warning /></el-icon>
          验证
        </el-button>

        <el-button
          size="small"
          @click="exportGrades"
        >
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </div>

    <!-- Error Display -->
    <el-alert
      v-if="gradeStore.state.error"
      :title="gradeStore.state.error"
      type="error"
      show-icon
      closable
      @close="gradeStore.state.error = null"
      class="error-alert"
    />

    <!-- Validation Errors -->
    <div v-if="gradeStore.getters.hasErrors" class="validation-errors">
      <el-alert
        :title="`发现 ${gradeStore.getters.errorCount} 个验证错误`"
        type="warning"
        show-icon
        :closable="false"
      >
        <template #default>
          <ul class="error-list">
            <li v-for="error in gradeStore.state.validationErrors.slice(0, 3)" :key="`${error.rowId}-${error.columnId}`">
              {{ getErrorDescription(error) }}
            </li>
            <li v-if="gradeStore.getters.errorCount > 3">
              还有 {{ gradeStore.getters.errorCount - 3 }} 个错误...
            </li>
          </ul>
        </template>
      </el-alert>
    </div>

    <!-- Spreadsheet Table -->
    <div class="spreadsheet-container" ref="spreadsheetContainer" @keydown="handleKeyDown">
      <el-table
        ref="tableRef"
        :data="visibleData"
        :height="tableHeight"
        :row-height="gradeStore.state.config.virtualScrolling.itemHeight"
        :border="true"
        :stripe="gradeStore.state.config.ui.alternatingRowColors"
        :highlight-current-row="gradeStore.state.config.ui.enableSelection"
        :row-class-name="getRowClassName"
        :cell-class-name="getCellClassName"
        @cell-click="handleCellClick"
        @cell-dblclick="handleCellDoubleClick"
        @selection-change="handleSelectionChange"
        @contextmenu="handleContextMenu"
        class="grade-table"
      >
        <!-- Row Numbers -->
        <el-table-column
          v-if="gradeStore.state.config.ui.showRowNumbers"
          type="index"
          :index="getRowNumber"
          label="#"
          width="60"
          fixed="left"
          align="center"
        />

        <!-- Student Info Columns -->
        <el-table-column
          prop="studentId"
          label="学号"
          width="120"
          fixed="left"
          sortable
        />
        <el-table-column
          prop="studentName"
          label="姓名"
          width="100"
          fixed="left"
          sortable
        />
        <el-table-column
          prop="gender"
          label="性别"
          width="80"
          fixed="left"
        />
        <el-table-column
          prop="major"
          label="专业"
          width="150"
          fixed="left"
        />
        <el-table-column
          prop="class"
          label="班级"
          width="120"
          fixed="left"
        />

        <!-- Grade Columns -->
        <el-table-column
          v-for="column in gradeStore.state.visibleColumns"
          :key="column.id"
          :prop="`grades.${column.id}`"
          :label="column.title"
          :width="getColumnWidth(column)"
          :min-width="100"
          :sortable="false"
          :resizable="true"
        >
          <template #header="{ column: col }">
            <div class="column-header">
              <span>{{ col.label }}</span>
              <el-tooltip
                :content="`满分: ${getColumnMaxScore(col.property)}, 权重: ${getColumnWeight(col.property)}%`"
                placement="top"
              >
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>

          <template #default="{ row, column: col }">
            <GradeCell
              :row="row"
              :column="getColumnFromProperty(col.property)"
              :value="row.grades[getColumnIdFromProperty(col.property)]"
              :is-editing="isCellEditing(row.id, getColumnIdFromProperty(col.property))"
              :is-selected="isCellSelected(row.id, getColumnIdFromProperty(col.property))"
              :has-error="hasCellError(row.id, getColumnIdFromProperty(col.property))"
              :is-modified="row.isModified"
              @edit="startEdit"
              @save="saveEdit"
              @cancel="cancelEdit"
            />
          </template>
        </el-table-column>

        <!-- Summary Columns -->
        <el-table-column
          prop="totalScore"
          label="总分"
          width="100"
          fixed="right"
          sortable
        >
          <template #default="{ row }">
            <span :class="getScoreClass(row.totalScore)">
              {{ formatScore(row.totalScore) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column
          prop="averageScore"
          label="平均分"
          width="100"
          fixed="right"
          sortable
        >
          <template #default="{ row }">
            <span :class="getScoreClass(row.averageScore)">
              {{ formatScore(row.averageScore) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column
          prop="rank"
          label="排名"
          width="80"
          fixed="right"
          sortable
        >
          <template #default="{ row }">
            <el-tag :type="getRankType(row.rank)">
              {{ row.rank }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Status Bar -->
    <div class="spreadsheet-status">
      <div class="status-left">
        <span>共 {{ gradeStore.getters.totalRows }} 行，{{ gradeStore.getters.totalColumns }} 列</span>
        <span v-if="gradeStore.getters.hasUnsavedChanges" class="unsaved-indicator">
          <el-icon><Warning /></el-icon>
          有未保存的更改
        </span>
      </div>
      <div class="status-right">
        <span v-if="gradeStore.state.selectedCells.length > 0">
          已选择 {{ getSelectedCellCount() }} 个单元格
        </span>
      </div>
    </div>

    <!-- Context Menu -->
    <el-dropdown
      ref="contextMenuRef"
      :virtual-ref="contextMenuTarget"
      virtual-triggering
      @command="handleContextMenuCommand"
    >
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="edit">编辑</el-dropdown-item>
          <el-dropdown-item command="copy">复制</el-dropdown-item>
          <el-dropdown-item command="paste" :disabled="!hasClipboardData">粘贴</el-dropdown-item>
          <el-dropdown-item command="clear">清空</el-dropdown-item>
          <el-dropdown-item divided command="fill-down">向下填充</el-dropdown-item>
          <el-dropdown-item command="fill-right">向右填充</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- Bulk Operation Dialog -->
    <el-dialog
      v-model="bulkOperationDialog.visible"
      :title="getBulkOperationTitle()"
      width="400px"
    >
      <el-form :model="bulkOperationDialog" label-width="80px">
        <el-form-item
          v-if="bulkOperationDialog.type === 'add-points'"
          label="加分"
        >
          <el-input-number
            v-model="bulkOperationDialog.value"
            :min="-100"
            :max="100"
            :step="1"
            :precision="1"
          />
        </el-form-item>
        <el-form-item
          v-if="bulkOperationDialog.type === 'multiply'"
          label="系数"
        >
          <el-input-number
            v-model="bulkOperationDialog.value"
            :min="0"
            :max="10"
            :step="0.1"
            :precision="2"
          />
        </el-form-item>
        <el-form-item
          v-if="bulkOperationDialog.type === 'percentage'"
          label="百分比"
        >
          <el-input-number
            v-model="bulkOperationDialog.value"
            :min="0"
            :max="200"
            :step="1"
            :precision="0"
          />
          <span class="ml-2">%</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bulkOperationDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="executeBulkOperation">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElTable, ElMessage, ElMessageBox } from 'element-plus'
import { useGradeStore } from '@/stores/grade'
import GradeCell from './GradeCell.vue'
import type {
  GradeValidationError,
  GradeColumn,
  StudentGradeRow
} from '@/types/grade'

// Props
interface Props {
  courseId: number
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  height: 600
})

// Store
const gradeStore = useGradeStore()

// Refs
const tableRef = ref<InstanceType<typeof ElTable>>()
const spreadsheetContainer = ref<HTMLElement>()
const contextMenuRef = ref()
const contextMenuTarget = ref()

// State
const tableHeight = ref(props.height)
const hasClipboardData = ref(false)
const bulkOperationDialog = ref({
  visible: false,
  type: 'add-points' as 'add-points' | 'multiply' | 'percentage',
  value: 0
})

// Computed
const visibleData = computed(() => gradeStore.getters.visibleRows)

// Watch for course changes
watch(() => props.courseId, (newCourseId) => {
  if (newCourseId) {
    gradeStore.actions.loadGrades(newCourseId)
  }
}, { immediate: true })

// Methods
const getRowNumber = (index: number) => {
  return index + gradeStore.state.visibleRange.startRow + 1
}

const getRowClassName = ({ row }: { row: StudentGradeRow }) => {
  const classes = []
  if (row.isModified) classes.push('row-modified')
  if (row.hasErrors) classes.push('row-has-errors')
  return classes.join(' ')
}

const getCellClassName = ({ row, column }: { row: StudentGradeRow, column: any }) => {
  const columnId = getColumnIdFromProperty(column.property)
  if (!columnId) return ''

  const classes = []
  if (isCellSelected(row.id, columnId)) classes.push('cell-selected')
  if (hasCellError(row.id, columnId)) classes.push('cell-error')
  if (isCellEditing(row.id, columnId)) classes.push('cell-editing')
  return classes.join(' ')
}

const getColumnFromProperty = (property: string): GradeColumn | undefined => {
  const columnId = getColumnIdFromProperty(property)
  return gradeStore.state.columns.find(col => col.id === columnId)
}

const getColumnIdFromProperty = (property: string): string | null => {
  if (property?.startsWith('grades.')) {
    return property.replace('grades.', '')
  }
  return null
}

const getColumnWidth = (column: GradeColumn): number => {
  // Dynamic width based on content
  const baseWidth = 100
  const padding = 20
  const titleWidth = column.title.length * 8
  return Math.max(baseWidth, titleWidth + padding)
}

const getColumnMaxScore = (property: string): number => {
  const column = getColumnFromProperty(property)
  return column?.maxScore || 100
}

const getColumnWeight = (property: string): number => {
  const column = getColumnFromProperty(property)
  return column?.weight || 1
}

const isCellEditing = (rowId: number, columnId: string): boolean => {
  return gradeStore.state.editingCell?.rowId === rowId &&
         gradeStore.state.editingCell?.columnId === columnId
}

const isCellSelected = (rowId: number, columnId: string): boolean => {
  const rowIndex = gradeStore.state.rows.findIndex(r => r.id === rowId)
  return gradeStore.state.selectedCells.some(selection => {
    const colIndex = gradeStore.state.columns.findIndex(c => c.id === columnId)
    return rowIndex >= selection.startRow &&
           rowIndex <= selection.endRow &&
           colIndex >= gradeStore.state.columns.findIndex(c => c.id === selection.startColumn) &&
           colIndex <= gradeStore.state.columns.findIndex(c => c.id === selection.endColumn)
  })
}

const hasCellError = (rowId: number, columnId: string): boolean => {
  return gradeStore.state.validationErrors.some(
    error => error.rowId === rowId && error.columnId === columnId
  )
}

const getScoreClass = (score: number): string => {
  if (score >= 90) return 'score-excellent'
  if (score >= 80) return 'score-good'
  if (score >= 70) return 'score-average'
  if (score >= 60) return 'score-pass'
  return 'score-fail'
}

const getRankType = (rank: number): string => {
  if (rank <= 5) return 'success'
  if (rank <= 10) return 'warning'
  if (rank <= 20) return 'info'
  return ''
}

const formatScore = (score: number): string => {
  return score ? score.toFixed(1) : '-'
}

const getSelectedCellCount = (): number => {
  let count = 0
  gradeStore.state.selectedCells.forEach(selection => {
    const rows = selection.endRow - selection.startRow + 1
    const startColIndex = gradeStore.state.columns.findIndex(c => c.id === selection.startColumn)
    const endColIndex = gradeStore.state.columns.findIndex(c => c.id === selection.endColumn)
    const cols = endColIndex - startColIndex + 1
    count += rows * cols
  })
  return count
}

const getErrorDescription = (error: GradeValidationError): string => {
  const row = gradeStore.state.rows.find(r => r.id === error.rowId)
  const column = gradeStore.state.columns.find(c => c.id === error.columnId)
  return `第${row?.studentName || error.rowId}行${column?.title || ''}列: ${error.message}`
}

// Event handlers
const handleCellClick = (row: StudentGradeRow, column: any) => {
  const columnId = getColumnIdFromProperty(column.property)
  if (columnId) {
    gradeStore.actions.selectCell(row.id, columnId)
  }
}

const handleCellDoubleClick = (row: StudentGradeRow, column: any) => {
  const columnId = getColumnIdFromProperty(column.property)
  if (columnId) {
    startEdit(row.id, columnId)
  }
}

const handleSelectionChange = (selection: any[]) => {
  // Handle selection change if needed
}

const handleContextMenu = (event: MouseEvent, row: StudentGradeRow, column: any) => {
  event.preventDefault()
  const columnId = getColumnIdFromProperty(column.property)
  if (columnId) {
    gradeStore.actions.selectCell(row.id, columnId)
    contextMenuTarget.value = event.target
    nextTick(() => {
      contextMenuRef.value?.handleOpen()
    })
  }
}

const handleContextMenuCommand = (command: string) => {
  switch (command) {
    case 'edit':
      if (gradeStore.state.currentCell) {
        startEdit(gradeStore.state.currentCell.rowId, gradeStore.state.currentCell.columnId)
      }
      break
    case 'copy':
      gradeStore.actions.copy()
      hasClipboardData.value = true
      break
    case 'paste':
      gradeStore.actions.paste()
      break
    case 'clear':
      gradeStore.actions.clear()
      break
    case 'fill-down':
      gradeStore.actions.fill('down')
      break
    case 'fill-right':
      gradeStore.actions.fill('right')
      break
  }
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (!gradeStore.state.config.ui.enableKeyboardNavigation) return

  const { key, ctrlKey, shiftKey, altKey } = event

  // Prevent default for handled shortcuts
  if (handleKeyboardShortcut(key, ctrlKey, shiftKey, altKey)) {
    event.preventDefault()
  }
}

const handleKeyboardShortcut = (key: string, ctrlKey: boolean, shiftKey: boolean, altKey: boolean): boolean => {
  // Navigation shortcuts
  if (!ctrlKey && !altKey && !gradeStore.state.editingCell) {
    switch (key) {
      case 'ArrowUp':
        navigateCell('up', shiftKey)
        return true
      case 'ArrowDown':
        navigateCell('down', shiftKey)
        return true
      case 'ArrowLeft':
        navigateCell('left', shiftKey)
        return true
      case 'ArrowRight':
        navigateCell('right', shiftKey)
        return true
      case 'Tab':
        navigateCell(shiftKey ? 'previous' : 'next')
        return true
      case 'Enter':
        if (gradeStore.state.editingCell) {
          gradeStore.actions.finishEdit()
        } else {
          navigateCell('down', shiftKey)
        }
        return true
      case 'Escape':
        if (gradeStore.state.editingCell) {
          gradeStore.actions.cancelEdit()
        } else {
          gradeStore.actions.clearSelection()
        }
        return true
    }
  }

  // Editing shortcuts
  if (!ctrlKey && !altKey) {
    switch (key) {
      case 'F2':
        if (gradeStore.state.currentCell) {
          startEdit(gradeStore.state.currentCell.rowId, gradeStore.state.currentCell.columnId)
        }
        return true
      case 'Delete':
      case 'Backspace':
        if (!gradeStore.state.editingCell) {
          gradeStore.actions.clear()
          return true
        }
        break
    }
  }

  // System shortcuts
  if (ctrlKey && !altKey) {
    switch (key) {
      case 'a':
        if (!shiftKey) {
          gradeStore.actions.selectAll()
          return true
        }
        break
      case 'c':
        if (!shiftKey) {
          gradeStore.actions.copy()
          hasClipboardData.value = true
          return true
        }
        break
      case 'v':
        if (!shiftKey) {
          gradeStore.actions.paste()
          return true
        }
        break
      case 'x':
        if (!shiftKey) {
          gradeStore.actions.copy()
          gradeStore.actions.clear()
          hasClipboardData.value = true
          return true
        }
        break
      case 'z':
        if (shiftKey) {
          gradeStore.actions.redo()
        } else {
          gradeStore.actions.undo()
        }
        return true
      case 'y':
        if (!shiftKey) {
          gradeStore.actions.redo()
          return true
        }
        break
      case 's':
        if (!shiftKey) {
          saveGrades()
          return true
        }
        break
    }
  }

  return false
}

const navigateCell = (direction: 'up' | 'down' | 'left' | 'right' | 'next' | 'previous', extend = false) => {
  if (!gradeStore.state.currentCell) return

  const { rowId, columnId } = gradeStore.state.currentCell
  const rowIndex = gradeStore.state.rows.findIndex(r => r.id === rowId)
  const colIndex = gradeStore.state.columns.findIndex(c => c.id === columnId)

  let newRowIndex = rowIndex
  let newColIndex = colIndex

  switch (direction) {
    case 'up':
      newRowIndex = Math.max(0, rowIndex - 1)
      break
    case 'down':
      newRowIndex = Math.min(gradeStore.state.rows.length - 1, rowIndex + 1)
      break
    case 'left':
      newColIndex = Math.max(0, colIndex - 1)
      break
    case 'right':
      newColIndex = Math.min(gradeStore.state.columns.length - 1, colIndex + 1)
      break
    case 'next':
      if (colIndex < gradeStore.state.columns.length - 1) {
        newColIndex++
      } else if (rowIndex < gradeStore.state.rows.length - 1) {
        newRowIndex++
        newColIndex = 0
      }
      break
    case 'previous':
      if (colIndex > 0) {
        newColIndex--
      } else if (rowIndex > 0) {
        newRowIndex--
        newColIndex = gradeStore.state.columns.length - 1
      }
      break
  }

  if (newRowIndex !== rowIndex || newColIndex !== colIndex) {
    const newRow = gradeStore.state.rows[newRowIndex]
    const newColumn = gradeStore.state.columns[newColIndex]
    if (newRow && newColumn) {
      gradeStore.actions.selectCell(newRow.id, newColumn.id, extend)
    }
  }
}

const startEdit = (rowId: number, columnId: string) => {
  gradeStore.actions.startEdit(rowId, columnId)
}

const saveEdit = () => {
  gradeStore.actions.finishEdit()
}

const cancelEdit = () => {
  gradeStore.actions.cancelEdit()
}

const saveGrades = async () => {
  try {
    const updates: Record<string, number | null> = {}
    gradeStore.state.rows.forEach(row => {
      Object.entries(row.grades).forEach(([columnId, value]) => {
        updates[`${row.id}-${columnId}`] = value
      })
    })
    await gradeStore.actions.saveGrades(updates)
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const validateAll = () => {
  const errors = gradeStore.actions.validateAll()
  if (errors.length === 0) {
    ElMessage.success('所有数据验证通过')
  } else {
    ElMessage.warning(`发现 ${errors.length} 个验证错误`)
  }
}

const exportGrades = () => {
  // TODO: Implement export functionality
  ElMessage.info('导出功能开发中...')
}

const handleBulkOperation = (command: string) => {
  bulkOperationDialog.value.type = command as 'add-points' | 'multiply' | 'percentage'
  bulkOperationDialog.value.value = command === 'percentage' ? 100 : 0
  bulkOperationDialog.value.visible = true
}

const getBulkOperationTitle = (): string => {
  switch (bulkOperationDialog.value.type) {
    case 'add-points':
      return '批量加分'
    case 'multiply':
      return '批量乘以系数'
    case 'percentage':
      return '批量设置百分比'
    default:
      return '批量操作'
  }
}

const executeBulkOperation = () => {
  switch (bulkOperationDialog.value.type) {
    case 'add-points':
      gradeStore.actions.addPoints(bulkOperationDialog.value.value)
      break
    case 'multiply':
      gradeStore.actions.multiplyBy(bulkOperationDialog.value.value)
      break
    case 'percentage':
      gradeStore.actions.setPercentage(bulkOperationDialog.value.value)
      break
  }
  bulkOperationDialog.value.visible = false
  ElMessage.success('批量操作完成')
}

// Lifecycle
onMounted(() => {
  // Initialize any required setup
})

onUnmounted(() => {
  // Cleanup
})
</script>

<style scoped lang="scss">
.grade-spreadsheet {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.spreadsheet-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #f8f9fa;

  .toolbar-left,
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.error-alert {
  margin: 16px;
}

.validation-errors {
  margin: 0 16px 16px;

  .error-list {
    margin: 8px 0 0;
    padding-left: 20px;

    li {
      margin-bottom: 4px;
      font-size: 14px;
    }
  }
}

.spreadsheet-container {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.grade-table {
  :deep(.el-table__header) {
    background: #fafafa;
  }

  :deep(.el-table__body) {
    .cell-selected {
      background: #e6f7ff !important;
      border: 2px solid #1890ff;
    }

    .cell-error {
      background: #fff2f0 !important;
      border: 1px solid #ff4d4f;
    }

    .cell-editing {
      background: #f6ffed !important;
      border: 1px solid #52c41a;
    }
  }

  :deep(.row-modified) {
    background: #fffbe6;
  }

  :deep(.row-has-errors) {
    background: #fff2f0;
  }
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .info-icon {
    font-size: 14px;
    color: #909399;
    cursor: help;
    margin-left: 4px;
  }
}

.score-excellent {
  color: #67c23a;
  font-weight: bold;
}

.score-good {
  color: #409eff;
  font-weight: bold;
}

.score-average {
  color: #e6a23c;
}

.score-pass {
  color: #f56c6c;
}

.score-fail {
  color: #f56c6c;
  font-weight: bold;
}

.spreadsheet-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
  font-size: 14px;
  color: #606266;

  .status-left,
  .status-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .unsaved-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #e6a23c;
  }
}

// Mobile responsive
@media (max-width: 768px) {
  .spreadsheet-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;

    .toolbar-left,
    .toolbar-right {
      justify-content: center;
    }
  }

  .spreadsheet-status {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}
</style>