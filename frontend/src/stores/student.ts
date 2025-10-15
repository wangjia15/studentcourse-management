import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Student {
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

export const useStudentStore = defineStore('student', () => {
  // State
  const students = ref<Student[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const totalStudents = computed(() => students.value.length)
  const maleStudents = computed(() => students.value.filter(s => s.gender === '男'))
  const femaleStudents = computed(() => students.value.filter(s => s.gender === '女'))

  // Actions
  const fetchStudents = async () => {
    loading.value = true
    error.value = null

    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      // 模拟数据
      students.value = [
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
    } catch (err) {
      error.value = '加载学生数据失败'
      console.error('Error fetching students:', err)
    } finally {
      loading.value = false
    }
  }

  const addStudent = async (student: Omit<Student, 'id'>) => {
    loading.value = true
    error.value = null

    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))

      const newStudent: Student = {
        ...student,
        id: Date.now()
      }

      students.value.push(newStudent)
      return newStudent
    } catch (err) {
      error.value = '添加学生失败'
      console.error('Error adding student:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateStudent = async (id: number, updates: Partial<Student>) => {
    loading.value = true
    error.value = null

    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))

      const index = students.value.findIndex(s => s.id === id)
      if (index !== -1) {
        students.value[index] = { ...students.value[index], ...updates }
      }
    } catch (err) {
      error.value = '更新学生失败'
      console.error('Error updating student:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteStudent = async (id: number) => {
    loading.value = true
    error.value = null

    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))

      students.value = students.value.filter(s => s.id !== id)
    } catch (err) {
      error.value = '删除学生失败'
      console.error('Error deleting student:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    students,
    loading,
    error,

    // Getters
    totalStudents,
    maleStudents,
    femaleStudents,

    // Actions
    fetchStudents,
    addStudent,
    updateStudent,
    deleteStudent,
    clearError
  }
})