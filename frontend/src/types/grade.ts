// Grade-related TypeScript interfaces and types

export interface Grade {
  id: number
  studentId: number
  courseId: number
  assignmentId?: number
  score: number
  maxScore: number
  weight: number
  category: GradeCategory
  semester: string
  academicYear: string
  isFinal: boolean
  createdAt: string
  updatedAt: string
  gradedBy?: number
  comments?: string
}

export interface StudentGradeRow {
  id: number
  studentId: string
  studentName: string
  gender: '男' | '女'
  major: string
  grade: string
  class: string
  email: string
  phone: string
  grades: Record<string, number | null>
  totalScore?: number
  averageScore?: number
  rank?: number
  isModified?: boolean
  hasErrors?: boolean
  lastModified?: string
}

export interface CourseInfo {
  id: number
  code: string
  name: string
  credit: number
  totalWeight: number
  semester: string
  academicYear: string
  teacherId: number
  teacherName: string
  isActive: boolean
}

export interface GradeColumn {
  id: string
  title: string
  category: GradeCategory
  maxScore: number
  weight: number
  isRequired: boolean
  isVisible: boolean
  order: number
  assignmentId?: number
}

export interface GradeCategory {
  id: string
  name: string
  weight: number
  color?: string
  description?: string
}

export interface GradeValidationRule {
  min: number
  max: number
  required: boolean
  allowDecimals: boolean
  decimalPlaces?: number
}

export interface GradeValidationError {
  rowId: number
  columnId: string
  message: string
  type: 'range' | 'required' | 'format' | 'duplicate'
}

export interface GradeCell {
  rowId: number
  columnId: string
  value: number | null
  originalValue: number | null
  isEditing: boolean
  isValid: boolean
  errorMessage?: string
  lastModified: string
}

export interface GradeSelection {
  startRow: number
  endRow: number
  startColumn: string
  endColumn: string
  type: 'cell' | 'row' | 'column' | 'range'
}

export interface GradeOperation {
  type: 'set' | 'add' | 'multiply' | 'clear' | 'fill'
  value: number | null
  targetRange: GradeSelection
  timestamp: string
}

export interface GradeHistoryEntry {
  id: string
  operation: GradeOperation
  previousValues: Record<string, number | null>
  newValues: Record<string, number | null>
  userId: number
  timestamp: string
  description: string
}

export interface GradeSpreadsheetConfig {
  virtualScrolling: {
    enabled: boolean
    itemHeight: number
    bufferSize: number
    threshold: number
  }
  autoSave: {
    enabled: boolean
    interval: number
    debounce: number
  }
  validation: {
    enabled: boolean
    realTime: boolean
    showError: boolean
  }
  ui: {
    showRowNumbers: boolean
    showColumnHeaders: boolean
    alternatingRowColors: boolean
    enableSelection: boolean
    enableKeyboardNavigation: boolean
  }
  performance: {
    maxRows: number
    maxColumns: number
    lazyLoad: boolean
  }
}

export interface GradeSpreadsheetState {
  // Data
  columns: GradeColumn[]
  rows: StudentGradeRow[]
  courseInfo: CourseInfo | null

  // UI State
  loading: boolean
  saving: boolean
  error: string | null

  // Selection and editing
  selectedCells: GradeSelection[]
  currentCell: GradeCell | null
  editingCell: GradeCell | null

  // Validation
  validationErrors: GradeValidationError[]

  // History
  history: GradeHistoryEntry[]
  historyIndex: number

  // Performance
  visibleRange: {
    startRow: number
    endRow: number
    startColumn: number
    endColumn: number
  }

  // Configuration
  config: GradeSpreadsheetConfig
}

export interface GradeSpreadsheetActions {
  // Data operations
  loadGrades: (courseId: number) => Promise<void>
  saveGrades: (grades: Record<string, number | null>) => Promise<void>
  updateCell: (rowId: number, columnId: string, value: number | null) => void
  batchUpdate: (updates: Record<string, number | null>) => void

  // Selection operations
  selectCell: (rowId: number, columnId: string, extend?: boolean) => void
  selectRow: (rowId: number, extend?: boolean) => void
  selectColumn: (columnId: string, extend?: boolean) => void
  selectAll: () => void
  clearSelection: () => void

  // Editing operations
  startEdit: (rowId: number, columnId: string) => void
  finishEdit: () => void
  cancelEdit: () => void

  // Batch operations
  copy: () => void
  paste: () => void
  fill: (direction: 'up' | 'down' | 'left' | 'right') => void
  clear: () => void

  // Grade operations
  addPoints: (points: number) => void
  multiplyBy: (factor: number) => void
  setPercentage: (percentage: number) => void

  // History operations
  undo: () => void
  redo: () => void
  clearHistory: () => void

  // Validation
  validateAll: () => GradeValidationError[]
  validateCell: (rowId: number, columnId: string, value: number | null) => string | null

  // Configuration
  updateConfig: (config: Partial<GradeSpreadsheetConfig>) => void

  // Performance
  updateVisibleRange: (range: GradeSpreadsheetState['visibleRange']) => void
}

export interface GradeSpreadsheetGetters {
  // Computed data
  totalRows: number
  totalColumns: number
  modifiedRows: number[]
  hasUnsavedChanges: boolean

  // Selection
  selectedData: Record<string, number | null>
  selectedRows: number[]
  selectedColumns: string[]

  // Validation
  hasErrors: boolean
  errorCount: number

  // Performance
  visibleRows: StudentGradeRow[]
  visibleColumns: GradeColumn[]

  // Status
  canUndo: boolean
  canRedo: boolean
  canSave: boolean
}

export interface GradeSpreadsheetComposable {
  state: GradeSpreadsheetState
  actions: GradeSpreadsheetActions
  getters: GradeSpreadsheetGetters
}

// Event types
export interface GradeSpreadsheetEvent {
  type: 'cell-click' | 'cell-edit' | 'cell-change' | 'selection-change' | 'save-start' | 'save-end' | 'error' | 'validation-error'
  data: any
  timestamp: string
}

export interface GradeImportData {
  courseCode: string
  studentId: string
  studentName: string
  [key: string]: string | number
}

export interface GradeExportOptions {
  format: 'excel' | 'csv' | 'pdf'
  includeHeaders: boolean
  includeStats: boolean
  filter?: {
    columns?: string[]
    rows?: number[]
  }
}

// Keyboard shortcuts
export interface KeyboardShortcut {
  key: string
  ctrlKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  action: string
  description: string
  category: 'navigation' | 'editing' | 'selection' | 'operations'
}

export const DEFAULT_GRADE_VALIDATION_RULE: GradeValidationRule = {
  min: 0,
  max: 100,
  required: false,
  allowDecimals: true,
  decimalPlaces: 2
}

export const DEFAULT_SPREADSHEET_CONFIG: GradeSpreadsheetConfig = {
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

export const DEFAULT_KEYBOARD_SHORTCUTS: KeyboardShortcut[] = [
  // Navigation
  { key: 'ArrowUp', action: 'navigate-up', description: '向上移动', category: 'navigation' },
  { key: 'ArrowDown', action: 'navigate-down', description: '向下移动', category: 'navigation' },
  { key: 'ArrowLeft', action: 'navigate-left', description: '向左移动', category: 'navigation' },
  { key: 'ArrowRight', action: 'navigate-right', description: '向右移动', category: 'navigation' },
  { key: 'Tab', action: 'navigate-next', description: '移到下一个单元格', category: 'navigation' },
  { key: 'Tab', shiftKey: true, action: 'navigate-previous', description: '移到上一个单元格', category: 'navigation' },
  { key: 'Enter', action: 'navigate-next-row', description: '确认并移到下一行', category: 'navigation' },

  // Editing
  { key: 'F2', action: 'edit-cell', description: '编辑单元格', category: 'editing' },
  { key: 'Delete', action: 'clear-cell', description: '清空单元格', category: 'editing' },
  { key: 'Escape', action: 'cancel-edit', description: '取消编辑', category: 'editing' },

  // Selection
  { key: 'a', ctrlKey: true, action: 'select-all', description: '全选', category: 'selection' },
  { key: 'c', ctrlKey: true, action: 'copy', description: '复制', category: 'selection' },
  { key: 'v', ctrlKey: true, action: 'paste', description: '粘贴', category: 'selection' },
  { key: 'x', ctrlKey: true, action: 'cut', description: '剪切', category: 'selection' },

  // Operations
  { key: 'z', ctrlKey: true, action: 'undo', description: '撤销', category: 'operations' },
  { key: 'z', ctrlKey: true, shiftKey: true, action: 'redo', description: '重做', category: 'operations' },
  { key: 's', ctrlKey: true, action: 'save', description: '保存', category: 'operations' },
]