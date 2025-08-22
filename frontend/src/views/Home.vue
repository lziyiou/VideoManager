<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <h1>视频文件管理</h1>
        <VideoList />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import VideoList from '../components/VideoList.vue'
</script>

<style scoped>
.home {
  max-width: auto;
  margin: 0 auto;
  padding: 0 10px;
}

h1 {
  text-align: center;
  margin-bottom: 2rem;
}

.feature-card {
  margin-bottom: 2rem;
}

.el-card {
  text-align: center;
  margin-bottom: 1rem;
}

.el-icon {
  font-size: 2rem;
  color: #409EFF;
  margin-bottom: 1rem;
}

h4 {
  margin: 1rem 0;
}

p {
  color: #666;
}
</style>