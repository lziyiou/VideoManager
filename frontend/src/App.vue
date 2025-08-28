<template>
  <el-container class="app-container">
    <el-header>
      <el-menu mode="horizontal" router>
        <el-menu-item index="/">首页</el-menu-item>
        <el-menu-item index="/admin">后台管理</el-menu-item>
        <el-menu-item index="/tags">标签管理</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <router-view></router-view>
    </el-main>
  </el-container>
</template>

<script setup>
import { onMounted, provide, ref } from 'vue'
import SettingService from './services/setting_service'

// 全局设置状态
const globalSettings = ref({
  videosPerPage: 12 // 默认值
})

// 初始化全局设置
const initializeGlobalSettings = async () => {
  try {
    const videosPerPage = await SettingService.getVideosPerPage()
    globalSettings.value.videosPerPage = videosPerPage
  } catch (error) {
    console.error('获取全局设置失败:', error)
    // 保持默认值
  }
}

// 提供全局设置给子组件
provide('globalSettings', globalSettings)

// 应用启动时初始化设置
onMounted(() => {
  initializeGlobalSettings()
})
</script>

<style>
.app-container {
  min-height: 100vh;
}

.el-header {
  padding: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.el-main {
  padding: 20px;
}
</style>