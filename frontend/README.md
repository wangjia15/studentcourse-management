# 中国大学成绩管理系统 - 前端

基于 Vue3 + TypeScript + Vite 构建的现代化前端应用。

## 技术栈

### 核心框架
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript 超集
- **Vite** - 快速的构建工具和开发服务器

### UI 框架
- **Element Plus** - Vue 3 的桌面端组件库
- **Tailwind CSS** - 实用优先的 CSS 框架
- **Shadcn-vue** - 现代化的 Vue 组件库

### 状态管理
- **Pinia** - Vue 3 的状态管理库
- **Vue Router** - Vue.js 的官方路由管理器

### 开发工具
- **ESLint** - 代码质量检查工具
- **Prettier** - 代码格式化工具
- **Vue TSC** - Vue 的 TypeScript 编译器

## 项目结构

```
frontend/
├── src/
│   ├── assets/          # 静态资源
│   ├── components/      # Vue 组件
│   │   └── ui/         # UI 基础组件
│   ├── lib/            # 工具函数
│   ├── router/         # 路由配置
│   ├── stores/         # Pinia 状态管理
│   ├── types/          # TypeScript 类型定义
│   ├── utils/          # 工具函数
│   ├── views/          # 页面组件
│   ├── App.vue         # 根组件
│   └── main.ts         # 应用入口
├── public/             # 公共资源
├── index.html          # HTML 模板
├── package.json        # 项目配置
├── tsconfig.json       # TypeScript 配置
├── vite.config.ts      # Vite 配置
├── tailwind.config.js  # Tailwind CSS 配置
└── README.md           # 项目文档
```

## 开发环境设置

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖
```bash
npm install
```

### 开发服务器
```bash
npm run dev
```

应用将在 `http://localhost:5173` 启动。

### 构建生产版本
```bash
npm run build
```

### 预览生产构建
```bash
npm run preview
```

## 开发脚本

- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run preview` - 预览生产构建
- `npm run lint` - 运行 ESLint 检查
- `npm run format` - 格式化代码

## 功能特性

### 已实现功能
- ✅ Vue3 + TypeScript 项目基础架构
- ✅ Vue Router 路由系统
- ✅ Pinia 状态管理
- ✅ Element Plus UI 组件库集成
- ✅ Tailwind CSS 样式系统
- ✅ Shadcn-vue 组件库配置
- ✅ ESLint + Prettier 代码规范
- ✅ 响应式设计支持

### 示例页面
- **首页** - 系统概览和功能介绍
- **学生管理** - 使用 Element Plus 表格组件的学生列表页面
- **关于页面** - 技术栈和项目信息

## 代码规范

### ESLint 配置
项目使用 ESLint 进行代码质量检查，配置文件：`.eslintrc.cjs`

### Prettier 配置
使用 Prettier 进行代码格式化，配置文件：`.prettierrc.json`

### TypeScript 配置
严格的 TypeScript 配置确保类型安全：
- `tsconfig.json` - 主配置文件
- `tsconfig.app.json` - 应用代码配置
- `tsconfig.node.json` - 构建工具配置

## 组件开发指南

### UI 组件
基于 Shadcn-vue 的设计系统，支持：
- 主题定制
- 响应式设计
- 可访问性
- TypeScript 类型支持

### 状态管理
使用 Pinia 进行状态管理，推荐的结构：
```typescript
export const useExampleStore = defineStore('example', () => {
  // State
  const state = ref()

  // Getters
  const computed = computed(() => {})

  // Actions
  const action = async () => {}

  return { state, computed, action }
})
```

## 构建和部署

### 构建配置
- **输出目录**: `dist/`
- **资源处理**: Vite 自动处理
- **代码分割**: 自动优化
- **压缩**: 生产环境自动压缩

### 部署建议
1. 运行 `npm run build` 生成生产构建
2. 将 `dist/` 目录内容部署到静态文件服务器
3. 配置服务器支持 SPA 路由（所有请求重定向到 index.html）

## 开发注意事项

1. **TypeScript**: 始终使用 TypeScript 进行类型安全开发
2. **组件**: 使用 Composition API (`<script setup>`) 语法
3. **样式**: 优先使用 Tailwind CSS 实用类
4. **状态**: 复杂状态使用 Pinia 管理
5. **路由**: 使用 Vue Router 进行页面导航

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 许可证

本项目遵循 MIT 许可证。