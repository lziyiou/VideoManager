<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <h1>Video Manager - 视频管理系统</h1>
        
        <!-- 继续观看区域 -->
        <ContinueWatching 
          ref="continueWatchingRef"
          :on-refresh-video-list="refreshVideoList"
          @play-video="handlePlayVideo"
        />
        
        <!-- 搜索和过滤组件 -->
        <VideoSearchBar
          @search="handleSearch"
          @sort-change="handleSortChange"
          @view-mode-change="handleViewModeChange"
          @refresh-random="handleRefreshRandom"
        />
        
        <VideoList 
          ref="videoListRef"
          :search-keyword="searchKeyword"
          :only-favorites="onlyFavorites"
          :selected-tag-ids="selectedTagIds"
          :duration-filter="durationFilter"
          :sort-filter="sortFilter"
          :view-mode="viewMode"
          @video-updated="handleVideoUpdated"
          @play-video="handlePlayVideo"
          @show-tags-dialog="handleShowTagsDialog"
        />
      </el-col>
    </el-row>
  </div>
  
  <!-- 视频播放器 -->
  <VideoPlayer
    :visible="showPlayer"
    :video-id="currentVideo?.id?.toString() || ''"
    :title="currentVideo?.filename || ''"
    @thumbnail-updated="updateThumbnail"
    @update:visible="handlePlayerClose"
  />

  <!-- 标签管理对话框 -->
  <TagsDialog
    v-model="showTagsDialog"
    :video="selectedVideo"
    @tags-updated="handleTagsUpdated"
  />
</template>

<script setup>
import { ref } from 'vue'
import VideoList from '../components/VideoList.vue'
import VideoPlayer from '../components/VideoPlayer.vue'
import ContinueWatching from '../components/ContinueWatching.vue'
import TagsDialog from '../components/TagsDialog.vue'
import VideoSearchBar from '../components/VideoSearchBar.vue'

const showPlayer = ref(false)
const currentVideo = ref(null)
const videoListRef = ref(null)
const continueWatchingRef = ref(null)

// 标签对话框相关
const showTagsDialog = ref(false)
const selectedVideo = ref(null)

// 搜索和过滤状态
const searchKeyword = ref('')
const onlyFavorites = ref(false)
const selectedTagIds = ref([])
const durationFilter = ref('')
const sortFilter = ref('random')
const viewMode = ref('grid')

// 刷新VideoList的方法
const refreshVideoList = () => {
  if (videoListRef.value && videoListRef.value.loadVideos) {
    videoListRef.value.loadVideos()
  }
}

// 播放视频
const handlePlayVideo = (video) => {
  currentVideo.value = video
  showPlayer.value = true
}

// 更新单个视频的播放进度
const updateVideoProgress = async (videoId) => {
  // 调用ContinueWatching组件的更新方法
  if (continueWatchingRef.value && continueWatchingRef.value.updateVideoProgress) {
    continueWatchingRef.value.updateVideoProgress(videoId)
  }
}

// 处理VideoList组件的video-updated事件
const handleVideoUpdated = (eventData) => {
  // 当VideoList中的视频状态更新时，只更新对应视频的进度
  // 而不是刷新整个继续观看列表
  if (eventData && eventData.videoId) {
    updateVideoProgress(eventData.videoId)
  }
}

// 播放器关闭时更新对应视频进度
const handlePlayerClose = () => {
  const videoId = currentVideo.value?.id
  showPlayer.value = false
  currentVideo.value = null
  
  // 同时更新ContinueWatching和VideoList组件中对应视频的进度
  if (videoId) {
    // 更新ContinueWatching组件
    updateVideoProgress(videoId)
    
    // 更新VideoList组件
    if (videoListRef.value && videoListRef.value.updateVideoProgress) {
      videoListRef.value.updateVideoProgress(videoId)
    }
  }
}

// 显示标签对话框
const handleShowTagsDialog = (video) => {
  selectedVideo.value = video
  showTagsDialog.value = true
}

// 标签更新后的处理
const handleTagsUpdated = (updatedTags) => {
  // 刷新视频列表以更新标签信息
  if (videoListRef.value && videoListRef.value.loadVideos) {
    videoListRef.value.loadVideos()
  }
}

// 更新视频缩略图
const updateThumbnail = (videoId) => {
  // 刷新视频列表以更新缩略图
  if (videoListRef.value && videoListRef.value.loadVideos) {
    videoListRef.value.loadVideos()
  }
}

// 搜索处理
const handleSearch = (searchData) => {
  searchKeyword.value = searchData.keyword
  onlyFavorites.value = searchData.onlyFavorites
  selectedTagIds.value = searchData.selectedTagIds
  durationFilter.value = searchData.durationFilter
}

// 排序变化处理
const handleSortChange = (sortData) => {
  sortFilter.value = sortData.sortFilter
}

// 视图模式变化处理
const handleViewModeChange = (viewData) => {
  viewMode.value = viewData.viewMode
}

// 随机刷新处理
const handleRefreshRandom = () => {
  if (videoListRef.value && videoListRef.value.refreshRandom) {
    videoListRef.value.refreshRandom()
  }
}

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