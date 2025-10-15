<template>
  <div
    class="grade-cell"
    :class="cellClasses"
    @click="handleClick"
    @dblclick="handleDoubleClick"
    @keydown="handleKeyDown"
  >
    <!-- Display mode -->
    <div v-if="!isEditing" class="cell-display">
      <span v-if="value !== null && value !== undefined" class="cell-value">
        {{ formatDisplayValue(value) }}
      </span>
      <span v-else class="cell-empty">-</span>
    </div>

    <!-- Edit mode -->
    <div v-else class="cell-edit">
      <el-input-number
        ref="inputRef"
        v-model="editValue"
        :min="0"
        :max="column?.maxScore || 100"
        :precision="decimalPlaces"
        :step="step"
        :controls="false"
        size="small"
        class="grade-input"
        @blur="handleBlur"
        @keydown.enter="handleEnter"
        @keydown.escape="handleEscape"
        @keydown.tab="handleTab"
      />
    </div>

    <!-- Status indicators -->
    <div v-if="hasError" class="error-indicator">
      <el-tooltip :content="errorMessage" placement="top">
        <el-icon class="error-icon"><Warning /></el-icon>
      </el-tooltip>
    </div>

    <div v-if="isModified" class="modified-indicator">
      <el-tooltip content="已修改" placement="top">
        <el-icon class="modified-icon"><Edit /></el-icon>
      </el-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import type { GradeColumn, StudentGradeRow } from '@/types/grade'

// Props
interface Props {
  row: StudentGradeRow
  column?: GradeColumn
  value: number | null
  isEditing: boolean
  isSelected: boolean
  hasError: boolean
  isModified: boolean
  errorMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  column: undefined,
  errorMessage: ''
})

// Emits
interface Emits {
  (e: 'edit'): void
  (e: 'save', value: number | null): void
  (e: 'cancel'): void
  (e: 'click', event: MouseEvent): void
  (e: 'dblclick', event: MouseEvent): void
}

const emit = defineEmits<Emits>()

// Refs
const inputRef = ref()
const editValue = ref<number | null>(null)

// Computed
const cellClasses = computed(() => ({
  'is-editing': props.isEditing,
  'is-selected': props.isSelected,
  'has-error': props.hasError,
  'is-modified': props.isModified,
  'is-empty': props.value === null || props.value === undefined
}))

const decimalPlaces = computed(() => {
  // Allow 1 decimal place for max scores that aren't whole numbers
  if (props.column?.maxScore && !Number.isInteger(props.column.maxScore)) {
    return 1
  }
  return 0
})

const step = computed(() => {
  return decimalPlaces.value > 0 ? 0.1 : 1
})

// Methods
const formatDisplayValue = (value: number): string => {
  if (decimalPlaces.value > 0) {
    return value.toFixed(decimalPlaces.value)
  }
  return Math.round(value).toString()
}

const handleClick = (event: MouseEvent) => {
  emit('click', event)
}

const handleDoubleClick = (event: MouseEvent) => {
  emit('dblclick', event)
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (props.isEditing) return

  // Start editing on F2 or any number key
  if (event.key === 'F2' || (!event.ctrlKey && !event.altKey && /^[0-9.]$/.test(event.key))) {
    event.preventDefault()
    startEdit()
    if (/^[0-9.]$/.test(event.key)) {
      // Pre-fill with the typed number
      nextTick(() => {
        if (inputRef.value) {
          editValue.value = 0
          // Simulate typing the number
          nextTick(() => {
            const inputElement = inputRef.value?.$el?.querySelector('input')
            if (inputElement) {
              inputElement.value = event.key
              editValue.value = parseFloat(event.key) || 0
            }
          })
        }
      })
    }
  }

  // Navigation
  if (!props.isEditing) {
    switch (event.key) {
      case 'Enter':
      case 'F2':
        event.preventDefault()
        startEdit()
        break
      case 'Delete':
      case 'Backspace':
        if (!event.ctrlKey && !event.altKey) {
          event.preventDefault()
          emit('save', null)
        }
        break
    }
  }
}

const startEdit = () => {
  editValue.value = props.value
  emit('edit')
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus()
      inputRef.value.select()
    }
  })
}

const handleBlur = () => {
  saveEdit()
}

const handleEnter = (event: KeyboardEvent) => {
  event.preventDefault()
  saveEdit()
  // Move to next cell (handled by parent)
}

const handleEscape = (event: KeyboardEvent) => {
  event.preventDefault()
  cancelEdit()
}

const handleTab = (event: KeyboardEvent) => {
  event.preventDefault()
  saveEdit()
  // Tab navigation (handled by parent)
}

const saveEdit = () => {
  if (validateValue(editValue.value)) {
    emit('save', editValue.value)
  } else {
    cancelEdit()
  }
}

const cancelEdit = () => {
  editValue.value = props.value
  emit('cancel')
}

const validateValue = (value: number | null): boolean => {
  if (value === null || value === undefined) return true

  // Check range
  const min = 0
  const max = props.column?.maxScore || 100

  if (value < min || value > max) {
    return false
  }

  // Check decimal places
  if (decimalPlaces.value === 0 && !Number.isInteger(value)) {
    return false
  }

  return true
}

// Watch for editing state changes
watch(() => props.isEditing, (newEditing) => {
  if (newEditing) {
    editValue.value = props.value
    nextTick(() => {
      if (inputRef.value) {
        inputRef.value.focus()
        inputRef.value.select()
      }
    })
  } else {
    editValue.value = null
  }
})

// Watch for value changes (when not editing)
watch(() => props.value, (newValue) => {
  if (!props.isEditing) {
    editValue.value = newValue
  }
})
</script>

<style scoped lang="scss">
.grade-cell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 4px 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;

  &:hover {
    background-color: #f5f7fa;
  }

  &.is-selected {
    background-color: #e6f7ff;
    border: 1px solid #1890ff;
  }

  &.is-editing {
    background-color: #f6ffed;
    border: 1px solid #52c41a;
    cursor: text;
    user-select: text;
  }

  &.has-error {
    background-color: #fff2f0;
    border: 1px solid #ff4d4f;
  }

  &.is-modified {
    background-color: #fffbe6;
  }

  &.is-empty {
    color: #c0c4cc;
  }
}

.cell-display {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-height: 24px;
}

.cell-value {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.cell-empty {
  color: #c0c4cc;
  font-style: italic;
}

.cell-edit {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.grade-input {
  width: 100%;

  :deep(.el-input__inner) {
    text-align: center;
    font-weight: 500;
    font-size: 14px;
    padding: 0 8px;
    height: 28px;
    line-height: 28px;
  }
}

.error-indicator,
.modified-indicator {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 12px;
}

.error-indicator {
  background-color: #fef0f0;
  color: #f56c6c;
}

.modified-indicator {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.error-icon,
.modified-icon {
  font-size: 12px;
}

// Focus styles
.grade-cell.is-editing {
  .grade-input {
    :deep(.el-input__inner) {
      border-color: #409eff;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
    }
  }
}

// High contrast mode support
@media (prefers-contrast: high) {
  .grade-cell {
    border: 1px solid #dcdfe6;

    &.is-selected {
      border-width: 2px;
    }

    &.has-error {
      border-color: #f56c6c;
      border-width: 2px;
    }

    &.is-editing {
      border-color: #67c23a;
      border-width: 2px;
    }
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .grade-cell {
    transition: none;
  }
}

// Mobile styles
@media (max-width: 768px) {
  .grade-cell {
    padding: 2px 4px;

    .cell-value {
      font-size: 13px;
    }

    .grade-input {
      :deep(.el-input__inner) {
        font-size: 13px;
        height: 24px;
        line-height: 24px;
      }
    }
  }

  .error-indicator,
  .modified-indicator {
    width: 14px;
    height: 14px;
    font-size: 10px;
  }
}
</style>