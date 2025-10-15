import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import type { GradeCell, GradeSelection } from '@/types/grade'

interface KeyboardNavigationOptions {
  enabled?: boolean
  wrapNavigation?: boolean
  editOnTyping?: boolean
  confirmOnEnter?: boolean
  moveDownOnEnter?: boolean
}

interface KeyboardNavigationResult {
  currentCell: GradeCell | null
  selectedCells: GradeSelection[]
  handleKeyDown: (event: KeyboardEvent) => void
  navigateTo: (rowId: number, columnId: string, extend?: boolean) => void
  startEdit: () => void
  finishEdit: () => void
  cancelEdit: () => void
  selectAll: () => void
  clearSelection: () => void
  setEditingValue: (value: string) => void
}

export function useKeyboardNavigation(
  options: KeyboardNavigationOptions = {}
): KeyboardNavigationResult {
  const {
    enabled = true,
    wrapNavigation = true,
    editOnTyping = true,
    confirmOnEnter = true,
    moveDownOnEnter = true
  } = options

  // State
  const currentCell = ref<GradeCell | null>(null)
  const selectedCells = ref<GradeSelection[]>([])
  const isEditing = ref(false)
  const editingValue = ref('')

  // Computed
  const hasSelection = computed(() => selectedCells.value.length > 0)
  const canEdit = computed(() => currentCell.value !== null && !isEditing.value)
  const editingText = computed(() => editingValue.value)

  // Keyboard shortcuts registry
  const shortcuts = new Map<string, (event: KeyboardEvent) => boolean>()

  // Register default shortcuts
  const registerDefaultShortcuts = () => {
    // Navigation shortcuts
    shortcuts.set('ArrowUp', (event) => {
      if (isEditing.value) return false
      navigate('up', event.shiftKey)
      return true
    })

    shortcuts.set('ArrowDown', (event) => {
      if (isEditing.value) return false
      navigate('down', event.shiftKey)
      return true
    })

    shortcuts.set('ArrowLeft', (event) => {
      if (isEditing.value) return false
      navigate('left', event.shiftKey)
      return true
    })

    shortcuts.set('ArrowRight', (event) => {
      if (isEditing.value) return false
      navigate('right', event.shiftKey)
      return true
    })

    shortcuts.set('Tab', (event) => {
      event.preventDefault()
      navigate(event.shiftKey ? 'previous' : 'next')
      return true
    })

    shortcuts.set('Enter', (event) => {
      if (isEditing.value) {
        if (confirmOnEnter) {
          finishEdit()
          if (moveDownOnEnter) {
            nextTick(() => {
              navigate('down')
            })
          }
        }
        return true
      } else {
        navigate('down', event.shiftKey)
        return true
      }
    })

    shortcuts.set('Escape', () => {
      if (isEditing.value) {
        cancelEdit()
        return true
      } else {
        clearSelection()
        return true
      }
    })

    // Editing shortcuts
    shortcuts.set('F2', () => {
      if (canEdit.value) {
        startEdit()
        return true
      }
      return false
    })

    shortcuts.set('Delete', (event) => {
      if (!isEditing.value && !event.ctrlKey && !event.altKey) {
        // Clear selected cells
        clearSelectedCells()
        return true
      }
      return false
    })

    shortcuts.set('Backspace', (event) => {
      if (!isEditing.value && !event.ctrlKey && !event.altKey) {
        // Clear selected cells
        clearSelectedCells()
        return true
      }
      return false
    })

    // Selection shortcuts
    shortcuts.set('a', (event) => {
      if (event.ctrlKey && !event.altKey && !event.shiftKey) {
        selectAll()
        return true
      }
      return false
    })

    shortcuts.set(' ', (event) => {
      if (!isEditing.value && currentCell.value) {
        // Space to start editing or toggle checkbox
        startEdit()
        return true
      }
      return false
    })

    // Number keys for quick editing
    for (let i = 0; i <= 9; i++) {
      shortcuts.set(i.toString(), (event) => {
        if (editOnTyping && canEdit.value && !event.ctrlKey && !event.altKey && !event.shiftKey) {
          startEdit()
          setEditingValue(i.toString())
          return true
        }
        return false
      })

      shortcuts.set('Numpad' + i, (event) => {
        if (editOnTyping && canEdit.value && !event.ctrlKey && !event.altKey && !event.shiftKey) {
          startEdit()
          setEditingValue(i.toString())
          return true
        }
        return false
      })
    }

    // Decimal point
    shortcuts.set('.', (event) => {
      if (editOnTyping && canEdit.value && !event.ctrlKey && !event.altKey && !event.shiftKey) {
        startEdit()
        setEditingValue('0.')
        return true
      }
      return false
    })

    shortcuts.set('NumpadDecimal', (event) => {
      if (editOnTyping && canEdit.value && !event.ctrlKey && !event.altKey && !event.shiftKey) {
        startEdit()
        setEditingValue('0.')
        return true
      }
      return false
    })
  }

  // Navigation methods
  const navigate = (direction: 'up' | 'down' | 'left' | 'right' | 'next' | 'previous', extend = false) => {
    if (!currentCell.value) return

    const { rowId, columnId } = currentCell.value
    const newPosition = calculateNewPosition(rowId, columnId, direction)

    if (newPosition) {
      navigateTo(newPosition.rowId, newPosition.columnId, extend)
    }
  }

  const calculateNewPosition = (
    rowId: number,
    columnId: string,
    direction: 'up' | 'down' | 'left' | 'right' | 'next' | 'previous'
  ): { rowId: number; columnId: string } | null => {
    // This would be implemented based on the grid structure
    // For now, return null to indicate no movement
    return null
  }

  // Public methods
  const navigateTo = (rowId: number, columnId: string, extend = false) => {
    currentCell.value = {
      rowId,
      columnId,
      value: null,
      originalValue: null,
      isEditing: false,
      isValid: true,
      lastModified: new Date().toISOString()
    }

    if (!extend) {
      selectedCells.value = [{
        startRow: rowId,
        endRow: rowId,
        startColumn: columnId,
        endColumn: columnId,
        type: 'cell'
      }]
    }
  }

  const startEdit = () => {
    if (!currentCell.value) return

    isEditing.value = true
    editingValue.value = currentCell.value.value?.toString() || ''
    currentCell.value.isEditing = true
  }

  const finishEdit = () => {
    if (!isEditing.value || !currentCell.value) return

    const newValue = parseEditingValue(editingValue.value)
    currentCell.value.value = newValue
    currentCell.value.isEditing = false
    currentCell.value.lastModified = new Date().toISOString()
    isEditing.value = false
    editingValue.value = ''

    // Emit change event
    window.dispatchEvent(new CustomEvent('cell-change', {
      detail: {
        rowId: currentCell.value.rowId,
        columnId: currentCell.value.columnId,
        value: newValue
      }
    }))
  }

  const cancelEdit = () => {
    if (!currentCell.value) return

    currentCell.value.isEditing = false
    isEditing.value = false
    editingValue.value = ''
  }

  const selectAll = () => {
    if (!currentCell.value) return

    // Select entire grid
    selectedCells.value = [{
      startRow: 0,
      endRow: Number.MAX_SAFE_INTEGER,
      startColumn: '',
      endColumn: '',
      type: 'range'
    }]
  }

  const clearSelection = () => {
    selectedCells.value = []
    if (!isEditing.value) {
      currentCell.value = null
    }
  }

  const clearSelectedCells = () => {
    // Emit clear event for selected cells
    window.dispatchEvent(new CustomEvent('cells-clear', {
      detail: {
        cells: selectedCells.value
      }
    }))
  }

  const setEditingValue = (value: string) => {
    editingValue.value = value
  }

  const parseEditingValue = (value: string): number | null => {
    if (!value.trim()) return null

    const parsed = parseFloat(value)
    return isNaN(parsed) ? null : parsed
  }

  // Event handlers
  const handleKeyDown = (event: KeyboardEvent) => {
    if (!enabled) return

    const key = getKeyString(event)
    const handler = shortcuts.get(key)

    if (handler) {
      const handled = handler(event)
      if (handled) {
        event.preventDefault()
        event.stopPropagation()
      }
    }
  }

  const getKeyString = (event: KeyboardEvent): string => {
    const parts = []

    if (event.ctrlKey) parts.push('ctrl')
    if (event.altKey) parts.push('alt')
    if (event.shiftKey) parts.push('shift')

    let key = event.key
    if (key.startsWith('Numpad')) {
      key = key
    } else if (key === ' ') {
      key = 'space'
    }

    parts.push(key.toLowerCase())

    return parts.join('+')
  }

  // Custom shortcut registration
  const registerShortcut = (key: string, handler: (event: KeyboardEvent) => boolean) => {
    shortcuts.set(key, handler)
  }

  const unregisterShortcut = (key: string) => {
    shortcuts.delete(key)
  }

  // Global keyboard event listener
  const globalKeyHandler = (event: KeyboardEvent) => {
    // Only handle events when the focus is within the spreadsheet
    const target = event.target as HTMLElement
    if (target.closest('.grade-spreadsheet, .virtual-table')) {
      handleKeyDown(event)
    }
  }

  // Lifecycle
  onMounted(() => {
    registerDefaultShortcuts()
    document.addEventListener('keydown', globalKeyHandler)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', globalKeyHandler)
    shortcuts.clear()
  })

  return {
    currentCell,
    selectedCells,
    handleKeyDown,
    navigateTo,
    startEdit,
    finishEdit,
    cancelEdit,
    selectAll,
    clearSelection,
    setEditingValue
  }
}

// Excel-like navigation patterns
export class ExcelNavigation {
  private wrapAround: boolean
  private moveDirectionAfterEnter: 'down' | 'right' | 'none'

  constructor(options: {
    wrapAround?: boolean
    moveDirectionAfterEnter?: 'down' | 'right' | 'none'
  } = {}) {
    this.wrapAround = options.wrapAround ?? true
    this.moveDirectionAfterEnter = options.moveDirectionAfterEnter ?? 'down'
  }

  getNextPosition(
    currentRow: number,
    currentCol: number,
    direction: 'up' | 'down' | 'left' | 'right',
    totalRows: number,
    totalCols: number
  ): { row: number; col: number } | null {
    let newRow = currentRow
    let newCol = currentCol

    switch (direction) {
      case 'up':
        newRow = currentRow - 1
        break
      case 'down':
        newRow = currentRow + 1
        break
      case 'left':
        newCol = currentCol - 1
        break
      case 'right':
        newCol = currentCol + 1
        break
    }

    // Wrap around if enabled
    if (this.wrapAround) {
      if (newRow < 0) newRow = totalRows - 1
      if (newRow >= totalRows) newRow = 0
      if (newCol < 0) newCol = totalCols - 1
      if (newCol >= totalCols) newCol = 0
    } else {
      // Don't wrap around, just clamp to bounds
      newRow = Math.max(0, Math.min(totalRows - 1, newRow))
      newCol = Math.max(0, Math.min(totalCols - 1, newCol))
    }

    // Check if we're still within bounds
    if (newRow >= 0 && newRow < totalRows && newCol >= 0 && newCol < totalCols) {
      return { row: newRow, col: newCol }
    }

    return null
  }

  getEnterNextPosition(
    currentRow: number,
    currentCol: number,
    totalRows: number,
    totalCols: number
  ): { row: number; col: number } | null {
    switch (this.moveDirectionAfterEnter) {
      case 'down':
        return this.getNextPosition(currentRow, currentCol, 'down', totalRows, totalCols)
      case 'right':
        return this.getNextPosition(currentRow, currentCol, 'right', totalRows, totalCols)
      case 'none':
        return null
      default:
        return null
    }
  }

  getTabNextPosition(
    currentRow: number,
    currentCol: number,
    forward: boolean,
    totalRows: number,
    totalCols: number
  ): { row: number; col: number } | null {
    if (forward) {
      // Move to next column, or next row first column if at end
      if (currentCol < totalCols - 1) {
        return { row: currentRow, col: currentCol + 1 }
      } else if (currentRow < totalRows - 1) {
        return { row: currentRow + 1, col: 0 }
      } else if (this.wrapAround) {
        return { row: 0, col: 0 }
      }
    } else {
      // Move to previous column, or previous row last column if at start
      if (currentCol > 0) {
        return { row: currentRow, col: currentCol - 1 }
      } else if (currentRow > 0) {
        return { row: currentRow - 1, col: totalCols - 1 }
      } else if (this.wrapAround) {
        return { row: totalRows - 1, col: totalCols - 1 }
      }
    }

    return null
  }
}

// Selection management for ranges
export class SelectionManager {
  private selections: GradeSelection[] = []
  private anchorCell: { rowId: number; columnId: string } | null = null

  selectCell(rowId: number, columnId: string, extend = false): void {
    if (!extend) {
      this.selections = [{
        startRow: rowId,
        endRow: rowId,
        startColumn: columnId,
        endColumn: columnId,
        type: 'cell'
      }]
      this.anchorCell = { rowId, columnId }
    } else if (this.anchorCell) {
      // Extend selection to include the new cell
      this.selections = [{
        startRow: Math.min(this.anchorCell.rowId, rowId),
        endRow: Math.max(this.anchorCell.rowId, rowId),
        startColumn: this.anchorCell.columnId,
        endColumn: columnId,
        type: 'range'
      }]
    }
  }

  selectRow(rowId: number, extend = false): void {
    if (!extend) {
      this.selections = [{
        startRow: rowId,
        endRow: rowId,
        startColumn: '',
        endColumn: '',
        type: 'row'
      }]
      this.anchorCell = { rowId, columnId: '' }
    }
  }

  selectColumn(columnId: string, extend = false): void {
    if (!extend) {
      this.selections = [{
        startRow: 0,
        endRow: Number.MAX_SAFE_INTEGER,
        startColumn: columnId,
        endColumn: columnId,
        type: 'column'
      }]
      this.anchorCell = { rowId: 0, columnId }
    }
  }

  selectAll(): void {
    this.selections = [{
      startRow: 0,
      endRow: Number.MAX_SAFE_INTEGER,
      startColumn: '',
      endColumn: '',
      type: 'range'
    }]
    this.anchorCell = null
  }

  clearSelection(): void {
    this.selections = []
    this.anchorCell = null
  }

  getSelections(): GradeSelection[] {
    return [...this.selections]
  }

  hasSelection(): boolean {
    return this.selections.length > 0
  }

  isCellSelected(rowId: number, columnId: string): boolean {
    return this.selections.some(selection => {
      const isRowInRange = rowId >= selection.startRow && rowId <= selection.endRow
      const isColInRange = selection.type === 'row' ||
        (columnId >= selection.startColumn && columnId <= selection.endColumn)
      return isRowInRange && isColInRange
    })
  }
}