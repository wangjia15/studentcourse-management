<template>
  <div class="about">
    <h1>关于系统</h1>
    <p>这是一个基于 Vue3 + TypeScript + FastAPI 开发的中国大学成绩管理系统。</p>

    <div class="tech-stack">
      <h2>技术栈</h2>
      <div class="stack-grid">
        <div class="stack-item">
          <h3>前端</h3>
          <ul>
            <li>Vue 3</li>
            <li>TypeScript</li>
            <li>Vite</li>
            <li>Vue Router</li>
            <li>Pinia</li>
            <li>Tailwind CSS</li>
            <li>Element Plus</li>
          </ul>
        </div>
        <div class="stack-item">
          <h3>后端</h3>
          <ul>
            <li>FastAPI</li>
            <li>Python</li>
            <li>SQLAlchemy</li>
            <li>SQLite</li>
            <li>JWT 认证</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// About view setup
</script>

<style scoped>
.about {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
}

.tech-stack {
  margin-top: 2rem;
}

.stack-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 1rem;
}

.stack-item {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
}

.stack-item h3 {
  color: #495057;
  margin-bottom: 1rem;
}

.stack-item ul {
  list-style: none;
  padding: 0;
}

.stack-item li {
  color: #6c757d;
  padding: 0.25rem 0;
}

.stack-item li:before {
  content: "✓ ";
  color: #28a745;
  font-weight: bold;
}
</style>