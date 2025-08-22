<template>
  <div class="video-list">
    <div class="video-list-header">
      <div class="top-controls">
        <div class="left-section">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索视频文件"
            class="search-input"
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-switch
            v-model="onlyFavorites"
            class="favorite-filter"
            @change="handleSearch"
            active-text="只看收藏"
            inactive-text=""
          >
          </el-switch>
          
          <el-select
            v-model="durationFilter"
            placeholder="视频时长"
            clearable
            @change="handleSearch"
            class="duration-filter"
          >
            <el-option
              v-for="option in durationOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>

          <el-select
            v-model="sortFilter"
            placeholder="排序方式"
            clearable
            @change="handleSortChange"
            class="sort-filter"
          >
            <el-option
              v-for="option in sortOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          
          <el-button 
            v-if="sortFilter === 'random'"
            @click="refreshRandom"
            :icon="Refresh"
            size="small"
            type="primary"
            plain
            class="refresh-random-btn"
          >
            重新随机
          </el-button>
        </div>
        <div class="right-section">
          <el-radio-group v-model="viewMode" size="large">
            <el-radio-button label="list">
              <el-icon><List /></el-icon>
            </el-radio-button>
            <el-radio-button label="grid">
              <el-icon><Grid /></el-icon>
            </el-radio-button>
          </el-radio-group>
        </div>
      </div>
      
      <!-- 标签过滤组件 -->
      <div class="tag-filter-container">
        <TagList
          :all-tags="allTags"
          v-model:selected-tag-ids="selectedTagIds"
          @update:selected-tag-ids="handleSearch"
        />
      </div>
    </div>

    <div v-loading="loading">
      <!-- 列表视图 -->
      <el-table
        v-if="viewMode === 'list'"
        :data="videos"
        style="width: 100%"
      >
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长" width="120">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="100">
          <template #default="{ row }">
            <div class="video-tags">
              <el-tag 
                v-for="tag in row.tags" 
                :key="tag.id" 
                size="small" 
                class="video-tag"
                closable
                @close="removeTagFromVideo(row.id, tag.id)"
              >
                {{ tag.name }}
              </el-tag>
              <el-button 
                type="primary" 
                size="small" 
                circle 
                plain 
                @click="handleShowTagsDialog(row)"
              >
                <el-icon><Plus /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <div class="operation-buttons">
              <el-button link type="primary" @click="handlePlay(row)">
                <el-icon><VideoPlay /></el-icon>
                播放
              </el-button>
              <el-button link type="primary" @click="handleEdit(row)">
                <el-icon :size="16"><Edit style="color: #409EFF; transform: scale(1.1);" /></el-icon>
                编辑
              </el-button>
              <el-button 
                link 
                :type="row.is_favorite ? 'danger' : 'primary'" 
                @click="updateVideoStatus(row, 'favorite', !row.is_favorite)"
              >
                <el-icon :size="16">
                  <StarFilled v-if="row.is_favorite" style="color: #F56C6C; transform: scale(1.1); border-radius: 50%;" />
                  <Star v-else style="color: #409EFF; transform: scale(1.1); border-radius: 50%;" />
                </el-icon>
                {{ row.is_favorite ? '取消收藏' : '收藏' }}
              </el-button>
              <el-button 
                link 
                :type="!row.web_playable ? 'danger' : 'primary'" 
                :style="!row.web_playable ? 'font-weight: bold; text-decoration: underline;' : ''"
                @click="updateVideoStatus(row, 'webPlayable', !row.web_playable)"
              >
                <el-icon :size="16">
                  <WarningFilled v-if="!row.web_playable" style="color: #F56C6C; transform: scale(1.1);" />
                  <Warning v-else style="color: #409EFF; transform: scale(1.1);" />
                </el-icon>
                {{ row.web_playable ? '标记无法播放' : '标记可以播放' }}
              </el-button>
              <el-button link type="danger" @click="handleDelete(row)">
                <el-icon :size="16"><Delete style="color: #F56C6C; transform: scale(1.1);" /></el-icon>
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 网格视图 -->
      <div v-else class="video-grid">
        <el-card
          v-for="video in videos"
          :key="video.id"
          class="video-card"
          shadow="hover"
          @click="handlePlay(video)"
        >
          <div class="video-thumbnail" :style="{
            backgroundImage: `url(/api/videos/${video.id}/thumbnail?t=${video.updated_at || Date.now()})`
          }">
            <el-icon class="play-icon"><VideoPlay /></el-icon>
          </div>
          <div class="video-info">
            <div class="video-title" :title="video.filename">{{ video.filename }}</div>
            <div class="video-meta">
              <span>{{ formatFileSize(video.size) }}</span>
              <span>{{ formatDuration(video.duration) }}</span>
              <div class="video-actions">
                <el-button link type="primary" @click.stop="handleEdit(video)">
                <el-icon :size="16"><Edit style="color: #409EFF; transform: scale(1.1);" /></el-icon>
              </el-button>
                <el-button 
                  link 
                  :type="video.is_favorite ? 'danger' : 'primary'" 
                  @click.stop="updateVideoStatus(video, 'favorite', !video.is_favorite)"
                >
                  <el-icon :size="16">
                <StarFilled v-if="video.is_favorite" style="color: rgb(255, 183, 0); transform: scale(1.1); border-radius: 50%;" />
                <Star v-else style="color: #409EFF; transform: scale(1.1); border-radius: 50%;" />
              </el-icon>
                </el-button>
                <el-button 
                  link 
                  :type="!video.web_playable ? 'danger' : 'primary'" 
                  :style="!video.web_playable ? 'font-weight: bold; text-decoration: underline;' : ''"
                  @click.stop="updateVideoStatus(video, 'webPlayable', !video.web_playable)"
                >
                  <el-icon :size="16">
                <WarningFilled v-if="!video.web_playable" style="color: #F56C6C; transform: scale(1.1);" />
                <Warning v-else style="color: #409EFF; transform: scale(1.1);" />
              </el-icon>
                </el-button>
                <el-button link type="danger" @click.stop="handleDelete(video)">
                <el-icon :size="16"><Delete style="color: #F56C6C; transform: scale(1.1);" /></el-icon>
              </el-button>
              </div>
            </div>
            <div class="video-tags" v-if="video.tags && video.tags.length > 0">
              <el-tag 
                v-for="tag in video.tags" 
                :key="tag.id" 
                size="small" 
                class="video-tag"
                @click.stop
                closable
                @close.stop="removeTagFromVideo(video.id, tag.id)"
              >
                {{ tag.name }}
              </el-tag>
              <el-button 
                type="primary" 
                size="small" 
                circle 
                plain 
                class="add-tag-btn"
                @click.stop="handleShowTagsDialog(video)"
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
                @click.stop="handleShowTagsDialog(video)"
              >
                <el-icon><Plus /></el-icon> 添加标签
              </el-button>
            </div>
          </div>
        </el-card>
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

  <!-- 视频播放器 -->
  <VideoPlayer
    v-model:visible="showPlayer"
    :video-id="currentVideo?.id"
    :title="currentVideo?.filename"
    @thumbnail-updated="updateThumbnail"
  />

  <!-- 标签管理对话框 -->
  <TagsDialog
    v-model="showTagsDialog"
    :video="selectedVideo"
    @tags-updated="handleTagsUpdated"
  />
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Search, Refresh, VideoPlay, List, Grid, Plus, Edit, Star, StarFilled, Warning, WarningFilled, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// import axios from 'axios'; // Replaced by apiClient
import apiClient from '../services/api_client';
import { useRoute, useRouter } from 'vue-router'
import VideoPlayer from './VideoPlayer.vue'
import TagsDialog from './TagsDialog.vue'
import TagList from './TagList.vue'
import TagService from '../services/tag_service'
import VideoService from '../services/video_service'

const route = useRoute()
const router = useRouter()

const videos = ref([])
const loading = ref(false)
const searchKeyword = ref(route.query.keyword || '')
const currentPage = ref(parseInt(route.query.page) || 1)
const pageSize = ref(parseInt(route.query.size) || 12)
const total = ref(0)
const viewMode = ref(localStorage.getItem('viewMode') || 'grid') // 'list' 或 'grid'

// 过滤相关
const onlyFavorites = ref(route.query.favorite === 'true')
const selectedTagIds = ref(route.query.tags ? route.query.tags.split(',').map(Number) : [])
const allTags = ref([])
const durationFilter = ref(route.query.duration || '')
const durationOptions = [
  { label: '全部', value: '' },
  { label: '短视频', value: 'short' },
  { label: '长视频', value: 'long' }
]
const sortFilter = ref(route.query.sort_by || 'random')
// 如果是随机排序但没有种子，则生成一个初始种子
const randomSeed = ref(
  route.query.seed ? parseInt(route.query.seed) : 
  (route.query.sort_by === 'random' || (!route.query.sort_by)) ? Date.now() : null
)
const sortOptions = [
  { label: '文件名', value: 'filename' },
  { label: '时长', value: 'duration' },
  { label: '添加时间', value: 'created_at' },
  { label: '随机', value: 'random' },
]

// 更新视频标记状态
const updateVideoStatus = async (video, type, value) => {
  try {
    if (type === 'favorite') {
      await VideoService.updateFavorite(video.id, value)
      video.is_favorite = value ? 1 : 0
    } else if (type === 'webPlayable') {
      await VideoService.updateWebPlayable(video.id, value)
      video.web_playable = value ? 1 : 0
    }
    ElMessage.success('更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
    console.error('更新视频状态失败:', error)
  }
}

// 视频播放相关
const showPlayer = ref(false)
const currentVideo = ref(null)

// 标签管理相关
const showTagsDialog = ref(false)
const selectedVideo = ref(null)

// 更新视频缩略图 (现在由后端管理时间戳, 前端只需刷新列表)
const updateThumbnail = (videoId) => {
  // 找到需要更新的视频
  const videoIndex = videos.value.findIndex(video => video.id === videoId)
  if (videoIndex !== -1) {
    // 更新视频的时间戳
    videos.value[videoIndex].updated_at = Date.now()
  }
}

// 修改文件名
const handleEdit = async (video) => {
  try {
    const ext = video.filename.split('.').pop()
    const oldName = video.filename.replace('.'+ext, '')
    const { value: newFilename } = await ElMessageBox.prompt('请输入新的文件名', '重命名', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: oldName,
      inputValidator: (value) => {
        if (!value) {
          return '文件名不能为空'
        }
        if (value.length > 255) {
          return '文件名不能超过255个字符'
        }
        return true
      },
      inputErrorMessage: '文件名格式不正确'
    })

    const newName = newFilename.trim() + '.' + ext

    if (newName !== video.filename) {
      try {
        const response = await VideoService.rename(video.id, newName)
        
        if (response.status == 200) {  // 假设后端返回 { success: true } 结构
          video.filename = newName;  // 后端确认成功，才更新前端
          ElMessage.success('重命名成功！');
        }
      } catch (error) {
        console.error('重命名失败:', error);
        if (error.response?.data?.detail) {
          // 显示后端返回的详细错误信息
          ElMessage({
            message: error.response.data.detail,
            type: 'error',
            duration: 5000,  // 延长显示时间到5秒
            showClose: true  // 显示关闭按钮
          });
        } else {
          ElMessage.error('重命名失败，请稍后再试。');
        }
      }
    }
  } catch (error) {
    if (error.message !== 'cancel') {
      console.error('重命名失败:', error)
    }
  }
}

// 监听 viewMode 变化并保存到 localStorage
watch(viewMode, (newValue) => {
  localStorage.setItem('viewMode', newValue)
})

// 更新路由参数
const updateRouteQuery = () => {
  router.push({
    query: {
      ...route.query,
      keyword: searchKeyword.value || undefined,
      page: currentPage.value,
      size: pageSize.value,
      favorite: onlyFavorites.value ? 'true' : undefined,
      tags: selectedTagIds.value.length > 0 ? selectedTagIds.value.join(',') : undefined,
      duration: durationFilter.value || undefined,
      sort_by: sortFilter.value || 'random',
      seed: randomSeed.value || undefined
    }
  })
}

// 处理排序变化
const handleSortChange = () => {
  if (sortFilter.value === 'random') {
    // 当选择随机排序时，生成新的随机种子
    randomSeed.value = Date.now()
  } else {
    // 非随机排序时清除种子
    randomSeed.value = null
  }
  handleSearch()
}

// 重新随机
const refreshRandom = () => {
  if (sortFilter.value === 'random') {
    randomSeed.value = Date.now()
    handleSearch()
  }
}

// 加载视频列表
const loadVideos = async () => {
  try {
    loading.value = true
    const skip = (currentPage.value - 1) * pageSize.value
    
    // 构建查询参数
    const params = {
      skip,
      limit: pageSize.value
    }
    
    // 添加收藏过滤参数
    if (onlyFavorites.value) {
      params.favorite = true
    }
    
    // 添加标签过滤参数
    if (selectedTagIds.value.length > 0) {
      params.tags = selectedTagIds.value.join(',')
    }
    
    // 添加时长过滤参数
    if (durationFilter.value) {
      params.duration = durationFilter.value
    }

    // 添加排序参数
    if (sortFilter.value) {
      params.sort_by = sortFilter.value
      // 如果是随机排序，使用固定的随机种子
      if (sortFilter.value === 'random' && randomSeed.value) {
        params.seed = randomSeed.value
      }
    }
    
    let response
    if (searchKeyword.value) {
      // 搜索模式
      params.keyword = searchKeyword.value
      response = await VideoService.getVideos(params)
    } else {
      // 列表模式
      response = await VideoService.getVideos(params)
    }
    
    videos.value = response.items // 使用返回的视频列表数据
    total.value = response.total // 使用返回的总记录数
  } catch (error) {
    ElMessage.error('加载视频列表失败')
    console.error('加载视频列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = async () => {
  currentPage.value = 1
  updateRouteQuery()
}

// 分页处理
const handleSizeChange = async (val) => {
  pageSize.value = val
  updateRouteQuery()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  updateRouteQuery()
}

// 播放视频
const handlePlay = (video) => {
  currentVideo.value = video
  showPlayer.value = true
}

// 显示标签管理对话框
const handleShowTagsDialog = (video) => {
  selectedVideo.value = video
  showTagsDialog.value = true
}

// 标签更新后重新加载视频列表
const handleTagsUpdated = (updatedTags) => {
  if (selectedVideo.value) {
    const videoIndex = videos.value.findIndex(video => video.id === selectedVideo.value.id)
    if (videoIndex !== -1) {
      videos.value[videoIndex].tags = updatedTags
    }
  }
}

// 移除视频标签
const removeTagFromVideo = async (videoId, tagId) => {
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

// 格式化文件大小
const formatFileSize = (size) => {
  if (size >= 1024) {
    return `${(size / 1024).toFixed(2)} GB`
  }
  return `${size.toFixed(2)} MB`
}

// 删除视频
const handleDelete = async (video) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除视频 "${video.filename}" 吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await VideoService.delete(video.id)
    ElMessage.success('视频删除成功')
    // 从列表中移除视频
    videos.value = videos.value.filter(v => v.id !== video.id)
    // 如果当前页没有数据了，且不是第一页，则返回上一页
    if (videos.value.length === 0 && currentPage.value > 1) {
      currentPage.value -= 1
    }
    loadVideos() // 重新加载数据，确保分页正确
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除视频失败')
      console.error('删除视频失败:', error)
    }
  }
}

// 格式化视频时长
const formatDuration = (duration) => {
  const hours = Math.floor(duration / 3600)
  const minutes = Math.floor((duration % 3600) / 60)
  const seconds = Math.floor(duration % 60)
  // 如果小时数为0，则只显示分钟和秒
  if (hours === 0) {
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

// 监听路由参数变化
watch(
  () => route.query,
  () => {
    const { keyword, page, size, favorite, tags, sort_by, duration, seed } = route.query
    searchKeyword.value = keyword || ''
    currentPage.value = parseInt(page) || 1
    pageSize.value = parseInt(size) || 12
    onlyFavorites.value = favorite === 'true'
    selectedTagIds.value = tags ? tags.split(',').map(Number) : []
    sortFilter.value = sort_by || 'random'
    durationFilter.value = duration || ''
    randomSeed.value = seed ? parseInt(seed) : null
    loadVideos()
  }
)

// 加载所有标签
const loadAllTags = async () => {
  try {
    const response = await TagService.getAllTags()
    allTags.value = response
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

onMounted(() => {
  loadAllTags()
  // 如果是随机排序且生成了新的种子，更新URL
  if (sortFilter.value === 'random' && randomSeed.value && !route.query.seed) {
    updateRouteQuery()
  } else {
    loadVideos()
  }
})
</script>

<style scoped>
.operation-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.video-actions {
  margin-left: auto;
}

.video-list {
  padding: 12px;
}

.refresh-random-btn {
  margin-left: 8px;
  font-size: 12px;
}

.video-list-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
}

.top-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.left-section {
  display: flex;
  gap: 12px;
}

.search-input {
  width: 300px;
}

.tag-filter-container {
  width: 100%;
}

.favorite-filter {
  margin-left: 12px;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  padding: 20px 0;
}

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
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
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

.duration-filter {
  width: 180px;
  margin-left: 12px;
}

.sort-filter {
  width: 130px;
  margin-left: 12px;
}
</style>

