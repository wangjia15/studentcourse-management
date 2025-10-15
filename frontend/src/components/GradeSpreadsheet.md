# GradeSpreadsheet Component

A high-performance Excel-style grade entry spreadsheet component for Chinese University Grade Management System.

## Features

### Core Functionality
- **Virtual Scrolling**: Handles 5000+ rows smoothly with >30fps performance
- **Excel-like Navigation**: Full keyboard navigation support (Tab, Enter, Arrow keys, Esc)
- **Real-time Validation**: Input validation with 0-100 score range
- **Batch Operations**: Copy/paste, bulk adjustments, and mass operations
- **Auto-save**: Automatic saving with conflict detection
- **Undo/Redo**: Full history management with 100-entry limit

### User Experience
- **Responsive Design**: Mobile-friendly interface with touch support
- **Visual Feedback**: Alternating row colors, selection highlighting, error states
- **Context Menus**: Right-click context menus for quick actions
- **Toolbar Shortcuts**: Quick access toolbar with common operations
- **Accessibility**: Full ARIA support and keyboard navigation

## Installation

The component is part of the Chinese University Grade Management System and requires the following dependencies:

```bash
npm install vue@^3.4.0 pinia@^2.1.7 element-plus@^2.11.4
```

## Usage

### Basic Usage

```vue
<template>
  <GradeSpreadsheet
    :course-id="courseId"
    :height="600"
    @save="handleSave"
    @cell-change="handleCellChange"
  />
</template>

<script setup lang="ts">
import GradeSpreadsheet from '@/components/GradeSpreadsheet.vue'

const courseId = ref(1)

const handleSave = async (data) => {
  console.log('Saving grades:', data)
}

const handleCellChange = (event) => {
  console.log('Cell changed:', event.detail)
}
</script>
```

### Advanced Usage with Custom Configuration

```vue
<template>
  <GradeSpreadsheet
    :course-id="courseId"
    :height="800"
    :config="customConfig"
    @selection-change="handleSelectionChange"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import GradeSpreadsheet from '@/components/GradeSpreadsheet.vue'
import type { GradeSpreadsheetConfig } from '@/types/grade'

const courseId = ref(1)

const customConfig: GradeSpreadsheetConfig = {
  virtualScrolling: {
    enabled: true,
    itemHeight: 45,
    bufferSize: 15,
    threshold: 200
  },
  autoSave: {
    enabled: true,
    interval: 60000,
    debounce: 2000
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
    maxRows: 10000,
    maxColumns: 100,
    lazyLoad: true
  }
}
</script>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| courseId | `number` | **Required** | The ID of the course to load grades for |
| height | `number` | `600` | Height of the spreadsheet in pixels |
| config | `GradeSpreadsheetConfig` | `DEFAULT_CONFIG` | Configuration object for customization |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| save | `data: Record<string, number \| null>` | Emitted when grades are saved |
| cell-change | `{ rowId, columnId, value }` | Emitted when a cell value changes |
| selection-change | `selection: GradeSelection[]` | Emitted when selection changes |
| validation-error | `errors: GradeValidationError[]` | Emitted when validation errors occur |

## Keyboard Shortcuts

### Navigation
- **Arrow Keys** (↑↓←→): Navigate between cells
- **Tab**: Move to next cell
- **Shift + Tab**: Move to previous cell
- **Enter**: Confirm input and move to next row
- **Home**: Move to first cell in row
- **End**: Move to last cell in row
- **Page Up**: Move up one screen
- **Page Down**: Move down one screen

### Editing
- **F2**: Enter edit mode
- **0-9**: Start editing with number
- **Enter**: Confirm edit
- **Escape**: Cancel edit
- **Delete/Backspace**: Clear cell value

### Selection
- **Ctrl + A**: Select all cells
- **Shift + Arrow Keys**: Extend selection
- **Ctrl + Space**: Select column
- **Shift + Space**: Select row

### Operations
- **Ctrl + C**: Copy selected cells
- **Ctrl + V**: Paste cells
- **Ctrl + X**: Cut selected cells
- **Ctrl + Z**: Undo
- **Ctrl + Y**: Redo
- **Ctrl + S**: Save changes

## Data Structure

### GradeRow Interface

```typescript
interface StudentGradeRow {
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
```

### GradeColumn Interface

```typescript
interface GradeColumn {
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
```

## Configuration Options

### Virtual Scrolling

```typescript
virtualScrolling: {
  enabled: boolean      // Enable virtual scrolling
  itemHeight: number    // Height of each row in pixels
  bufferSize: number   // Number of extra rows to render
  threshold: number    // Minimum rows to enable virtual scrolling
}
```

### Auto Save

```typescript
autoSave: {
  enabled: boolean     // Enable auto-save
  interval: number     // Auto-save interval in milliseconds
  debounce: number     // Debounce delay in milliseconds
}
```

### Validation

```typescript
validation: {
  enabled: boolean     // Enable validation
  realTime: boolean    // Real-time validation
  showError: boolean   // Show error messages
}
```

### UI Settings

```typescript
ui: {
  showRowNumbers: boolean           // Show row numbers
  showColumnHeaders: boolean        // Show column headers
  alternatingRowColors: boolean     // Alternating row colors
  enableSelection: boolean          // Enable cell selection
  enableKeyboardNavigation: boolean // Enable keyboard navigation
}
```

## Performance Considerations

### Virtual Scrolling
- Enabled automatically for datasets > 100 rows
- Renders only visible rows + buffer
- Maintains smooth scrolling at 30+ FPS

### Memory Management
- Automatic cleanup of unused data
- Limited history size (100 entries)
- Efficient event handling

### Optimization Tips
1. **Large Datasets**: Enable virtual scrolling for >1000 rows
2. **Frequent Updates**: Increase auto-save debounce
3. **Memory Usage**: Limit history size for complex operations
4. **Mobile Devices**: Reduce item height and buffer size

## Styling

The component uses SCSS with CSS custom properties for theming:

```scss
.grade-spreadsheet {
  --primary-color: #409eff;
  --success-color: #67c23a;
  --warning-color: #e6a23c;
  --danger-color: #f56c6c;
  --info-color: #909399;

  --border-color: #e4e7ed;
  --background-color: #f5f7fa;
  --text-color: #303133;
  --text-secondary: #606266;
}
```

## Accessibility

- Full ARIA support
- Keyboard navigation
- Screen reader compatibility
- High contrast mode support
- Reduced motion support

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Mobile Support

- Touch gestures for selection
- Responsive design for screens < 768px
- Optimized touch targets
- Virtual keyboard handling

## Troubleshooting

### Performance Issues
1. Enable virtual scrolling for large datasets
2. Increase item height for better touch interaction
3. Reduce auto-save frequency
4. Limit history size

### Validation Errors
1. Check grade range (0-100)
2. Verify required fields
3. Review column configuration
4. Check data types

### Keyboard Navigation
1. Ensure component has focus
2. Check enableKeyboardNavigation setting
3. Verify no other elements intercept events
4. Test in different browsers

## Examples

### Basic Grade Entry

```vue
<template>
  <div class="grade-management">
    <h2>成绩录入</h2>
    <GradeSpreadsheet
      :course-id="currentCourse"
      :height="500"
      @save="onSave"
    />
  </div>
</template>
```

### With Statistics Panel

```vue
<template>
  <div class="grade-layout">
    <div class="spreadsheet-section">
      <GradeSpreadsheet :course-id="courseId" />
    </div>
    <div class="statistics-section">
      <GradeStatistics :course-id="courseId" />
    </div>
  </div>
</template>
```

### Custom Validation

```vue
<script setup lang="ts">
const customValidation = (rowId: number, columnId: string, value: number | null): string | null => {
  // Custom validation logic
  if (columnId === 'final_exam' && value !== null && value < 60) {
    return '期末考试成绩不能低于60分'
  }
  return null
}

// Apply custom validation in the store
gradeStore.actions.setCustomValidator(customValidation)
</script>
```

## Contributing

When contributing to the GradeSpreadsheet component:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Test performance with large datasets
5. Verify accessibility compliance

## License

This component is part of the Chinese University Grade Management System and is subject to the project's license terms.