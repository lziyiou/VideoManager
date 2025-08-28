import { ref, computed, watch, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import VideoService from '../services/video_service'
import TagService from '../services/tag_service'

export function useVideoList(props = {}) {
  const route = useRoute()
  const router = useRouter()

  // 响应式数据
  const videos = ref([])
  const loading = ref(false)
  const searchKeyword = ref(props.searchKeyword || '')
  const onlyFavorites = ref(props.onlyFavorites || false)
  const selectedTagIds = ref(props.selectedTagIds || [])
  const allTags = ref([])
  const durationFilter = ref(props.durationFilter || '')
  const sortFilter = ref(props.sortFilter || 'random')
  const viewMode = ref(props.viewMode || 'grid')
  const currentPage = ref(1)
  // 注入全局设置
  const globalSettings = inject('globalSettings', { value: { videosPerPage: 20 } })
  const pageSize = ref(globalSettings.value.videosPerPage)
  
  // 监听全局设置变化
  watch(() => globalSettings.value.videosPerPage, (newValue) => {
    pageSize.value = newValue
  })
  const total = ref(0)
  const randomSeed = ref(Math.random())

  // 计算属性
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
  const hasVideos = computed(() => videos.value.length > 0)
  const isGridView = computed(() => viewMode.value === 'grid')
  const isListView = computed(() => viewMode.value === 'list')

  // 初始化数据
  const initializeFromRoute = () => {
    // 从路由参数初始化搜索条件
    searchKeyword.value = route.query.search || ''
    onlyFavorites.value = route.query.favorites === 'true'
    selectedTagIds.value = route.query.tags ? route.query.tags.split(',').map(Number) : []
    durationFilter.value = route.query.duration || ''
    sortFilter.value = route.query.sort || 'random'
    currentPage.value = parseInt(route.query.page) || 1
    
    // 从 localStorage 获取视图模式
    viewMode.value = localStorage.getItem('viewMode') || 'grid'
  }

  // 更新路由参数
  const updateRouteParams = () => {
    const queryParams = {
      search: searchKeyword.value || undefined,
      favorites: onlyFavorites.value ? 'true' : undefined,
      tags: selectedTagIds.value.length > 0 ? selectedTagIds.value.join(',') : undefined,
      duration: durationFilter.value || undefined,
      sort: sortFilter.value !== 'random' ? sortFilter.value : undefined,
      page: currentPage.value > 1 ? currentPage.value : undefined
    }

    // 过滤掉undefined值并合并现有查询参数
    const query = {
      ...route.query,
      ...Object.fromEntries(
        Object.entries(queryParams).filter(([_, value]) => value !== undefined)
      )
    }

    router.replace({ query })
  }

  // 加载视频列表
  const loadVideos = async () => {
    loading.value = true
    try {
      const params = {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value,
        keyword: searchKeyword.value,
        favorite: onlyFavorites.value,
        tags: selectedTagIds.value.join(','),
        duration: durationFilter.value,
        sort_by: sortFilter.value,
        seed: Math.floor(randomSeed.value * 1000000)
      }

      // 移除空值参数
      const cleanParams = Object.fromEntries(
        Object.entries(params).filter(([key, value]) => {
          if (value === '' || value === false) return false
          if (Array.isArray(value) && value.length === 0) return false
          return true
        })
      )

      const response = await VideoService.getVideos(cleanParams)
      videos.value = response.items
      total.value = response.total
      
      // 更新路由参数
      updateRouteParams()
    } catch (error) {
      console.error('加载视频列表失败:', error)
      ElMessage.error('加载视频列表失败')
    } finally {
      loading.value = false
    }
  }

  // 加载标签列表
  const loadTags = async () => {
    try {
      const response = await TagService.getAllTags()
      allTags.value = response
    } catch (error) {
      console.error('加载标签失败:', error)
    }
  }

  // 搜索处理
  const handleSearch = () => {
    currentPage.value = 1
    loadVideos()
  }

  // 排序变化处理
  const handleSortChange = () => {
    if (sortFilter.value === 'random') {
      randomSeed.value = Math.random()
    }
    currentPage.value = 1
    loadVideos()
  }

  // 重新随机
  const refreshRandom = () => {
    randomSeed.value = Math.random()
    loadVideos()
  }

  // 页面大小变化处理
  const handleSizeChange = (size) => {
    pageSize.value = size
    currentPage.value = 1
    loadVideos()
  }

  // 当前页变化处理（分页器使用）
  const handleCurrentChange = (page) => {
    currentPage.value = page
    loadVideos()
  }

  // 视图模式变化处理
  const handleViewModeChange = (mode) => {
    viewMode.value = mode
    localStorage.setItem('viewMode', mode)
  }

  // 更新单个视频进度
  const updateVideoProgress = async (videoId) => {
    try {
      const progress = await VideoService.getProgress(videoId)
      if (progress) {
        const video = videos.value.find(v => v.id === videoId)
        if (video) {
          // 更新视频的播放进度信息
          video.last_position = progress.last_position
          video.watch_progress = progress.watch_progress
          video.is_completed = progress.is_completed
          video.last_watched_at = progress.last_watched_at
        }
      }
    } catch (error) {
      console.error('更新视频播放进度失败:', error)
    }
  }

  // 删除视频
  const deleteVideo = async (videoId) => {
    try {
      await ElMessageBox.confirm(
        '确定要删除这个视频吗？此操作不可恢复。',
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )

      await VideoService.delete(videoId)
      
      // 从列表中移除视频
      const index = videos.value.findIndex(v => v.id === videoId)
      if (index !== -1) {
        videos.value.splice(index, 1)
        total.value--
      }
      
      ElMessage.success('视频删除成功')
      
      // 如果当前页没有视频了，回到上一页
      if (videos.value.length === 0 && currentPage.value > 1) {
        currentPage.value--
        loadVideos()
      }
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除视频失败:', error)
        ElMessage.error('删除视频失败')
      }
    }
  }

  // 更新视频信息
  const updateVideo = (videoId, updates) => {
    const video = videos.value.find(v => v.id === videoId)
    if (video) {
      Object.assign(video, updates)
    }
  }

  // 重命名视频
  const renameVideo = async (videoId, newFilename) => {
    try {
      const response = await VideoService.rename(videoId, newFilename)
      if (response.status === 200) {
        const video = videos.value.find(v => v.id === videoId)
        if (video) {
          video.filename = newFilename
        }
        return { success: true }
      }
    } catch (error) {
      return { success: false, error }
    }
  }

  // 监听props变化
  if (props) {
    watch(
      () => [props.searchKeyword, props.onlyFavorites, props.selectedTagIds, props.durationFilter, props.sortFilter, props.viewMode],
      ([newSearchKeyword, newOnlyFavorites, newSelectedTagIds, newDurationFilter, newSortFilter, newViewMode]) => {
        searchKeyword.value = newSearchKeyword || ''
        onlyFavorites.value = newOnlyFavorites || false
        selectedTagIds.value = newSelectedTagIds || []
        durationFilter.value = newDurationFilter || ''
        sortFilter.value = newSortFilter || 'random'
        viewMode.value = newViewMode || 'grid'
        // 当props变化时重新加载数据
        loadVideos()
      },
      { deep: true }
    )
  }

  // 监听路由变化
  watch(
    () => route.query,
    () => {
      if (!props) {
        initializeFromRoute()
        loadVideos()
      }
    },
    { immediate: false }
  )

  return {
    // 响应式数据
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
    
    // 计算属性
    totalPages,
    hasVideos,
    isGridView,
    isListView,
    
    // 核心方法
    initializeFromRoute,
    loadVideos,
    loadTags,
    
    // 事件处理方法
    handleSearch,
    handleSortChange,
    refreshRandom,
    handleSizeChange,
    handleCurrentChange,
    handleViewModeChange,
    
    // 数据操作方法
    updateVideoProgress,
    deleteVideo,
    updateVideo,
    renameVideo
  }
}