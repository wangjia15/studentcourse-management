<template>
  <div class="grade-statistics">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else class="statistics-content">
      <!-- Overview Cards -->
      <div class="stats-overview">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalStudents }}</div>
            <div class="stat-label">学生总数</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.averageScore.toFixed(1) }}</div>
            <div class="stat-label">平均分</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Trophy /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.highestScore.toFixed(1) }}</div>
            <div class="stat-label">最高分</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.passRate.toFixed(1) }}%</div>
            <div class="stat-label">及格率</div>
          </div>
        </div>
      </div>

      <!-- Score Distribution Chart -->
      <div class="chart-section">
        <h3>成绩分布</h3>
        <div ref="chartRef" class="chart-container"></div>
      </div>

      <!-- Grade Breakdown -->
      <div class="grade-breakdown">
        <h3>等级分布</h3>
        <div class="grade-bars">
          <div v-for="grade in gradeDistribution" :key="grade.range" class="grade-bar-item">
            <div class="grade-label">{{ grade.range }}</div>
            <div class="grade-bar-container">
              <div
                class="grade-bar"
                :style="{ width: `${grade.percentage}%` }"
                :class="grade.class"
              ></div>
            </div>
            <div class="grade-count">{{ grade.count }}人</div>
            <div class="grade-percentage">{{ grade.percentage.toFixed(1) }}%</div>
          </div>
        </div>
      </div>

      <!-- Detailed Table -->
      <div class="detailed-stats">
        <h3>详细统计</h3>
        <el-table :data="detailedStats" stripe>
          <el-table-column prop="category" label="项目" width="200" />
          <el-table-column prop="count" label="人数" width="100" align="center" />
          <el-table-column prop="percentage" label="百分比" align="center">
            <template #default="{ row }">
              {{ row.percentage.toFixed(1) }}%
            </template>
          </el-table-column>
          <el-table-column prop="average" label="平均分" align="center">
            <template #default="{ row }">
              {{ row.average?.toFixed(1) || '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Export Options -->
      <div class="export-section">
        <h3>导出选项</h3>
        <div class="export-buttons">
          <el-button @click="exportPDF">
            <el-icon><Document /></el-icon>
            导出PDF报告
          </el-button>
          <el-button @click="exportExcel">
            <el-icon><Download /></el-icon>
            导出Excel
          </el-button>
          <el-button @click="printReport">
            <el-icon><Printer /></el-icon>
            打印报告
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useGradeStore } from '@/stores/grade'

// Props
interface Props {
  courseId: number
}

const props = defineProps<Props>()

// Store
const gradeStore = useGradeStore()

// Refs
const chartRef = ref<HTMLElement>()
const loading = ref(false)

// Computed statistics
const stats = computed(() => {
  const rows = gradeStore.state.rows
  if (rows.length === 0) {
    return {
      totalStudents: 0,
      averageScore: 0,
      highestScore: 0,
      lowestScore: 0,
      passRate: 0
    }
  }

  const scores = rows.map(row => row.totalScore || 0).filter(score => score > 0)
  const totalStudents = rows.length
  const averageScore = scores.reduce((sum, score) => sum + score, 0) / scores.length || 0
  const highestScore = Math.max(...scores, 0)
  const lowestScore = Math.min(...scores, 0)
  const passCount = scores.filter(score => score >= 60).length
  const passRate = totalStudents > 0 ? (passCount / totalStudents) * 100 : 0

  return {
    totalStudents,
    averageScore,
    highestScore,
    lowestScore,
    passRate
  }
})

const gradeDistribution = computed(() => {
  const rows = gradeStore.state.rows
  const distribution = [
    { range: '90-100', min: 90, max: 100, class: 'excellent', count: 0 },
    { range: '80-89', min: 80, max: 89, class: 'good', count: 0 },
    { range: '70-79', min: 70, max: 79, class: 'average', count: 0 },
    { range: '60-69', min: 60, max: 69, class: 'pass', count: 0 },
    { range: '0-59', min: 0, max: 59, class: 'fail', count: 0 }
  ]

  rows.forEach(row => {
    const score = row.totalScore || 0
    const grade = distribution.find(g => score >= g.min && score <= g.max)
    if (grade) {
      grade.count++
    }
  })

  const total = rows.length
  return distribution.map(grade => ({
    ...grade,
    percentage: total > 0 ? (grade.count / total) * 100 : 0
  }))
})

const detailedStats = computed(() => {
  const rows = gradeStore.state.rows
  const columns = gradeStore.state.columns

  return columns.map(column => {
    const scores = rows
      .map(row => row.grades[column.id])
      .filter(score => score !== null && score !== undefined && score > 0)

    const count = scores.length
    const percentage = rows.length > 0 ? (count / rows.length) * 100 : 0
    const average = count > 0 ? scores.reduce((sum, score) => sum + score, 0) / count : 0

    return {
      category: column.title,
      count,
      percentage,
      average
    }
  })
})

let chartInstance: echarts.ECharts | null = null

// Methods
const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  const distribution = gradeDistribution.value
  const data = distribution.map(grade => ({
    name: grade.range,
    value: grade.count,
    itemStyle: {
      color: getGradeColor(grade.class)
    }
  }))

  const option: echarts.EChartsOption = {
    title: {
      text: '成绩分布直方图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}: ${data.value}人 (${data.data.percentage.toFixed(1)}%)`
      }
    },
    xAxis: {
      type: 'category',
      data: distribution.map(grade => grade.range),
      axisLabel: {
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      name: '人数'
    },
    series: [
      {
        name: '人数',
        type: 'bar',
        data,
        barWidth: '60%',
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => params.value
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

const getGradeColor = (gradeClass: string): string => {
  const colors: Record<string, string> = {
    excellent: '#67c23a',
    good: '#409eff',
    average: '#e6a23c',
    pass: '#f56c6c',
    fail: '#f56c6c'
  }
  return colors[gradeClass] || '#909399'
}

const exportPDF = () => {
  // TODO: Implement PDF export
  console.log('Export PDF')
}

const exportExcel = () => {
  // TODO: Implement Excel export
  console.log('Export Excel')
}

const printReport = () => {
  window.print()
}

// Lifecycle
onMounted(() => {
  loading.value = true

  // Simulate loading data
  setTimeout(() => {
    loading.value = false
    initChart()
  }, 1000)
})

watch(gradeDistribution, () => {
  updateChart()
}, { deep: true })

// Handle window resize
window.addEventListener('resize', () => {
  if (chartInstance) {
    chartInstance.resize()
  }
})
</script>

<style scoped lang="scss">
.grade-statistics {
  padding: 20px;
}

.loading-container {
  padding: 20px;
}

.statistics-content {
  .stats-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 32px;

    .stat-card {
      display: flex;
      align-items: center;
      padding: 20px;
      background: #fff;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

      .stat-icon {
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #409eff;
        border-radius: 50%;
        margin-right: 16px;

        .el-icon {
          font-size: 24px;
          color: #fff;
        }
      }

      .stat-info {
        .stat-value {
          font-size: 24px;
          font-weight: bold;
          color: #303133;
          line-height: 1;
        }

        .stat-label {
          margin-top: 4px;
          font-size: 14px;
          color: #909399;
        }
      }
    }
  }

  .chart-section {
    margin-bottom: 32px;

    h3 {
      margin-bottom: 16px;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }

    .chart-container {
      height: 400px;
      background: #fff;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      padding: 20px;
    }
  }

  .grade-breakdown {
    margin-bottom: 32px;

    h3 {
      margin-bottom: 16px;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }

    .grade-bars {
      .grade-bar-item {
        display: grid;
        grid-template-columns: 80px 1fr 60px 80px;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;

        .grade-label {
          font-weight: 500;
          color: #303133;
        }

        .grade-bar-container {
          height: 24px;
          background: #f5f7fa;
          border-radius: 12px;
          overflow: hidden;

          .grade-bar {
            height: 100%;
            border-radius: 12px;
            transition: width 0.3s ease;

            &.excellent {
              background: linear-gradient(90deg, #67c23a, #85ce61);
            }

            &.good {
              background: linear-gradient(90deg, #409eff, #66b1ff);
            }

            &.average {
              background: linear-gradient(90deg, #e6a23c, #ebb563);
            }

            &.pass {
              background: linear-gradient(90deg, #f56c6c, #f78989);
            }

            &.fail {
              background: linear-gradient(90deg, #f56c6c, #ff4d4f);
            }
          }
        }

        .grade-count {
          font-weight: 500;
          color: #606266;
        }

        .grade-percentage {
          font-weight: 500;
          color: #909399;
        }
      }
    }
  }

  .detailed-stats {
    margin-bottom: 32px;

    h3 {
      margin-bottom: 16px;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
  }

  .export-section {
    h3 {
      margin-bottom: 16px;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }

    .export-buttons {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
  }
}

// Print styles
@media print {
  .grade-statistics {
    padding: 0;

    .export-section {
      display: none;
    }

    .chart-container {
      break-inside: avoid;
    }
  }
}

// Mobile responsive
@media (max-width: 768px) {
  .grade-statistics {
    padding: 16px;
  }

  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;

    .stat-card {
      padding: 16px;

      .stat-icon {
        width: 40px;
        height: 40px;
        margin-right: 12px;

        .el-icon {
          font-size: 20px;
        }
      }

      .stat-info {
        .stat-value {
          font-size: 20px;
        }
      }
    }
  }

  .grade-bar-item {
    grid-template-columns: 60px 1fr 50px 60px !important;
    gap: 8px !important;
    font-size: 13px;
  }

  .export-buttons {
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }
}
</style>