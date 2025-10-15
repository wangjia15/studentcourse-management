import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useGradeStore } from '../grade'
import { gradeApi } from '@/lib/api'
import type { GradeColumn, StudentGradeRow } from '@/types/grade'

// Mock API
vi.mock('@/lib/api')

describe('Grade Store', () => {
  let gradeStore: any

  const mockCourseInfo = {
    id: 1,
    code: 'CS101',
    name: '计算机科学导论',
    credit: 3,
    totalWeight: 100,
    semester: '2023-2024-1',
    academicYear: '2023-2024',
    teacherId: 1,
    teacherName: '王老师',
    isActive: true
  }

  const mockColumns: GradeColumn[] = [
    {
      id: 'assignment1',
      title: '作业1',
      category: { id: 'assignment', name: '作业', weight: 20 },
      maxScore: 100,
      weight: 20,
      isRequired: true,
      isVisible: true,
      order: 1
    }
  ]

  const mockStudents = [
    {
      id: 1,
      student_id: '2021001',
      name: '张三',
      gender: '男',
      major: '计算机科学与技术',
      grade: '2021级',
      class: '计科2101',
      email: 'zhangsan@example.com',
      phone: '13800138001'
    }
  ]

  const mockGrades = {
    1: { assignment1: 85 }
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    gradeStore = useGradeStore()

    // Reset mocks
    vi.clearAllMocks()

    // Mock API responses
    vi.mocked(gradeApi.getCourse).mockResolvedValue({
      data: mockCourseInfo
    })

    vi.mocked(gradeApi.getCourseGrades).mockResolvedValue({
      data: {
        students: mockStudents,
        columns: mockColumns,
        grades: mockGrades
      }
    })

    vi.mocked(gradeApi.updateGrades).mockResolvedValue({
      data: { success: true }
    })
  })

  describe('State Management', () => {
    it('initializes with correct default state', () => {
      expect(gradeStore.state.loading).toBe(false)
      expect(gradeStore.state.saving).toBe(false)
      expect(gradeStore.state.error).toBeNull()
      expect(gradeStore.state.columns).toEqual([])
      expect(gradeStore.state.rows).toEqual([])
      expect(gradeStore.state.courseInfo).toBeNull()
      expect(gradeStore.state.selectedCells).toEqual([])
      expect(gradeStore.state.currentCell).toBeNull()
      expect(gradeStore.state.editingCell).toBeNull()
      expect(gradeStore.state.validationErrors).toEqual([])
      expect(gradeStore.state.history).toEqual([])
      expect(gradeStore.state.historyIndex).toBe(-1)
    })

    it('has correct computed getters', () => {
      // Add some test data
      gradeStore.state.columns = mockColumns
      gradeStore.state.rows = [{
        ...mockStudents[0],
        id: mockStudents[0].id,
        studentId: mockStudents[0].student_id,
        studentName: mockStudents[0].name,
        gender: mockStudents[0].gender,
        major: mockStudents[0].major,
        grade: mockStudents[0].grade,
        class: mockStudents[0].class,
        email: mockStudents[0].email,
        phone: mockStudents[0].phone,
        grades: mockGrades[1],
        totalScore: 85,
        averageScore: 85,
        rank: 1,
        isModified: false,
        hasErrors: false
      }]

      expect(gradeStore.getters.totalRows).toBe(1)
      expect(gradeStore.getters.totalColumns).toBe(1)
      expect(gradeStore.getters.modifiedRows).toEqual([])
      expect(gradeStore.getters.hasUnsavedChanges).toBe(false)
      expect(gradeStore.getters.hasErrors).toBe(false)
      expect(gradeStore.getters.errorCount).toBe(0)
      expect(gradeStore.getters.canUndo).toBe(false)
      expect(gradeStore.getters.canRedo).toBe(false)
    })
  })

  describe('loadGrades', () => {
    it('loads course and grades successfully', async () => {
      await gradeStore.actions.loadGrades(1)

      expect(gradeStore.state.loading).toBe(false)
      expect(gradeStore.state.courseInfo).toEqual(mockCourseInfo)
      expect(gradeStore.state.columns).toEqual(mockColumns)
      expect(gradeStore.state.rows).toHaveLength(1)
      expect(gradeStore.state.rows[0].studentName).toBe('张三')
      expect(gradeStore.state.rows[0].grades).toEqual(mockGrades[1])
      expect(gradeApi.getCourse).toHaveBeenCalledWith(1)
      expect(gradeApi.getCourseGrades).toHaveBeenCalledWith(1)
    })

    it('handles loading errors correctly', async () => {
      const error = new Error('API Error')
      vi.mocked(gradeApi.getCourse).mockRejectedValue(error)

      await gradeStore.actions.loadGrades(1)

      expect(gradeStore.state.loading).toBe(false)
      expect(gradeStore.state.error).toBe('加载成绩数据失败')
    })

    it('sets loading state during fetch', async () => {
      const promise = gradeStore.actions.loadGrades(1)
      expect(gradeStore.state.loading).toBe(true)

      await promise
      expect(gradeStore.state.loading).toBe(false)
    })
  })

  describe('updateCell', () => {
    beforeEach(async () => {
      await gradeStore.actions.loadGrades(1)
    })

    it('updates cell value correctly', () => {
      const rowId = 1
      const columnId = 'assignment1'
      const newValue = 90

      gradeStore.actions.updateCell(rowId, columnId, newValue)

      const row = gradeStore.state.rows.find(r => r.id === rowId)
      expect(row?.grades[columnId]).toBe(newValue)
      expect(row?.isModified).toBe(true)
      expect(row?.totalScore).toBe(90)
      expect(row?.averageScore).toBe(90)
    })

    it('validates cell value and adds errors', () => {
      const rowId = 1
      const columnId = 'assignment1'
      const invalidValue = 150

      gradeStore.actions.updateCell(rowId, columnId, invalidValue)

      expect(gradeStore.state.validationErrors).toHaveLength(1)
      expect(gradeStore.state.validationErrors[0].message).toBe('分数必须在 0 到 100 之间')

      const row = gradeStore.state.rows.find(r => r.id === rowId)
      expect(row?.hasErrors).toBe(true)
    })

    it('adds to history when updating cell', () => {
      const rowId = 1
      const columnId = 'assignment1'
      const newValue = 90

      gradeStore.actions.updateCell(rowId, columnId, newValue)

      expect(gradeStore.state.history).toHaveLength(1)
      expect(gradeStore.state.historyIndex).toBe(0)
      expect(gradeStore.state.history[0].operation.type).toBe('set')
      expect(gradeStore.state.history[0].operation.value).toBe(newValue)
    })

    it('clears validation errors for valid values', () => {
      const rowId = 1
      const columnId = 'assignment1'

      // First add an error
      gradeStore.actions.updateCell(rowId, columnId, 150)
      expect(gradeStore.state.validationErrors).toHaveLength(1)

      // Then fix it
      gradeStore.actions.updateCell(rowId, columnId, 85)
      expect(gradeStore.state.validationErrors).toHaveLength(0)
    })
  })

  describe('Selection Management', () => {
    beforeEach(async () => {
      await gradeStore.actions.loadGrades(1)
    })

    it('selects a single cell', () => {
      gradeStore.actions.selectCell(1, 'assignment1')

      expect(gradeStore.state.selectedCells).toHaveLength(1)
      expect(gradeStore.state.selectedCells[0].type).toBe('cell')
      expect(gradeStore.state.currentCell?.rowId).toBe(1)
      expect(gradeStore.state.currentCell?.columnId).toBe('assignment1')
    })

    it('extends selection to range', () => {
      // First select initial cell
      gradeStore.actions.selectCell(1, 'assignment1')

      // Then extend selection
      gradeStore.actions.selectCell(1, 'assignment1', true)

      expect(gradeStore.state.selectedCells).toHaveLength(1)
      expect(gradeStore.state.selectedCells[0].type).toBe('range')
    })

    it('selects entire row', () => {
      gradeStore.actions.selectRow(1)

      expect(gradeStore.state.selectedCells).toHaveLength(1)
      expect(gradeStore.state.selectedCells[0].type).toBe('row')
    })

    it('selects entire column', () => {
      gradeStore.actions.selectColumn('assignment1')

      expect(gradeStore.state.selectedCells).toHaveLength(1)
      expect(gradeStore.state.selectedCells[0].type).toBe('column')
    })

    it('selects all cells', () => {
      gradeStore.actions.selectAll()

      expect(gradeStore.state.selectedCells).toHaveLength(1)
      expect(gradeStore.state.selectedCells[0].type).toBe('range')
    })

    it('clears selection', () => {
      gradeStore.actions.selectCell(1, 'assignment1')
      expect(gradeStore.state.selectedCells).toHaveLength(1)

      gradeStore.actions.clearSelection()
      expect(gradeStore.state.selectedCells).toHaveLength(0)
      expect(gradeStore.state.currentCell).toBeNull()
    })
  })

  describe('Batch Operations', () => {
    beforeEach(async () => {
      await gradeStore.actions.loadGrades(1)
      gradeStore.actions.selectCell(1, 'assignment1')
    })

    it('copies selected data', () => {
      gradeStore.actions.copy()
      // Note: clipboard is internal, but we can test that copy was called
      expect(gradeStore.state.selectedCells).toHaveLength(1)
    })

    it('clears selected cells', () => {
      gradeStore.actions.clear()

      const row = gradeStore.state.rows.find(r => r.id === 1)
      expect(row?.grades['assignment1']).toBeNull()
      expect(row?.isModified).toBe(true)
    })

    it('adds points to selected cells', () => {
      gradeStore.actions.addPoints(5)

      const row = gradeStore.state.rows.find(r => r.id === 1)
      expect(row?.grades['assignment1']).toBe(90) // 85 + 5
    })

    it('multiplies selected cells', () => {
      gradeStore.actions.multiplyBy(1.1)

      const row = gradeStore.state.rows.find(r => r.id === 1)
      expect(row?.grades['assignment1']).toBe(93.5) // 85 * 1.1
    })

    it('sets percentage for selected cells', () => {
      gradeStore.actions.setPercentage(90)

      const row = gradeStore.state.rows.find(r => r.id === 1)
      expect(row?.grades['assignment1']).toBe(76.5) // 85 * 0.9
    })
  })

  describe('History Management', () => {
    beforeEach(async () => {
      await gradeStore.actions.loadGrades(1)
    })

    it('can undo changes', () => {
      // Make a change
      gradeStore.actions.updateCell(1, 'assignment1', 90)
      expect(gradeStore.getters.canUndo).toBe(true)

      // Undo the change
      gradeStore.actions.undo()
      expect(gradeStore.getters.canUndo).toBe(false)

      const row = gradeStore.state.rows.find(r => r.id === 1)
      expect(row?.grades['assignment1']).toBe(85) // Back to original value
    })

    it('can redo changes', () => {
      // Make a change
      gradeStore.actions.updateCell(1, 'assignment1', 90)

      // Undo the change
      gradeStore.actions.undo()
      expect(gradeStore.getters.canRedo).toBe(true)

      // Redo the change
      gradeStore.actions.redo()
      expect(gradeStore.getters.canRedo).toBe(false)

      const row = gradeStore.state.rows.find(r => r.id === 1)
      expect(row?.grades['assignment1']).toBe(90) // Back to changed value
    })

    it('clears history correctly', () => {
      // Make some changes
      gradeStore.actions.updateCell(1, 'assignment1', 90)
      gradeStore.actions.updateCell(1, 'assignment1', 95)

      expect(gradeStore.state.history).toHaveLength(2)

      gradeStore.actions.clearHistory()
      expect(gradeStore.state.history).toHaveLength(0)
      expect(gradeStore.state.historyIndex).toBe(-1)
    })
  })

  describe('Validation', () => {
    beforeEach(async () => {
      await gradeStore.actions.loadGrades(1)
    })

    it('validates cell values correctly', () => {
      // Valid value
      expect(gradeStore.actions.validateCell(1, 'assignment1', 85)).toBeNull()

      // Invalid range - too high
      expect(gradeStore.actions.validateCell(1, 'assignment1', 150))
        .toBe('分数必须在 0 到 100 之间')

      // Invalid range - negative
      expect(gradeStore.actions.validateCell(1, 'assignment1', -5))
        .toBe('分数必须在 0 到 100 之间')

      // Null value for required field
      expect(gradeStore.actions.validateCell(1, 'assignment1', null))
        .toBe('此列为必填项')
    })

    it('validates all cells', () => {
      // Add an invalid value
      gradeStore.state.rows[0].grades['assignment1'] = 150

      const errors = gradeStore.actions.validateAll()
      expect(errors).toHaveLength(1)
      expect(errors[0].message).toBe('分数必须在 0 到 100 之间')
      expect(gradeStore.state.validationErrors).toHaveLength(1)
    })
  })

  describe('Save Operations', () => {
    beforeEach(async () => {
      await gradeStore.actions.loadGrades(1)
    })

    it('saves grades successfully', async () => {
      // Make some changes
      gradeStore.actions.updateCell(1, 'assignment1', 90)

      const updates = { '1-assignment1': 90 }
      await gradeStore.actions.saveGrades(updates)

      expect(gradeStore.state.saving).toBe(false)
      expect(gradeApi.updateGrades).toHaveBeenCalledWith(1, {
        updates: [
          {
            student_id: 1,
            column_id: 'assignment1',
            score: 90
          }
        ]
      })

      const row = gradeStore.state.rows.find(r => r.id === 1)
      expect(row?.isModified).toBe(false)
    })

    it('handles save errors', async () => {
      const error = new Error('Save failed')
      vi.mocked(gradeApi.updateGrades).mockRejectedValue(error)

      const updates = { '1-assignment1': 90 }

      await expect(gradeStore.actions.saveGrades(updates)).rejects.toThrow()
      expect(gradeStore.state.saving).toBe(false)
      expect(gradeStore.state.error).toBe('保存成绩失败')
    })
  })

  describe('Configuration', () => {
    it('updates configuration correctly', () => {
      const newConfig = {
        virtualScrolling: {
          enabled: false,
          itemHeight: 50,
          bufferSize: 15,
          threshold: 200
        }
      }

      gradeStore.actions.updateConfig(newConfig)

      expect(gradeStore.state.config.virtualScrolling.enabled).toBe(false)
      expect(gradeStore.state.config.virtualScrolling.itemHeight).toBe(50)
      expect(gradeStore.state.config.virtualScrolling.bufferSize).toBe(15)
      expect(gradeStore.state.config.virtualScrolling.threshold).toBe(200)
    })
  })

  describe('Performance', () => {
    it('calculates ranks correctly', async () => {
      // Add more students with different scores
      gradeStore.state.rows = [
        {
          id: 1,
          studentId: '2021001',
          studentName: '张三',
          gender: '男',
          major: '计算机科学与技术',
          grade: '2021级',
          class: '计科2101',
          email: 'zhangsan@example.com',
          phone: '13800138001',
          grades: { assignment1: 95 },
          totalScore: 95,
          averageScore: 95,
          rank: 0,
          isModified: false,
          hasErrors: false
        },
        {
          id: 2,
          studentId: '2021002',
          studentName: '李四',
          gender: '女',
          major: '软件工程',
          grade: '2021级',
          class: '软工2101',
          email: 'lisi@example.com',
          phone: '13800138002',
          grades: { assignment1: 85 },
          totalScore: 85,
          averageScore: 85,
          rank: 0,
          isModified: false,
          hasErrors: false
        }
      ]

      // Trigger rank calculation
      gradeStore.state.rows[0].totalScore = 95
      gradeStore.state.rows[1].totalScore = 85

      // Ranks should be calculated automatically when scores change
      expect(gradeStore.state.rows[0].rank).toBe(1) // Highest score
      expect(gradeStore.state.rows[1].rank).toBe(2)
    })

    it('limits history size to prevent memory issues', () => {
      // Add more than 100 history entries
      for (let i = 0; i < 150; i++) {
        gradeStore.actions.updateCell(1, 'assignment1', 80 + i)
      }

      expect(gradeStore.state.history.length).toBeLessThanOrEqual(100)
      expect(gradeStore.state.historyIndex).toBeLessThan(100)
    })
  })
})