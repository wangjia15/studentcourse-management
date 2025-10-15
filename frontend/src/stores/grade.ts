import { defineStore } from 'pinia'
import { ref, computed, reactive, nextTick, watch } from 'vue'
import { gradeApi } from '@/lib/api'
import type {
  GradeSpreadsheetState,
  GradeSpreadsheetActions,
  GradeSpreadsheetGetters,
  GradeCell,
  GradeSelection,
  GradeValidationError,
  GradeHistoryEntry,
  GradeOperation,
  StudentGradeRow,
  GradeColumn,
  CourseInfo,
  GradeCategory,
  DEFAULT_SPREADSHEET_CONFIG,
  DEFAULT_GRADE_VALIDATION_RULE
} from '@/types/grade'

export const useGradeStore = defineStore('grade', () => {
  // State
  const state = reactive<GradeSpreadsheetState>({
    // Data
    columns: [],
    rows: [],
    courseInfo: null,

    // UI State
    loading: false,
    saving: false,
    error: null,

    // Selection and editing
    selectedCells: [],
    currentCell: null,
    editingCell: null,

    // Validation
    validationErrors: [],

    // History
    history: [],
    historyIndex: -1,

    // Performance
    visibleRange: {
      startRow: 0,
      endRow: 100,
      startColumn: 0,
      endColumn: 10
    },

    // Configuration
    config: DEFAULT_SPREADSHEET_CONFIG
  })

  // Auto-save timer
  let autoSaveTimer: NodeJS.Timeout | null = null

  // Clipboard for copy/paste operations
  const clipboard = ref<Record<string, number | null>>({})

  // Getters
  const getters: GradeSpreadsheetGetters = {
    totalRows: computed(() => state.rows.length),
    totalColumns: computed(() => state.columns.length),

    modifiedRows: computed(() =>
      state.rows.filter(row => row.isModified || row.hasErrors).map(row => row.id)
    ),

    hasUnsavedChanges: computed(() => getters.modifiedRows.value.length > 0),

    selectedData: computed(() => {
      const data: Record<string, number | null> = {}
      state.selectedCells.forEach(selection => {
        for (let row = selection.startRow; row <= selection.endRow; row++) {
          for (let colIndex = state.columns.findIndex(col => col.id === selection.startColumn);
               colIndex <= state.columns.findIndex(col => col.id === selection.endColumn);
               colIndex++) {
            if (row >= 0 && row < state.rows.length && colIndex >= 0 && colIndex < state.columns.length) {
              const column = state.columns[colIndex]
              const rowData = state.rows[row]
              const key = `${rowData.id}-${column.id}`
              data[key] = rowData.grades[column.id] ?? null
            }
          }
        }
      })
      return data
    }),

    selectedRows: computed(() => {
      const rows = new Set<number>()
      state.selectedCells.forEach(selection => {
        for (let row = selection.startRow; row <= selection.endRow; row++) {
          if (row >= 0 && row < state.rows.length) {
            rows.add(state.rows[row].id)
          }
        }
      })
      return Array.from(rows)
    }),

    selectedColumns: computed(() => {
      const columns = new Set<string>()
      state.selectedCells.forEach(selection => {
        const startColIndex = state.columns.findIndex(col => col.id === selection.startColumn)
        const endColIndex = state.columns.findIndex(col => col.id === selection.endColumn)
        for (let col = startColIndex; col <= endColIndex; col++) {
          if (col >= 0 && col < state.columns.length) {
            columns.add(state.columns[col].id)
          }
        }
      })
      return Array.from(columns)
    }),

    hasErrors: computed(() => state.validationErrors.length > 0),
    errorCount: computed(() => state.validationErrors.length),

    visibleRows: computed(() =>
      state.rows.slice(state.visibleRange.startRow, state.visibleRange.endRow + 1)
    ),

    visibleColumns: computed(() =>
      state.columns.slice(state.visibleRange.startColumn, state.visibleRange.endColumn + 1)
    ),

    canUndo: computed(() => state.historyIndex > 0),
    canRedo: computed(() => state.historyIndex < state.history.length - 1),
    canSave: computed(() => getters.hasUnsavedChanges.value && !state.saving)
  }

  // Actions
  const actions: GradeSpreadsheetActions = {
    // Data operations
    async loadGrades(courseId: number) {
      state.loading = true
      state.error = null

      try {
        // Load course info
        const courseResponse = await gradeApi.getCourse(courseId)
        state.courseInfo = courseResponse.data

        // Load students and grades
        const gradesResponse = await gradeApi.getCourseGrades(courseId)
        const { students, columns, grades } = gradesResponse.data

        // Process and map data
        state.columns = columns.map((col: any) => ({
          ...col,
          isVisible: true,
          order: col.order || 0
        }))

        state.rows = students.map((student: any, index: number) => ({
          id: student.id,
          studentId: student.student_id,
          studentName: student.name,
          gender: student.gender,
          major: student.major,
          grade: student.grade,
          class: student.class,
          email: student.email,
          phone: student.phone,
          grades: grades[index] || {},
          totalScore: calculateTotalScore(grades[index] || {}, state.columns),
          averageScore: calculateAverageScore(grades[index] || {}, state.columns),
          rank: 0,
          isModified: false,
          hasErrors: false,
          lastModified: undefined
        }))

        // Calculate ranks
        calculateRanks()

        // Clear history after loading
        actions.clearHistory()

      } catch (error: any) {
        state.error = error.response?.data?.message || '加载成绩数据失败'
        console.error('Error loading grades:', error)
      } finally {
        state.loading = false
      }
    },

    async saveGrades(grades: Record<string, number | null>) {
      if (!state.courseInfo) return

      state.saving = true
      state.error = null

      try {
        const updates = Object.entries(grades).map(([key, value]) => {
          const [rowId, columnId] = key.split('-')
          return {
            student_id: parseInt(rowId),
            column_id: columnId,
            score: value
          }
        })

        await gradeApi.updateGrades(state.courseInfo.id, { updates })

        // Update local state
        Object.entries(grades).forEach(([key, value]) => {
          const [rowId, columnId] = key.split('-')
          const row = state.rows.find(r => r.id === parseInt(rowId))
          if (row) {
            row.grades[columnId] = value
            row.isModified = false
            row.totalScore = calculateTotalScore(row.grades, state.columns)
            row.averageScore = calculateAverageScore(row.grades, state.columns)
          }
        })

        // Recalculate ranks
        calculateRanks()

        // Clear validation errors for saved cells
        state.validationErrors = state.validationErrors.filter(
          error => !Object.keys(grades).includes(`${error.rowId}-${error.columnId}`)
        )

      } catch (error: any) {
        state.error = error.response?.data?.message || '保存成绩失败'
        console.error('Error saving grades:', error)
        throw error
      } finally {
        state.saving = false
      }
    },

    updateCell(rowId: number, columnId: string, value: number | null) {
      const row = state.rows.find(r => r.id === rowId)
      if (!row) return

      const originalValue = row.grades[columnId] ?? null

      // Validate value
      const validationError = actions.validateCell(rowId, columnId, value)
      if (validationError) {
        state.validationErrors.push({
          rowId,
          columnId,
          message: validationError,
          type: 'range'
        })
        row.hasErrors = true
      } else {
        // Remove existing validation error for this cell
        state.validationErrors = state.validationErrors.filter(
          error => !(error.rowId === rowId && error.columnId === columnId)
        )
        row.hasErrors = state.validationErrors.some(error => error.rowId === rowId)
      }

      // Update value
      row.grades[columnId] = value
      row.isModified = true
      row.lastModified = new Date().toISOString()

      // Update calculated scores
      row.totalScore = calculateTotalScore(row.grades, state.columns)
      row.averageScore = calculateAverageScore(row.grades, state.columns)

      // Add to history
      const operation: GradeOperation = {
        type: value !== null ? 'set' : 'clear',
        value,
        targetRange: {
          startRow: state.rows.findIndex(r => r.id === rowId),
          endRow: state.rows.findIndex(r => r.id === rowId),
          startColumn: columnId,
          endColumn: columnId,
          type: 'cell'
        },
        timestamp: new Date().toISOString()
      }

      addToHistory(operation, { [`${rowId}-${columnId}`]: originalValue }, { [`${rowId}-${columnId}`]: value })

      // Auto-save if enabled
      if (state.config.autoSave.enabled) {
        scheduleAutoSave()
      }
    },

    batchUpdate(updates: Record<string, number | null>) {
      Object.entries(updates).forEach(([key, value]) => {
        const [rowId, columnId] = key.split('-')
        actions.updateCell(parseInt(rowId), columnId, value)
      })
    },

    // Selection operations
    selectCell(rowId: number, columnId: string, extend = false) {
      const rowIndex = state.rows.findIndex(r => r.id === rowId)
      const colIndex = state.columns.findIndex(c => c.id === columnId)

      if (rowIndex === -1 || colIndex === -1) return

      const selection: GradeSelection = {
        startRow: rowIndex,
        endRow: rowIndex,
        startColumn: columnId,
        endColumn: columnId,
        type: 'cell'
      }

      if (extend && state.selectedCells.length > 0) {
        const lastSelection = state.selectedCells[state.selectedCells.length - 1]
        selection.startRow = Math.min(lastSelection.startRow, rowIndex)
        selection.endRow = Math.max(lastSelection.endRow, rowIndex)
        selection.startColumn = lastSelection.startColumn
        selection.endColumn = columnId
        selection.type = 'range'
      }

      state.selectedCells = [selection]
      state.currentCell = { rowId, columnId, value: null, originalValue: null, isEditing: false, isValid: true, lastModified: new Date().toISOString() }
    },

    selectRow(rowId: number, extend = false) {
      const rowIndex = state.rows.findIndex(r => r.id === rowId)
      if (rowIndex === -1) return

      const selection: GradeSelection = {
        startRow: rowIndex,
        endRow: rowIndex,
        startColumn: state.columns[0]?.id || '',
        endColumn: state.columns[state.columns.length - 1]?.id || '',
        type: 'row'
      }

      if (extend && state.selectedCells.length > 0) {
        const lastSelection = state.selectedCells[state.selectedCells.length - 1]
        selection.startRow = Math.min(lastSelection.startRow, rowIndex)
        selection.endRow = Math.max(lastSelection.endRow, rowIndex)
        selection.type = 'range'
      }

      state.selectedCells = [selection]
    },

    selectColumn(columnId: string, extend = false) {
      const colIndex = state.columns.findIndex(c => c.id === columnId)
      if (colIndex === -1) return

      const selection: GradeSelection = {
        startRow: 0,
        endRow: state.rows.length - 1,
        startColumn: columnId,
        endColumn: columnId,
        type: 'column'
      }

      if (extend && state.selectedCells.length > 0) {
        const lastSelection = state.selectedCells[state.selectedCells.length - 1]
        selection.startColumn = lastSelection.startColumn
        selection.endColumn = columnId
        selection.type = 'range'
      }

      state.selectedCells = [selection]
    },

    selectAll() {
      if (state.columns.length === 0 || state.rows.length === 0) return

      state.selectedCells = [{
        startRow: 0,
        endRow: state.rows.length - 1,
        startColumn: state.columns[0].id,
        endColumn: state.columns[state.columns.length - 1].id,
        type: 'range'
      }]
    },

    clearSelection() {
      state.selectedCells = []
      state.currentCell = null
    },

    // Editing operations
    startEdit(rowId: number, columnId: string) {
      const row = state.rows.find(r => r.id === rowId)
      if (!row) return

      state.editingCell = {
        rowId,
        columnId,
        value: row.grades[columnId] ?? null,
        originalValue: row.grades[columnId] ?? null,
        isEditing: true,
        isValid: true,
        lastModified: new Date().toISOString()
      }
    },

    finishEdit() {
      if (!state.editingCell) return

      const { rowId, columnId, value } = state.editingCell
      actions.updateCell(rowId, columnId, value)
      state.editingCell = null
    },

    cancelEdit() {
      if (!state.editingCell) return
      state.editingCell = null
    },

    // Batch operations
    copy() {
      clipboard.value = getters.selectedData.value
    },

    paste() {
      if (state.selectedCells.length === 0 || Object.keys(clipboard.value).length === 0) return

      const updates: Record<string, number | null> = {}
      const clipboardEntries = Object.entries(clipboard.value)

      state.selectedCells.forEach(selection => {
        for (let row = selection.startRow; row <= selection.endRow; row++) {
          for (let colIndex = state.columns.findIndex(col => col.id === selection.startColumn);
               colIndex <= state.columns.findIndex(col => col.id === selection.endColumn);
               colIndex++) {
            if (row >= 0 && row < state.rows.length && colIndex >= 0 && colIndex < state.columns.length) {
              const column = state.columns[colIndex]
              const rowData = state.rows[row]
              const key = `${rowData.id}-${column.id}`

              // Get corresponding clipboard value (with wrap-around)
              const clipboardIndex = ((row - selection.startRow) * Math.abs(selection.endColumn.charCodeAt(0) - selection.startColumn.charCodeAt(0)) +
                                    (colIndex - state.columns.findIndex(col => col.id === selection.startColumn))) % clipboardEntries.length
              const [, value] = clipboardEntries[clipboardIndex]

              updates[key] = value
            }
          }
        }
      })

      actions.batchUpdate(updates)
    },

    fill(direction: 'up' | 'down' | 'left' | 'right') {
      if (state.selectedCells.length === 0) return

      const updates: Record<string, number | null> = {}

      state.selectedCells.forEach(selection => {
        for (let row = selection.startRow; row <= selection.endRow; row++) {
          for (let colIndex = state.columns.findIndex(col => col.id === selection.startColumn);
               colIndex <= state.columns.findIndex(col => col.id === selection.endColumn);
               colIndex++) {
            if (row >= 0 && row < state.rows.length && colIndex >= 0 && colIndex < state.columns.length) {
              const column = state.columns[colIndex]
              const rowData = state.rows[row]

              // Get source value based on direction
              let sourceRow = row
              let sourceCol = colIndex

              switch (direction) {
                case 'up':
                  sourceRow = selection.endRow + 1
                  break
                case 'down':
                  sourceRow = selection.startRow - 1
                  break
                case 'left':
                  sourceCol = state.columns.findIndex(col => col.id === selection.endColumn) + 1
                  break
                case 'right':
                  sourceCol = state.columns.findIndex(col => col.id === selection.startColumn) - 1
                  break
              }

              if (sourceRow >= 0 && sourceRow < state.rows.length &&
                  sourceCol >= 0 && sourceCol < state.columns.length) {
                const sourceColumn = state.columns[sourceCol]
                const sourceRowData = state.rows[sourceRow]
                const value = sourceRowData.grades[sourceColumn.id] ?? null

                const key = `${rowData.id}-${column.id}`
                updates[key] = value
              }
            }
          }
        }
      })

      actions.batchUpdate(updates)
    },

    clear() {
      const updates: Record<string, number | null> = {}

      state.selectedCells.forEach(selection => {
        for (let row = selection.startRow; row <= selection.endRow; row++) {
          for (let colIndex = state.columns.findIndex(col => col.id === selection.startColumn);
               colIndex <= state.columns.findIndex(col => col.id === selection.endColumn);
               colIndex++) {
            if (row >= 0 && row < state.rows.length && colIndex >= 0 && colIndex < state.columns.length) {
              const column = state.columns[colIndex]
              const rowData = state.rows[row]
              const key = `${rowData.id}-${column.id}`
              updates[key] = null
            }
          }
        }
      })

      actions.batchUpdate(updates)
    },

    // Grade operations
    addPoints(points: number) {
      const updates: Record<string, number | null> = {}

      state.selectedCells.forEach(selection => {
        for (let row = selection.startRow; row <= selection.endRow; row++) {
          for (let colIndex = state.columns.findIndex(col => col.id === selection.startColumn);
               colIndex <= state.columns.findIndex(col => col.id === selection.endColumn);
               colIndex++) {
            if (row >= 0 && row < state.rows.length && colIndex >= 0 && colIndex < state.columns.length) {
              const column = state.columns[colIndex]
              const rowData = state.rows[row]
              const currentValue = rowData.grades[column.id] ?? 0
              const newValue = Math.min(Math.max(0, currentValue + points), column.maxScore)
              const key = `${rowData.id}-${column.id}`
              updates[key] = newValue
            }
          }
        }
      })

      actions.batchUpdate(updates)
    },

    multiplyBy(factor: number) {
      const updates: Record<string, number | null> = {}

      state.selectedCells.forEach(selection => {
        for (let row = selection.startRow; row <= selection.endRow; row++) {
          for (let colIndex = state.columns.findIndex(col => col.id === selection.startColumn);
               colIndex <= state.columns.findIndex(col => col.id === selection.endColumn);
               colIndex++) {
            if (row >= 0 && row < state.rows.length && colIndex >= 0 && colIndex < state.columns.length) {
              const column = state.columns[colIndex]
              const rowData = state.rows[row]
              const currentValue = rowData.grades[column.id] ?? 0
              const newValue = Math.min(Math.max(0, currentValue * factor), column.maxScore)
              const key = `${rowData.id}-${column.id}`
              updates[key] = newValue
            }
          }
        }
      })

      actions.batchUpdate(updates)
    },

    setPercentage(percentage: number) {
      const factor = percentage / 100
      actions.multiplyBy(factor)
    },

    // History operations
    undo() {
      if (!getters.canUndo.value) return

      state.historyIndex--
      const entry = state.history[state.historyIndex]

      // Restore previous values
      Object.entries(entry.previousValues).forEach(([key, value]) => {
        const [rowId, columnId] = key.split('-')
        const row = state.rows.find(r => r.id === parseInt(rowId))
        if (row) {
          row.grades[columnId] = value
          row.isModified = true
          row.totalScore = calculateTotalScore(row.grades, state.columns)
          row.averageScore = calculateAverageScore(row.grades, state.columns)
        }
      })

      calculateRanks()
    },

    redo() {
      if (!getters.canRedo.value) return

      state.historyIndex++
      const entry = state.history[state.historyIndex]

      // Restore new values
      Object.entries(entry.newValues).forEach(([key, value]) => {
        const [rowId, columnId] = key.split('-')
        const row = state.rows.find(r => r.id === parseInt(rowId))
        if (row) {
          row.grades[columnId] = value
          row.isModified = true
          row.totalScore = calculateTotalScore(row.grades, state.columns)
          row.averageScore = calculateAverageScore(row.grades, state.columns)
        }
      })

      calculateRanks()
    },

    clearHistory() {
      state.history = []
      state.historyIndex = -1
    },

    // Validation
    validateAll() {
      const errors: GradeValidationError[] = []

      state.rows.forEach(row => {
        state.columns.forEach(column => {
          const value = row.grades[column.id]
          const error = actions.validateCell(row.id, column.id, value)
          if (error) {
            errors.push({
              rowId: row.id,
              columnId: column.id,
              message: error,
              type: 'range'
            })
          }
        })
      })

      state.validationErrors = errors
      return errors
    },

    validateCell(rowId: number, columnId: string, value: number | null): string | null {
      const column = state.columns.find(c => c.id === columnId)
      if (!column) return '列不存在'

      // Required validation
      if (column.isRequired && (value === null || value === undefined)) {
        return '此列为必填项'
      }

      // Skip validation for empty values if not required
      if (value === null || value === undefined) {
        return null
      }

      // Range validation
      if (value < 0 || value > column.maxScore) {
        return `分数必须在 0 到 ${column.maxScore} 之间`
      }

      // Decimal validation
      if (!DEFAULT_GRADE_VALIDATION_RULE.allowDecimals && !Number.isInteger(value)) {
        return '此列不支持小数'
      }

      if (DEFAULT_GRADE_VALIDATION_RULE.decimalPlaces &&
          value.toFixed(DEFAULT_GRADE_VALIDATION_RULE.decimalPlaces) !== value.toString()) {
        return `最多支持 ${DEFAULT_GRADE_VALIDATION_RULE.decimalPlaces} 位小数`
      }

      return null
    },

    // Configuration
    updateConfig(config: Partial<typeof DEFAULT_SPREADSHEET_CONFIG>) {
      state.config = { ...state.config, ...config }
    },

    // Performance
    updateVisibleRange(range: GradeSpreadsheetState['visibleRange']) {
      state.visibleRange = range
    }
  }

  // Helper functions
  function calculateTotalScore(grades: Record<string, number | null>, columns: GradeColumn[]): number {
    return columns.reduce((total, column) => {
      const score = grades[column.id] ?? 0
      return total + (score * column.weight / 100)
    }, 0)
  }

  function calculateAverageScore(grades: Record<string, number | null>, columns: GradeColumn[]): number {
    const totalWeight = columns.reduce((sum, col) => sum + col.weight, 0)
    if (totalWeight === 0) return 0

    const totalScore = calculateTotalScore(grades, columns)
    return totalScore / totalWeight * 100
  }

  function calculateRanks() {
    const sortedRows = [...state.rows].sort((a, b) => (b.totalScore || 0) - (a.totalScore || 0))
    sortedRows.forEach((row, index) => {
      const actualRow = state.rows.find(r => r.id === row.id)
      if (actualRow) {
        actualRow.rank = index + 1
      }
    })
  }

  function addToHistory(operation: GradeOperation, previousValues: Record<string, number | null>, newValues: Record<string, number | null>) {
    const entry: GradeHistoryEntry = {
      id: Date.now().toString(),
      operation,
      previousValues,
      newValues,
      userId: 1, // TODO: Get from auth store
      timestamp: new Date().toISOString(),
      description: generateOperationDescription(operation)
    }

    // Remove any entries after current index
    state.history = state.history.slice(0, state.historyIndex + 1)

    // Add new entry
    state.history.push(entry)
    state.historyIndex++

    // Limit history size
    if (state.history.length > 100) {
      state.history.shift()
      state.historyIndex--
    }
  }

  function generateOperationDescription(operation: GradeOperation): string {
    switch (operation.type) {
      case 'set':
        return `设置单元格值为 ${operation.value}`
      case 'add':
        return `加分 ${operation.value}`
      case 'multiply':
        return `乘以系数 ${operation.value}`
      case 'clear':
        return '清空单元格'
      case 'fill':
        return '填充单元格'
      default:
        return '未知操作'
    }
  }

  function scheduleAutoSave() {
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer)
    }

    autoSaveTimer = setTimeout(async () => {
      if (getters.hasUnsavedChanges.value) {
        try {
          const updates: Record<string, number | null> = {}
          state.rows.forEach(row => {
            Object.entries(row.grades).forEach(([columnId, value]) => {
              updates[`${row.id}-${columnId}`] = value
            })
          })
          await actions.saveGrades(updates)
        } catch (error) {
          console.error('Auto-save failed:', error)
        }
      }
    }, state.config.autoSave.debounce)
  }

  // Watch for window unload to prevent data loss
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', (event) => {
      if (getters.hasUnsavedChanges.value) {
        event.preventDefault()
        event.returnValue = '您有未保存的更改，确定要离开吗？'
      }
    })
  }

  return {
    state,
    actions,
    getters
  }
})