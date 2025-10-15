<template>
  <div class="student-list">
    <div class="page-header">
      <h1>学生管理</h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        添加学生
      </el-button>
    </div>

    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="学号">
          <el-input v-model="searchForm.studentId" placeholder="请输入学号" clearable />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="searchForm.name" placeholder="请输入姓名" clearable />
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="searchForm.major" placeholder="请选择专业" clearable>
            <el-option label="计算机科学与技术" value="cs" />
            <el-option label="软件工程" value="se" />
            <el-option label="数据科学" value="ds" />
            <el-option label="人工智能" value="ai" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
        element-loading-text="加载中..."
      >
        <el-table-column prop="studentId" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="gender" label="性别" width="80">
          <template #default="{ row }">
            <el-tag :type="row.gender === '男' ? 'primary' : 'success'">
              {{ row.gender }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="major" label="专业" width="180" />
        <el-table-column prop="grade" label="年级" width="100" />
        <el-table-column prop="class" label="班级" width="120" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="phone" label="电话" width="150" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button size="small" type="warning" link @click="handleViewGrades(row)">
              查看成绩
            </el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface Student {
  id: number
  studentId: string
  name: string
  gender: string
  major: string
  grade: string
  class: string
  email: string
  phone: string
}

const loading = ref(false)
const tableData = ref<Student[]>([])

const searchForm = reactive({
  studentId: '',
  name: '',
  major: ''
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 模拟数据
const mockData: Student[] = [
  {
    id: 1,
    studentId: '2021001',
    name: '张三',
    gender: '男',
    major: '计算机科学与技术',
    grade: '2021级',
    class: '计科2101',
    email: 'zhangsan@example.com',
    phone: '13800138001'
  },
  {
    id: 2,
    studentId: '2021002',
    name: '李四',
    gender: '女',
    major: '软件工程',
    grade: '2021级',
    class: '软工2101',
    email: 'lisi@example.com',
    phone: '13800138002'
  },
  {
    id: 3,
    studentId: '2021003',
    name: '王五',
    gender: '男',
    major: '数据科学',
    grade: '2021级',
    class: '数据2101',
    email: 'wangwu@example.com',
    phone: '13800138003'
  }
]

const loadStudents = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    tableData.value = mockData
    pagination.total = mockData.length
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  ElMessage.success('搜索功能待实现')
  loadStudents()
}

const handleReset = () => {
  Object.assign(searchForm, {
    studentId: '',
    name: '',
    major: ''
  })
  loadStudents()
}

const handleAdd = () => {
  ElMessage.info('添加学生功能待实现')
}

const handleEdit = (row: Student) => {
  ElMessage.info(`编辑学生: ${row.name}`)
}

const handleViewGrades = (row: Student) => {
  ElMessage.info(`查看 ${row.name} 的成绩`)
}

const handleDelete = async (row: Student) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除学生 ${row.name} 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    ElMessage.success('删除成功')
    loadStudents()
  } catch {
    ElMessage.info('已取消删除')
  }
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  loadStudents()
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  loadStudents()
}

onMounted(() => {
  loadStudents()
})
</script>

<style scoped>
.student-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.search-card {
  margin-bottom: 20px;
}

.search-form {
  margin: 0;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>