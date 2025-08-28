<template>
  <el-card
    class="video-card"
    shadow="hover"
    @click="handlePlay"
  >
    <div class="video-thumbnail">
      <img 
        :src="`/api/videos/${video.id}/thumbnail?t=${video.updated_at || Date.now()}`"
        @load="handleThumbnailLoad"
        @error="handleThumbnailError"
        alt="视频缩略图"
        class="thumbnail-image"
      />
      <el-icon class="play-icon"><VideoPlay /></el-icon>
      <!-- 播放进度条 -->
      <div v-if="video.watch_progress > 0 && !video.is_completed" class="progress-overlay">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: video.watch_progress + '%' }"
          ></div>
        </div>
        <div class="progress-text">{{ Math.round(video.watch_progress) }}%</div>
      </div>
      <!-- 已完成标记 -->
      <div v-if="video.is_completed" class="completed-overlay">
        <el-icon class="completed-icon"><Check /></el-icon>
      </div>
    </div>
    <div class="video-info">
      <div class="video-title" :title="video.filename">{{ video.filename }}</div>
      <div class="video-meta">
        <span>{{ formatFileSize(video.size) }}</span>
        <span>{{ formatDuration(video.duration) }}</span>
        <VideoActions
          :video="video"
          @edit="handleEdit"
          @update-status="handleUpdateStatus"
          @delete="handleDelete"
          @show-tags-dialog="handleShowTagsDialog"
        />
      </div>
      <div class="video-tags" v-if="video.tags && video.tags.length > 0">
        <el-tag 
          v-for="tag in video.tags" 
          :key="tag.id" 
          size="small" 
          class="video-tag"
          @click.stop
          closable
          @close.stop="handleRemoveTag(tag.id)"
        >
          {{ tag.name }}
        </el-tag>
        <el-button 
          type="primary" 
          size="small" 
          circle 
          plain 
          class="add-tag-btn"
          @click.stop="handleShowTagsDialog"
        >
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <div class="video-tags" v-else>
        <el-button 
          type="primary" 
          size="small" 
          plain 
          class="add-tag-btn empty-tags"
          @click.stop="handleShowTagsDialog"
        >
          <el-icon><Plus /></el-icon> 添加标签
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { VideoPlay, Plus, Check } from '@element-plus/icons-vue'
import VideoActions from './VideoActions.vue'

const props = defineProps({
  video: {
    type: Object,
    required: true
  }
})

const emit = defineEmits([
  'play',
  'edit', 
  'update-status',
  'delete',
  'show-tags-dialog',
  'remove-tag',
  'thumbnail-load',
  'thumbnail-error'
])

// 格式化文件大小
const formatFileSize = (size) => {
  if (size >= 1024) {
    return `${(size / 1024).toFixed(2)} GB`
  }
  return `${size.toFixed(2)} MB`
}

// 格式化视频时长
const formatDuration = (duration) => {
  const hours = Math.floor(duration / 3600)
  const minutes = Math.floor((duration % 3600) / 60)
  const seconds = Math.floor(duration % 60)
  // 如果小时数为0，则只显示分钟和秒
  if (hours === 0) {
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

// 事件处理函数
const handlePlay = () => {
  emit('play', props.video)
}

const handleEdit = () => {
  emit('edit', props.video)
}

const handleUpdateStatus = (type, value) => {
  emit('update-status', props.video, type, value)
}

const handleDelete = () => {
  emit('delete', props.video)
}

const handleShowTagsDialog = () => {
  emit('show-tags-dialog', props.video)
}

const handleRemoveTag = (tagId) => {
  emit('remove-tag', props.video.id, tagId)
}

const handleThumbnailLoad = (event) => {
  emit('thumbnail-load', props.video, event)
}

const handleThumbnailError = (event) => {
  emit('thumbnail-error', props.video, event)
}
</script>

<style scoped>
.video-card {
  cursor: pointer;
  transition: transform 0.2s;
  width: 100%;
  min-width: 240px;
}

.video-card:hover {
  transform: translateY(-3px);
}

.video-thumbnail {
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

.video-thumbnail::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.1);
  opacity: 0;
  transition: opacity 0.2s;
}

.video-card:hover .video-thumbnail::before {
  opacity: 1;
}

.play-icon {
  font-size: 48px;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s;
  position: relative;
  z-index: 1;
}

.video-card:hover .play-icon {
  opacity: 1;
  color: #909399;
  opacity: 0.7;
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}

.video-info {
  padding: 0 2px 2px;
}

.video-title {
  font-size: 13px;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 0.9em;
  margin-bottom: 8px;
}

.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.video-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.add-tag-btn {
  padding: 2px;
  height: 22px;
  width: 22px;
}

.add-tag-btn.empty-tags {
  width: auto;
  height: auto;
  font-size: 12px;
}

/* 播放进度条样式 */
.progress-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  overflow: hidden;
  margin-right: 8px;
}

.progress-fill {
  height: 100%;
  background-color: #409EFF;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  color: white;
  font-size: 12px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* 已完成标记样式 */
.completed-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
  background-color: rgba(67, 160, 71, 0.9);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.completed-icon {
  color: white;
  font-size: 18px;
}
</style>