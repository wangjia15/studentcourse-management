import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElTable, ElButton, ElInputNumber } from 'element-plus'
import GradeSpreadsheet from '../GradeSpreadsheet.vue'
import { useGradeStore } from '@/stores/grade'
import type { GradeColumn, StudentGradeRow } from '@/types/grade'

// Mock the store
vi.mock('@/stores/grade')

describe('GradeSpreadsheet', () => {
  let wrapper: any
  let mockStore: any

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
    },
    {
      id: 'midterm',
      title: '期中考试',
      category: { id: 'exam', name: '考试', weight: 30 },
      maxScore: 100,
      weight: 30,
      isRequired: true,
      isVisible: true,
      order: 2
    }
  ]

  const mockRows: StudentGradeRow[] = [
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
      grades: {
        assignment1: 85,
        midterm: 78
      },
      totalScore: 83.4,
      averageScore: 81.5,
      rank: 1,
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
      grades: {
        assignment1: 92,
        midterm: 88
      },
      totalScore: 90.4,
      averageScore: 90.0,
      rank: 2,
      isModified: false,
      hasErrors: false
    }
  ]

  beforeEach(() => {
    mockStore = {
      state: {
        loading: false,
        saving: false,
        error: null,
        columns: mockColumns,
        rows: mockRows,
        courseInfo: {
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
        },
        selectedCells: [],
        currentCell: null,
        editingCell: null,
        validationErrors: [],
        history: [],
        historyIndex: -1,
        visibleRange: {
          startRow: 0,
          endRow: 100,
          startColumn: 0,
          endColumn: 10
        },
        config: {
          virtualScrolling: {
            enabled: true,
            itemHeight: 40,
            bufferSize: 10,
            threshold: 100
          },
          autoSave: {
            enabled: true,
            interval: 30000,
            debounce: 1000
          },
          validation: {
            enabled: true,
            realTime: true,
            showError: true
          },
          ui: {
            showRowNumbers: true,
            showColumnHeaders: true,
            alternatingRowColors: true,
            enableSelection: true,
            enableKeyboardNavigation: true
          },
          performance: {
            maxRows: 5000,
            maxColumns: 50,
            lazyLoad: true
          }
        }
      },
      getters: {
        totalRows: 2,
        totalColumns: 2,
        modifiedRows: [],
        hasUnsavedChanges: false,
        selectedData: {},
        selectedRows: [],
        selectedColumns: [],
        hasErrors: false,
        errorCount: 0,
        visibleRows: mockRows,
        visibleColumns: mockColumns,
        canUndo: false,
        canRedo: false,
        canSave: false
      },
      actions: {
        loadGrades: vi.fn(),
        saveGrades: vi.fn().mockResolvedValue(undefined),
        updateCell: vi.fn(),
        batchUpdate: vi.fn(),
        selectCell: vi.fn(),
        selectRow: vi.fn(),
        selectColumn: vi.fn(),
        selectAll: vi.fn(),
        clearSelection: vi.fn(),
        startEdit: vi.fn(),
        finishEdit: vi.fn(),
        cancelEdit: vi.fn(),
        copy: vi.fn(),
        paste: vi.fn(),
        fill: vi.fn(),
        clear: vi.fn(),
        addPoints: vi.fn(),
        multiplyBy: vi.fn(),
        setPercentage: vi.fn(),
        undo: vi.fn(),
        redo: vi.fn(),
        clearHistory: vi.fn(),
        validateAll: vi.fn(),
        validateCell: vi.fn(),
        updateConfig: vi.fn(),
        updateVisibleRange: vi.fn()
      }
    }

    vi.mocked(useGradeStore).mockReturnValue(mockStore)

    wrapper = mount(GradeSpreadsheet, {
      props: {
        courseId: 1,
        height: 600
      },
      global: {
        components: {
          ElTable,
          ElButton,
          ElInputNumber
        }
      }
    })
  })

  it('renders correctly with course data', () => {
    expect(wrapper.find('.grade-spreadsheet').exists()).toBe(true)
    expect(wrapper.find('.spreadsheet-toolbar').exists()).toBe(true)
    expect(wrapper.find('.spreadsheet-container').exists()).toBe(true)
    expect(wrapper.find('.spreadsheet-status').exists()).toBe(true)
  })

  it('displays loading state when loading', async () => {
    mockStore.state.loading = true
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.el-loading-mask').exists()).toBe(true)
  })

  it('displays error message when there is an error', async () => {
    mockStore.state.error = '加载失败'
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-alert').exists()).toBe(true)
    expect(wrapper.text()).toContain('加载失败')
  })

  it('displays validation errors when they exist', async () => {
    mockStore.state.validationErrors = [
      {
        rowId: 1,
        columnId: 'assignment1',
        message: '分数必须在0-100之间',
        type: 'range'
      }
    ]
    mockStore.getters.hasErrors = true
    mockStore.getters.errorCount = 1

    await wrapper.vm.$nextTick()

    expect(wrapper.find('.validation-errors').exists()).toBe(true)
    expect(wrapper.text()).toContain('发现 1 个验证错误')
  })

  it('enables/disables toolbar buttons based on state', async () => {
    // Initially disabled
    const undoButton = wrapper.find('[data-testid="undo-button"]')
    const redoButton = wrapper.find('[data-testid="redo-button"]')
    const saveButton = wrapper.find('[data-testid="save-button"]')

    expect(undoButton.attributes('disabled')).toBeDefined()
    expect(redoButton.attributes('disabled')).toBeDefined()
    expect(saveButton.attributes('disabled')).toBeDefined()

    // Enable save when there are changes
    mockStore.getters.canSave = true
    await wrapper.vm.$nextTick()

    expect(saveButton.attributes('disabled')).toBeUndefined()
  })

  it('handles cell clicks correctly', async () => {
    const table = wrapper.findComponent(ElTable)

    // Mock cell click
    await table.vm.$emit('cell-click', mockRows[0], { property: 'grades.assignment1' })

    expect(mockStore.actions.selectCell).toHaveBeenCalledWith(1, 'assignment1')
  })

  it('handles cell double clicks for editing', async () => {
    const table = wrapper.findComponent(ElTable)

    // Mock cell double click
    await table.vm.$emit('cell-dblclick', mockRows[0], { property: 'grades.assignment1' })

    expect(mockStore.actions.startEdit).toHaveBeenCalledWith(1, 'assignment1')
  })

  it('handles keyboard shortcuts', async () => {
    const container = wrapper.find('.spreadsheet-container')

    // Test Ctrl+A for select all
    await container.trigger('keydown', {
      key: 'a',
      ctrlKey: true
    })

    expect(mockStore.actions.selectAll).toHaveBeenCalled()

    // Test Ctrl+S for save
    await container.trigger('keydown', {
      key: 's',
      ctrlKey: true
    })

    // Save should be called through the saveGrades method
    expect(mockStore.actions.saveGrades).toHaveBeenCalled()
  })

  it('handles bulk operations', async () => {
    // Mock selection
    mockStore.state.selectedCells = [{
      startRow: 0,
      endRow: 1,
      startColumn: 'assignment1',
      endColumn: 'assignment1',
      type: 'range'
    }]

    await wrapper.vm.$nextTick()

    // Find and click bulk operation dropdown
    const bulkDropdown = wrapper.find('[data-testid="bulk-operation-dropdown"]')
    expect(bulkDropdown.exists()).toBe(true)

    // Test add points operation
    await wrapper.vm.handleBulkOperation('add-points')
    expect(wrapper.vm.bulkOperationDialog.type).toBe('add-points')
    expect(wrapper.vm.bulkOperationDialog.visible).toBe(true)
  })

  it('calculates visible data correctly', () => {
    expect(wrapper.vm.visibleData).toEqual(mockRows)
  })

  it('formats scores correctly', () => {
    expect(wrapper.vm.formatScore(85.5)).toBe('85.5')
    expect(wrapper.vm.formatScore(85)).toBe('85')
    expect(wrapper.vm.formatScore(null)).toBe('-')
    expect(wrapper.vm.formatScore(undefined)).toBe('-')
  })

  it('gets cell class names correctly', () => {
    const row = mockRows[0]
    const column = { property: 'grades.assignment1' }

    // Test selected cell
    mockStore.state.selectedCells = [{
      startRow: 0,
      endRow: 0,
      startColumn: 'assignment1',
      endColumn: 'assignment1',
      type: 'cell'
    }]

    let className = wrapper.vm.getCellClassName({ row, column })
    expect(className).toContain('cell-selected')

    // Test error cell
    mockStore.state.validationErrors = [{
      rowId: 1,
      columnId: 'assignment1',
      message: '错误',
      type: 'range'
    }]

    className = wrapper.vm.getCellClassName({ row, column })
    expect(className).toContain('cell-error')

    // Test editing cell
    mockStore.state.editingCell = {
      rowId: 1,
      columnId: 'assignment1',
      value: 85,
      originalValue: 80,
      isEditing: true,
      isValid: true,
      lastModified: new Date().toISOString()
    }

    className = wrapper.vm.getCellClassName({ row, column })
    expect(className).toContain('cell-editing')
  })

  it('navigates cells correctly', () => {
    mockStore.state.currentCell = {
      rowId: 1,
      columnId: 'assignment1',
      value: 85,
      originalValue: 85,
      isEditing: false,
      isValid: true,
      lastModified: new Date().toISOString()
    }

    // Test navigation down
    wrapper.vm.navigateCell('down')
    expect(mockStore.actions.selectCell).toHaveBeenCalledWith(2, 'assignment1')

    // Test navigation right
    wrapper.vm.navigateCell('right')
    expect(mockStore.actions.selectCell).toHaveBeenCalledWith(1, 'midterm')
  })

  it('validates cells correctly', () => {
    const column = mockColumns[0]

    // Test valid score
    expect(wrapper.vm.validateCell(1, 'assignment1', 85)).toBeNull()

    // Test invalid score (too high)
    expect(wrapper.vm.validateCell(1, 'assignment1', 150)).toBe('分数必须在 0 到 100 之间')

    // Test invalid score (negative)
    expect(wrapper.vm.validateCell(1, 'assignment1', -5)).toBe('分数必须在 0 到 100 之间')

    // Test empty score for required column
    expect(wrapper.vm.validateCell(1, 'assignment1', null)).toBe('此列为必填项')
  })

  it('shows correct status information', () => {
    const status = wrapper.find('.spreadsheet-status')
    expect(status.exists()).toBe(true)
    expect(status.text()).toContain('共 2 行，2 列')
  })

  it('handles responsive design correctly', async () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    })

    window.dispatchEvent(new Event('resize'))
    await wrapper.vm.$nextTick()

    // Check if mobile styles are applied
    const toolbar = wrapper.find('.spreadsheet-toolbar')
    expect(toolbar.exists()).toBe(true)
  })

  it('cleans up properly on unmount', () => {
    const wrapper = mount(GradeSpreadsheet, {
      props: { courseId: 1 }
    })

    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout')

    wrapper.unmount()

    // Verify cleanup (if there are any timers or event listeners)
    expect(clearTimeoutSpy).toHaveBeenCalled()
  })
})