<template>
  <div
    ref="containerRef"
    class="virtual-table"
    :style="{ height: `${height}px` }"
    @scroll="handleScroll"
    @wheel="handleWheel"
  >
    <!-- Header -->
    <div class="virtual-table-header" :style="{ width: `${totalWidth}px` }">
      <div
        v-for="column in columns"
        :key="column.id"
        class="virtual-table-header-cell"
        :style="{ width: `${column.width}px` }"
        @click="handleHeaderClick(column)"
      >
        <slot name="header" :column="column">
          {{ column.title }}
        </slot>
      </div>
    </div>

    <!-- Virtual Scrolling Content -->
    <div
      class="virtual-table-body"
      :style="{ height: `${totalHeight}px` }"
    >
      <!-- Visible Items -->
      <div
        class="virtual-table-rows"
        :style="{ transform: `translateY(${offsetY}px)` }"
      >
        <div
          v-for="(item, index) in visibleItems"
          :key="getRowKey(item, startIndex + index)"
          class="virtual-table-row"
          :class="getRowClass(item, startIndex + index)"
          :style="{ height: `${itemHeight}px` }"
          @click="handleRowClick(item, startIndex + index, $event)"
          @dblclick="handleRowDoubleClick(item, startIndex + index, $event)"
          @contextmenu="handleRowContextMenu(item, startIndex + index, $event)"
        >
          <div
            v-for="column in columns"
            :key="column.id"
            class="virtual-table-cell"
            :class="getCellClass(item, column, startIndex + index)"
            :style="{ width: `${column.width}px` }"
            @click="handleCellClick(item, column, startIndex + index, $event)"
            @dblclick="handleCellDoubleClick(item, column, startIndex + index, $event)"
          >
            <slot
              name="cell"
              :item="item"
              :column="column"
              :value="getCellValue(item, column)"
              :row-index="startIndex + index"
            >
              {{ formatCellValue(getCellValue(item, column), column) }}
            </slot>
          </div>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="loading" class="virtual-table-loading">
        <el-loading-spinner />
        <span>加载中...</span>
      </div>

      <!-- Empty state -->
      <div v-if="!loading && items.length === 0" class="virtual-table-empty">
        <slot name="empty">
          <el-empty description="暂无数据" />
        </slot>
      </div>
    </div>

    <!-- Selection Rectangle -->
    <div
      v-if="selectionRect.visible"
      class="selection-rectangle"
      :style="selectionRect.style"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useVirtualScroll } from '@/composables/useVirtualScroll'
import type { GradeColumn, StudentGradeRow, GradeSelection } from '@/types/grade'

// Props
interface Props {
  items: any[]
  columns: VirtualColumn[]
  height: number
  itemHeight?: number
  loading?: boolean
  rowKey?: string | ((item: any) => string | number)
  selectable?: boolean
  striped?: boolean
  border?: boolean
  hover?: boolean
}

interface VirtualColumn {
  id: string
  title: string
  width: number
  minWidth?: number
  resizable?: boolean
  sortable?: boolean
  fixed?: 'left' | 'right'
  align?: 'left' | 'center' | 'right'
  formatter?: (value: any) => string
}

const props = withDefaults(defineProps<Props>(), {
  itemHeight: 40,
  loading: false,
  rowKey: 'id',
  selectable: true,
  striped: true,
  border: true,
  hover: true
})

// Emits
interface Emits {
  (e: 'row-click', item: any, index: number, event: MouseEvent): void
  (e: 'row-dblclick', item: any, index: number, event: MouseEvent): void
  (e: 'cell-click', item: any, column: VirtualColumn, rowIndex: number, event: MouseEvent): void
  (e: 'cell-dblclick', item: any, column: VirtualColumn, rowIndex: number, event: MouseEvent): void
  (e: 'selection-change', selection: GradeSelection[]): void
  (e: 'header-click', column: VirtualColumn): void
  (e: 'scroll', scrollTop: number): void
}

const emit = defineEmits<Emits>()

// Refs
const containerRef = ref<HTMLElement>()
const selectionRect = ref({
  visible: false,
  style: {} as Record<string, string>
})

// Virtual scrolling
const {
  visibleItems,
  totalHeight,
  offsetY,
  startIndex,
  handleScroll: virtualHandleScroll
} = useVirtualScroll(props.items, {
  itemHeight: props.itemHeight,
  containerHeight: props.height - 40, // Subtract header height
  enabled: props.items.length > 100
})

// Computed
const totalWidth = computed(() => {
  return props.columns.reduce((sum, column) => sum + column.width, 0)
})

// Methods
const getRowKey = (item: any, index: number): string | number => {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(item)
  }
  return item[props.rowKey] || index
}

const getRowClass = (item: any, index: number): string => {
  const classes = ['virtual-table-row']

  if (props.striped && index % 2 === 1) {
    classes.push('striped')
  }

  if (props.hover) {
    classes.push('hoverable')
  }

  if (item.isModified) {
    classes.push('modified')
  }

  if (item.hasErrors) {
    classes.push('has-errors')
  }

  return classes.join(' ')
}

const getCellClass = (item: any, column: VirtualColumn, rowIndex: number): string => {
  const classes = ['virtual-table-cell']

  if (column.align) {
    classes.push(`align-${column.align}`)
  }

  if (props.border) {
    classes.push('bordered')
  }

  return classes.join(' ')
}

const getCellValue = (item: any, column: VirtualColumn): any => {
  if (column.id.startsWith('grades.')) {
    const gradeKey = column.id.replace('grades.', '')
    return item.grades?.[gradeKey]
  }
  return item[column.id]
}

const formatCellValue = (value: any, column: VirtualColumn): string => {
  if (value === null || value === undefined) {
    return '-'
  }

  if (column.formatter) {
    return column.formatter(value)
  }

  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toString() : value.toFixed(1)
  }

  return String(value)
}

const handleWheel = (event: WheelEvent) => {
  // Prevent horizontal scrolling if needed
  if (event.deltaX !== 0 && containerRef.value) {
    const maxScrollLeft = containerRef.value.scrollWidth - containerRef.value.clientWidth
    const currentScrollLeft = containerRef.value.scrollLeft

    if ((event.deltaX > 0 && currentScrollLeft >= maxScrollLeft) ||
        (event.deltaX < 0 && currentScrollLeft <= 0)) {
      event.preventDefault()
    }
  }
}

const handleScroll = () => {
  virtualHandleScroll()
  emit('scroll', containerRef.value?.scrollTop || 0)
}

const handleHeaderClick = (column: VirtualColumn) => {
  emit('header-click', column)
}

const handleRowClick = (item: any, index: number, event: MouseEvent) => {
  emit('row-click', item, index, event)
}

const handleRowDoubleClick = (item: any, index: number, event: MouseEvent) => {
  emit('row-dblclick', item, index, event)
}

const handleRowContextMenu = (item: any, index: number, event: MouseEvent) => {
  event.preventDefault()
  // Context menu logic handled by parent
}

const handleCellClick = (item: any, column: VirtualColumn, rowIndex: number, event: MouseEvent) => {
  event.stopPropagation()
  emit('cell-click', item, column, rowIndex, event)
}

const handleCellDoubleClick = (item: any, column: VirtualColumn, rowIndex: number, event: MouseEvent) => {
  event.stopPropagation()
  emit('cell-dblclick', item, column, rowIndex, event)
}

// Public methods
const scrollTo = (index: number) => {
  if (containerRef.value) {
    const scrollTop = index * props.itemHeight
    containerRef.value.scrollTop = scrollTop
  }
}

const scrollToTop = () => {
  scrollTo(0)
}

const scrollToBottom = () => {
  scrollTo(props.items.length - 1)
}

// Expose methods
defineExpose({
  scrollTo,
  scrollToTop,
  scrollToBottom
})

// Watch for height changes
watch(() => props.height, () => {
  // Trigger recalculation
  nextTick(() => {
    handleScroll()
  })
})
</script>

<style scoped lang="scss">
.virtual-table {
  position: relative;
  overflow: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;

  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;

    &:hover {
      background: #a8a8a8;
    }
  }
}

.virtual-table-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
  color: #303133;
}

.virtual-table-header-cell {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-right: 1px solid #e4e7ed;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;

  &:last-child {
    border-right: none;
  }

  &:hover {
    background: #f0f2f5;
  }
}

.virtual-table-body {
  position: relative;
}

.virtual-table-rows {
  position: relative;
}

.virtual-table-row {
  display: flex;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.2s;

  &.striped {
    background: #fafafa;
  }

  &.hoverable:hover {
    background: #f5f7fa;
  }

  &.modified {
    background: #fffbe6;
  }

  &.has-errors {
    background: #fff2f0;
  }
}

.virtual-table-cell {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-right: 1px solid #f0f0f0;
  font-size: 14px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  &:last-child {
    border-right: none;
  }

  &.align-left {
    justify-content: flex-start;
  }

  &.align-center {
    justify-content: center;
  }

  &.align-right {
    justify-content: flex-end;
  }

  &.bordered {
    border-right: 1px solid #e4e7ed;
  }
}

.virtual-table-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #909399;
}

.virtual-table-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  text-align: center;
}

.selection-rectangle {
  position: absolute;
  border: 2px solid #409eff;
  background: rgba(64, 158, 255, 0.1);
  pointer-events: none;
  z-index: 5;
}

// Performance optimizations
.virtual-table-row,
.virtual-table-cell {
  will-change: transform;
}

// Reduce motion support
@media (prefers-reduced-motion: reduce) {
  .virtual-table-row,
  .virtual-table-cell,
  .virtual-table-header-cell {
    transition: none;
  }
}

// High contrast mode support
@media (prefers-contrast: high) {
  .virtual-table {
    border-width: 2px;
  }

  .virtual-table-header {
    border-bottom-width: 2px;
  }

  .virtual-table-row {
    border-bottom-width: 2px;
  }

  .virtual-table-cell {
    border-right-width: 2px;
  }
}

// Mobile responsive
@media (max-width: 768px) {
  .virtual-table-header-cell,
  .virtual-table-cell {
    padding: 8px 12px;
    font-size: 13px;
  }

  .virtual-table-header-cell {
    padding: 10px 12px;
  }
}
</style>