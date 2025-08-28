<template>
  <div class="video-list">

    <div v-loading="loading">
      <!-- 列表视图 -->
      <div v-if="isListView" class="video-list-view">
        <el-table :data="videos" style="width: 100%" stripe>
          <el-table-column label="缩略图" width="120" align="center">
            <template #default="{ row }">
              <div class="thumbnail-container">
                <img 
                  :src="`/api/videos/${row.id}/thumbnail?t=${row.updated_at || Date.now()}`"
                  @error="handleThumbnailError"
                  alt="视频缩略图"
                  class="list-thumbnail"
                  @click="playVideo(row)"
                />
                <div v-if="row.watch_progress > 0 && !row.is_completed" class="progress-overlay">
                  <div class="progress-bar">
                    <div 
                      class="progress-fill" 
                      :style="{ width: row.watch_progress + '%' }"
                    ></div>
                  </div>
                </div>
                <div v-if="row.is_completed" class="completed-overlay">
                  <el-icon class="completed-icon"><Check /></el-icon>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="filename" label="文件名" min-width="250" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="filename-cell">
                <div class="filename-text" @click="playVideo(row)">{{ row.filename }}</div>
                <div class="file-meta">
                  <span class="file-size">{{ formatFileSize(row.size) }}</span>
                  <span class="file-duration">{{ formatDuration(row.duration) }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="标签" width="200">
            <template #default="{ row }">
              <div class="video-tags">
                <el-tag 
                  v-for="tag in row.tags.slice(0, 2)" 
                  :key="tag.id" 
                  size="small" 
                  class="video-tag"
                  closable
                  @close="removeVideoTag(row.id, tag.id)"
                >
                  {{ tag.name }}
                </el-tag>
                <el-tag v-if="row.tags.length > 2" size="small" type="info">
                  +{{ row.tags.length - 2 }}
                </el-tag>
                <el-button 
                  type="primary" 
                  size="small" 
                  circle 
                  plain 
                  @click="showTagDialog(row)"
                >
                  <el-icon><Plus /></el-icon>
                </el-button>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="200" align="center">
            <template #default="{ row }">
              <div class="operation-buttons">
                <el-button link type="primary" @click="playVideo(row)">
                  <el-icon><VideoPlay /></el-icon>
                  播放
                </el-button>
                <VideoActions 
                  :video="row" 
                  :show-labels="false"
                  @edit="editVideo"
                  @update-status="handleUpdateStatus"
                  @delete="deleteVideo"
                />
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 网格视图 -->
      <div v-if="isGridView" class="video-grid">
        <VideoCard
          v-for="video in videos"
          :key="video.id"
          :video="video"
          @play="playVideo"
          @edit="editVideo"
          @update-status="handleUpdateStatus"
          @delete="deleteVideo"
          @show-tags-dialog="showTagDialog"
          @remove-tag="removeVideoTag"
        />
      </div>
    </div>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[8, 12, 16, 24]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, Plus, Check } from '@element-plus/icons-vue'
import { useVideoList } from '../composables/useVideoList.js'
import TagService from '../services/tag_service.js'
import VideoCard from './VideoCard.vue'
import VideoActions from './VideoActions.vue'

// 定义props
const props = defineProps({
  searchKeyword: {
    type: String,
    default: ''
  },
  onlyFavorites: {
    type: Boolean,
    default: false
  },
  selectedTagIds: {
    type: Array,
    default: () => []
  },
  durationFilter: {
    type: String,
    default: ''
  },
  sortFilter: {
    type: String,
    default: 'random'
  },
  viewMode: {
    type: String,
    default: 'grid'
  }
})

// 使用自定义 Hook
const {
  videos,
  loading,
  searchKeyword,
  onlyFavorites,
  selectedTagIds,
  allTags,
  durationFilter,
  sortFilter,
  viewMode,
  currentPage,
  pageSize,
  total,
  totalPages,
  hasVideos,
  isGridView,
  isListView,
  initializeFromRoute,
  loadVideos,
  loadTags,
  handleSearch,
  handleSortChange,
  refreshRandom,
  handleSizeChange,
  handleCurrentChange,
  handleViewModeChange,
  updateVideoProgress,
  deleteVideo: deleteVideoFromList,
  updateVideo,
  renameVideo
} = useVideoList(props)

// 定义事件
const emit = defineEmits(['video-updated', 'play-video', 'show-tags-dialog'])

// 播放视频
const playVideo = (video) => {
  emit('play-video', video)
}

// 文件名验证器
const validateFilename = (value) => {
  if (!value) return '文件名不能为空'
  if (value.length > 255) return '文件名不能超过255个字符'
  return true
}

// 处理重命名错误
const handleRenameError = (error) => {
  console.error('重命名失败:', error)
  if (error.response?.data?.detail) {
    ElMessage({
      message: error.response.data.detail,
      type: 'error',
      duration: 5000,
      showClose: true
    })
  } else {
    ElMessage.error('重命名失败，请稍后再试。')
  }
}

// 编辑视频
const editVideo = async (video) => {
  try {
    const ext = video.filename.split('.').pop()
    const oldName = video.filename.replace('.' + ext, '')
    
    const { value: newFilename } = await ElMessageBox.prompt('请输入新的文件名', '重命名', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: oldName,
      inputValidator: validateFilename,
      inputErrorMessage: '文件名格式不正确'
    })

    const newName = newFilename.trim() + '.' + ext
    if (newName === video.filename) return

    const result = await renameVideo(video.id, newName)
     if (result.success) {
       ElMessage.success('重命名成功！')
     } else {
       handleRenameError(result.error)
     }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重命名操作失败:', error)
    }
  }
}

// 处理视频状态更新
const handleUpdateStatus = async (video, field, value) => {
  const statusConfig = {
    favorite: {
      key: 'is_favorite',
      message: value => value ? '已收藏' : '已取消收藏'
    },
    webPlayable: {
      key: 'web_playable', 
      message: value => value ? '已标记为可播放' : '已标记为不可播放'
    }
  }

  const config = statusConfig[field]
  if (!config) {
    ElMessage.error('未知的状态字段')
    return
  }

  try {
    const updateData = { [config.key]: value }
    updateVideo(video.id, updateData)
    ElMessage.success(config.message(value))
  } catch (error) {
    console.error('更新视频状态失败:', error)
    ElMessage.error('更新失败')
  }
}

// 删除视频
const deleteVideo = async (videoId) => {
  await deleteVideoFromList(videoId)
}

// 显示标签对话框
const showTagDialog = (video) => {
  emit('show-tags-dialog', video)
}

// 从视频中移除标签
const removeVideoTag = async (videoId, tagId) => {
  try {
    await TagService.removeTagFromVideo(videoId, tagId)
    // 在本地更新视频的标签列表
    const videoIndex = videos.value.findIndex(video => video.id === videoId)
    if (videoIndex !== -1) {
      videos.value[videoIndex].tags = videos.value[videoIndex].tags.filter(tag => tag.id !== tagId)
    }
  } catch (error) {
    ElMessage.error('移除标签失败')
    console.error('移除标签失败:', error)
  }
}

// 处理缩略图加载错误
const handleThumbnailError = (event) => {
  event.target.src = '/default-thumbnail.png'
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 监听 viewMode 变化并保存到 localStorage
watch(viewMode, (newValue) => {
  localStorage.setItem('viewMode', newValue)
})

// 组件挂载时初始化数据
onMounted(async () => {
  // 如果没有props，则从路由初始化
  if (!props || Object.keys(props).length === 0) {
    initializeFromRoute()
  }
  await loadVideos()
})

// 暴露方法给父组件
defineExpose({
  loadVideos,
  updateVideoProgress,
  handleSearch,
  handleSortChange,
  refreshRandom
})
</script>

<style scoped>
.video-list {
  padding: 20px;
}

/* 网格视图样式 */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

/* 列表视图样式 */
.video-list-view {
  margin-bottom: 20px;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* 列表视图缩略图样式 */
.thumbnail-container {
  position: relative;
  width: 80px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
}

.list-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s;
}

.list-thumbnail:hover {
  transform: scale(1.05);
}

.progress-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(0, 0, 0, 0.3);
}

.progress-bar {
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
}

.progress-fill {
  height: 100%;
  background: #409eff;
  transition: width 0.3s;
}

.completed-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.7);
  border-radius: 50%;
  padding: 4px;
}

.completed-icon {
  color: #67c23a;
  font-size: 16px;
}

/* 文件名单元格样式 */
.filename-cell {
  cursor: pointer;
}

.filename-text {
  font-weight: 500;
  color: #409eff;
  margin-bottom: 4px;
  transition: color 0.2s;
}

.filename-text:hover {
  color: #66b1ff;
}

.file-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

/* 标签样式 */
.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.video-tag {
  margin: 0;
}

/* 操作按钮样式 */
.operation-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }
}
</style>

