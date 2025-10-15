<template>
  <div class="home">
    <h1>中国大学成绩管理系统</h1>
    <p>欢迎使用中国大学成绩管理系统</p>
    <div class="features">
      <div class="feature-card">
        <h3>学生管理</h3>
        <p>管理学生信息和档案</p>
      </div>
      <div class="feature-card">
        <h3>课程管理</h3>
        <p>管理课程信息和安排</p>
      </div>
      <div class="feature-card">
        <h3>成绩管理</h3>
        <p>录入和管理学生成绩</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Home view setup
</script>

<style scoped>
.home {
  text-align: center;
}

h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-top: 3rem;
}

.feature-card {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
}

.feature-card h3 {
  color: #495057;
  margin-bottom: 1rem;
}

.feature-card p {
  color: #6c757d;
}
</style>