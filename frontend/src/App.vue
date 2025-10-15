<template>
  <div id="app">
    <header>
      <nav>
        <router-link to="/">首页</router-link>
        <router-link to="/students">学生管理</router-link>
        <router-link to="/about">关于</router-link>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
// App component setup
</script>

<style scoped>
#app {
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

header {
  background-color: #f8f9fa;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

nav {
  display: flex;
  gap: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

nav a {
  color: #495057;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

nav a:hover,
nav a.router-link-active {
  background-color: #e9ecef;
  color: #212529;
}

main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}
</style>