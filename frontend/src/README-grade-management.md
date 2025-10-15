# 中国大学成绩管理系统 - 前端组件文档

## 项目概述

本项目为中国大学成绩管理系统的前端部分，采用 Vue 3 + TypeScript + Element Plus 技术栈，提供高性能的Excel风格成绩录入和管理功能。

## 核心功能

### 📊 成绩录入表格
- **高性能虚拟滚动**: 支持5000+行数据流畅操作 (>30fps)
- **Excel风格导航**: 完整键盘导航支持 (Tab, Enter, 方向键, Esc)
- **实时数据验证**: 0-100分数范围实时验证
- **批量操作**: 复制/粘贴、批量调整、批量计算
- **自动保存**: 智能自动保存机制，冲突检测
- **撤销重做**: 完整历史记录管理 (100条记录限制)

### 🎨 用户体验
- **响应式设计**: 移动端友好界面，触摸操作支持
- **视觉反馈**: 交替行颜色、选择高亮、错误状态提示
- **右键菜单**: 快速操作上下文菜单
- **工具栏快捷**: 常用操作快速访问
- **无障碍访问**: 完整ARIA支持和键盘导航

### 📈 数据管理
- **状态管理**: Pinia状态管理，支持复杂状态操作
- **数据同步**: 后端API集成，批量更新支持
- **冲突检测**: 多用户编辑冲突检测和解决
- **网络恢复**: 网络异常自动恢复机制

## 技术架构

### 核心技术栈
- **Vue 3**: Composition API + TypeScript
- **Element Plus**: UI组件库
- **Pinia**: 状态管理
- **Vite**: 构建工具
- **SCSS**: 样式预处理

### 组件架构
```
src/
├── components/
│   ├── GradeSpreadsheet.vue      # 主表格组件
│   ├── GradeCell.vue             # 单元格组件
│   ├── VirtualTable.vue          # 虚拟滚动表格
│   ├── GradeStatistics.vue       # 统计面板
│   └── SpreadsheetSettings.vue   # 设置面板
├── stores/
│   └── grade.ts                  # 成绩数据状态管理
├── types/
│   └── grade.ts                  # TypeScript类型定义
├── composables/
│   ├── useVirtualScroll.ts       # 虚拟滚动Hook
│   └── useKeyboardNavigation.ts   # 键盘导航Hook
└── views/
    └── GradeManagementView.vue   # 成绩管理页面
```

## 快速开始

### 环境要求
- Node.js 16+
- npm 8+ 或 yarn 1.22+

### 安装依赖
```bash
npm install
```

### 开发服务器
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

## 核心组件使用指南

### GradeSpreadsheet 主表格组件

#### 基础使用
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
import { ref } from 'vue'
import GradeSpreadsheet from '@/components/GradeSpreadsheet.vue'

const courseId = ref(1)

const handleSave = async (data) => {
  console.log('保存成绩:', data)
  // 调用API保存数据
}

const handleCellChange = (event) => {
  console.log('单元格变更:', event.detail)
  // 处理单元格变更事件
}
</script>
```

#### 高级配置
```vue
<script setup lang="ts">
import type { GradeSpreadsheetConfig } from '@/types/grade'

const customConfig: GradeSpreadsheetConfig = {
  virtualScrolling: {
    enabled: true,
    itemHeight: 45,
    bufferSize: 15,
    threshold: 200
  },
  autoSave: {
    enabled: true,
    interval: 60000,    // 1分钟
    debounce: 2000      // 2秒防抖
  },
  validation: {
    enabled: true,
    realTime: true,
    showError: true
  },
  ui: {
    showRowNumbers: true,
    alternatingRowColors: true,
    enableKeyboardNavigation: true
  }
}
</script>
```

### GradeStore 状态管理

#### 基础操作
```typescript
import { useGradeStore } from '@/stores/grade'

const gradeStore = useGradeStore()

// 加载课程成绩
await gradeStore.actions.loadGrades(courseId)

// 更新单元格
gradeStore.actions.updateCell(rowId, columnId, value)

// 批量更新
const updates = {
  '1-assignment1': 85,
  '1-assignment2': 90
}
gradeStore.actions.batchUpdate(updates)

// 保存数据
await gradeStore.actions.saveGrades(updates)
```

#### 选择和导航
```typescript
// 选择单元格
gradeStore.actions.selectCell(rowId, columnId)

// 选择整行
gradeStore.actions.selectRow(rowId)

// 选择整列
gradeStore.actions.selectColumn(columnId)

// 全选
gradeStore.actions.selectAll()
```

#### 批量操作
```typescript
// 复制粘贴
gradeStore.actions.copy()
gradeStore.actions.paste()

// 批量加分
gradeStore.actions.addPoints(5)

// 批量乘以系数
gradeStore.actions.multiplyBy(1.1)

// 批量设置百分比
gradeStore.actions.setPercentage(90)
```

## 键盘快捷键

### 导航操作
- **方向键** (↑↓←→): 单元格间导航
- **Tab**: 移动到下一个单元格
- **Shift + Tab**: 移动到上一个单元格
- **Enter**: 确认输入并移动到下一行
- **Home**: 移动到行首
- **End**: 移动到行尾
- **Page Up**: 向上移动一屏
- **Page Down**: 向下移动一屏

### 编辑操作
- **F2**: 进入编辑模式
- **0-9**: 数字键直接输入
- **Enter**: 确认编辑
- **Escape**: 取消编辑
- **Delete/Backspace**: 清空单元格

### 选择操作
- **Ctrl + A**: 全选
- **Shift + 方向键**: 扩展选择
- **Ctrl + Space**: 选择列
- **Shift + Space**: 选择行

### 系统操作
- **Ctrl + C**: 复制
- **Ctrl + V**: 粘贴
- **Ctrl + X**: 剪切
- **Ctrl + Z**: 撤销
- **Ctrl + Y**: 重做
- **Ctrl + S**: 保存

## 性能优化

### 虚拟滚动
- 数据集超过100行时自动启用
- 仅渲染可见行 + 缓冲区
- 保持30+ FPS流畅滚动

### 内存管理
- 自动清理未使用数据
- 限制历史记录大小 (100条)
- 高效事件处理机制

### 优化建议
1. **大数据集**: 超过1000行时启用虚拟滚动
2. **频繁更新**: 增加自动保存防抖时间
3. **内存使用**: 复杂操作时限制历史记录大小
4. **移动设备**: 减小行高和缓冲区大小

## 数据结构

### 学生成绩行
```typescript
interface StudentGradeRow {
  id: number                  // 学生ID
  studentId: string          // 学号
  studentName: string        // 姓名
  gender: '男' | '女'        // 性别
  major: string              // 专业
  grade: string              // 年级
  class: string              // 班级
  email: string              // 邮箱
  phone: string              // 电话
  grades: Record<string, number | null>  // 各项成绩
  totalScore?: number        // 总分
  averageScore?: number      // 平均分
  rank?: number              // 排名
  isModified?: boolean       // 是否已修改
  hasErrors?: boolean        // 是否有错误
  lastModified?: string      // 最后修改时间
}
```

### 成绩列
```typescript
interface GradeColumn {
  id: string                  // 列ID
  title: string              // 列标题
  category: GradeCategory    // 成绩分类
  maxScore: number           // 满分
  weight: number             // 权重
  isRequired: boolean        // 是否必填
  isVisible: boolean         // 是否可见
  order: number              // 排序
  assignmentId?: number      // 关联作业ID
}
```

## 样式定制

### CSS变量
```scss
.grade-spreadsheet {
  --primary-color: #409eff;    // 主色调
  --success-color: #67c23a;    // 成功色
  --warning-color: #e6a23c;    // 警告色
  --danger-color: #f56c6c;     // 错误色
  --info-color: #909399;       // 信息色

  --border-color: #e4e7ed;     // 边框色
  --background-color: #f5f7fa; // 背景色
  --text-color: #303133;       // 文本色
  --text-secondary: #606266;   // 次要文本色
}
```

### 自定义主题
```scss
// 暗色主题
.grade-spreadsheet.dark-theme {
  --background-color: #1a1a1a;
  --text-color: #ffffff;
  --border-color: #404040;
}

// 高对比度主题
.grade-spreadsheet.high-contrast {
  --border-color: #000000;
  --text-color: #000000;
  --background-color: #ffffff;
}
```

## 测试

### 运行测试
```bash
# 单元测试
npm run test

# 测试覆盖率
npm run test:coverage

# E2E测试
npm run test:e2e
```

### 测试文件结构
```
src/
├── components/
│   └── __tests__/
│       ├── GradeSpreadsheet.spec.ts
│       ├── GradeCell.spec.ts
│       └── VirtualTable.spec.ts
├── stores/
│   └── __tests__/
│       └── grade.spec.ts
└── composables/
    └── __tests__/
        ├── useVirtualScroll.spec.ts
        └── useKeyboardNavigation.spec.ts
```

## 部署

### 生产构建
```bash
# 构建生产版本
npm run build

# 预览构建结果
npm run preview

# 分析包大小
npm run build -- --analyze
```

### 环境变量
```bash
# API基础URL
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 应用标题
VITE_APP_TITLE=成绩管理系统

# 是否启用调试模式
VITE_DEBUG=true
```

## 浏览器支持

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 移动端支持

- **触摸手势**: 选择和导航
- **响应式设计**: 768px以下屏幕适配
- **优化触摸目标**: 44px最小触摸区域
- **虚拟键盘**: 输入法兼容处理

## 故障排除

### 性能问题
1. 大数据集启用虚拟滚动
2. 增加行高以提升触摸体验
3. 减少自动保存频率
4. 限制历史记录大小

### 验证错误
1. 检查分数范围 (0-100)
2. 验证必填字段
3. 检查列配置
4. 验证数据类型

### 键盘导航
1. 确保组件获得焦点
2. 检查enableKeyboardNavigation设置
3. 验证无其他元素拦截事件
4. 在不同浏览器中测试

## 贡献指南

### 开发流程
1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 提交Pull Request

### 代码规范
1. 遵循现有代码风格
2. 添加完整测试覆盖
3. 更新相关文档
4. 测试大数据集性能
5. 验证无障碍访问合规性

### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试相关
chore: 构建过程或辅助工具的变动
```

## 许可证

本项目为中国大学成绩管理系统的一部分，遵循项目许可证条款。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目Issues: [GitHub Issues](https://github.com/wangjia15/studentcourse-management/issues)
- 邮箱: support@example.com

---

**注意**: 本文档随项目更新而更新，请定期查看最新版本。