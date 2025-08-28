<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <h1>视频文件管理</h1>
        
        <!-- 继续观看区域 -->
        <div v-if="continueWatchingVideos.length > 0" class="continue-watching-section">
          <div class="section-header">
            <h2>继续观看</h2>
            <el-button 
              type="text" 
              size="small" 
              @click="clearAllProgress"
              class="clear-all-btn"
            >
              清除全部
            </el-button>
          </div>
          <div class="continue-watching-grid">
            <el-card
              v-for="video in continueWatchingVideos"
              :key="video.id"
              class="continue-video-card"
              shadow="hover"
              @click="handlePlayVideo(video)"
            >
              <div class="continue-video-thumbnail">
                <img 
                  :src="`/api/videos/${video.id}/thumbnail?t=${video.updated_at || Date.now()}`"
                  alt="视频缩略图"
                  class="continue-thumbnail-image"
                />
                <el-icon class="continue-play-icon"><VideoPlay /></el-icon>
                <div class="continue-progress-overlay">
                  <div class="continue-progress-bar">
                    <div 
                      class="continue-progress-fill" 
                      :style="{ width: video.watch_progress + '%' }"
                    ></div>
                  </div>
                  <div class="continue-progress-text">{{ Math.round(video.watch_progress) }}%</div>
                </div>
              </div>
              <div class="continue-video-info">
                <div class="continue-video-title" :title="video.filename">{{ video.filename }}</div>
                <div class="continue-video-meta">
                  <span>{{ formatDuration(video.duration) }}</span>
                  <span>剩余 {{ formatDuration(video.duration * (1 - video.watch_progress / 100)) }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
        
        <VideoList ref="videoListRef" @video-updated="loadContinueWatching" />
        
        <!-- 视频播放器 -->
        <VideoPlayer 
          :visible="showPlayer" 
          :video-id="currentVideo?.id" 
          @close="handlePlayerClose" 
        />
      </el-col>
    </el-row>
  </div>
  
  <!-- 视频播放器 -->
  <VideoPlayer
    v-model:visible="showPlayer"
    :video-id="currentVideo?.id"
    :title="currentVideo?.filename"
    @update:visible="handlePlayerClose"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import VideoList from '../components/VideoList.vue'
import VideoPlayer from '../components/VideoPlayer.vue'
import axios from 'axios'

const continueWatchingVideos = ref([])
const showPlayer = ref(false)
const currentVideo = ref(null)
const videoListRef = ref(null)

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return '00:00'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// 加载继续观看的视频
const loadContinueWatching = async () => {
  try {
    const response = await axios.get('/api/videos/continue-watching')
    continueWatchingVideos.value = response.data
  } catch (error) {
    console.error('加载继续观看视频失败:', error)
  }
}

// 播放视频
const handlePlayVideo = (video) => {
  currentVideo.value = video
  showPlayer.value = true
}

// 播放器关闭时刷新继续观看列表
const handlePlayerClose = () => {
  showPlayer.value = false
  currentVideo.value = null
  loadContinueWatching()
  // 刷新主视频列表
  if (videoListRef.value && videoListRef.value.loadVideos) {
    videoListRef.value.loadVideos()
  }
}

// 清除所有播放进度
const clearAllProgress = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除所有视频的播放进度吗？此操作不可撤销。',
      '清除播放进度',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 逐个清除每个视频的播放进度
    for (const video of continueWatchingVideos.value) {
      await axios.delete(`/api/videos/${video.id}/progress`)
    }
    
    ElMessage.success('已清除所有播放进度')
    loadContinueWatching()
    
    // 刷新主视频列表
    if (videoListRef.value && videoListRef.value.loadVideos) {
      videoListRef.value.loadVideos()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除播放进度失败:', error)
      ElMessage.error('清除播放进度失败')
    }
  }
}

onMounted(() => {
  loadContinueWatching()
})
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

/* 继续观看区域样式 */
.continue-watching-section {
  margin-bottom: 32px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.clear-all-btn {
  color: #909399;
  font-size: 12px;
}

.clear-all-btn:hover {
  color: #f56c6c;
}

.continue-watching-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.continue-video-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.continue-video-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.continue-video-thumbnail {
  aspect-ratio: 16/9;
  background-color: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  position: relative;
  border-radius: 4px;
  overflow: hidden;
}

.continue-thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}

.continue-play-icon {
  font-size: 32px;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s;
  position: relative;
  z-index: 2;
}

.continue-video-card:hover .continue-play-icon {
  opacity: 0.8;
}

.continue-progress-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
  padding: 6px 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.continue-progress-bar {
  flex: 1;
  height: 3px;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  overflow: hidden;
  margin-right: 6px;
}

.continue-progress-fill {
  height: 100%;
  background-color: #67c23a;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.continue-progress-text {
  color: white;
  font-size: 10px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.continue-video-info {
  padding: 0 4px;
}

.continue-video-title {
  font-size: 12px;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #303133;
}

.continue-video-meta {
  display: flex;
  justify-content: space-between;
  color: #909399;
  font-size: 10px;
}
</style>