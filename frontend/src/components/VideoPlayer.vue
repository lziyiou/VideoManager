<template>
  <div class="video-player-container">
    <el-dialog
      :model-value="visible"
      @update:model-value="emit('update:visible', $event)"
      :title="title"
      width="80%"
      :before-close="handleClose"
      class="video-dialog"
      :close-on-click-modal="true"
      :close-on-press-escape="true"
      :show-close="false"
      destroy-on-close
    >
      <div class="video-player" v-loading="loading">
        <div ref="playerContainer" class="plyr-container"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watchEffect, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import Plyr from 'plyr'
import 'plyr/dist/plyr.css'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  videoId: {
    type: String,
    required: true
  },
  title: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:visible', 'thumbnail-updated'])

const playerContainer = ref(null)
const loading = ref(true)
const videoUrl = ref('')
let player = null
let isClosing = ref(false)  // 添加关闭状态标志
let progressUpdateTimer = null  // 播放进度更新定时器
let lastSavedPosition = 0  // 上次保存的播放位置
const PROGRESS_UPDATE_INTERVAL = 5000  // 每5秒更新一次播放进度
const MIN_PROGRESS_SAVE_THRESHOLD = 5  // 最小保存进度阈值（秒）

// 播放进度相关API调用
const updateVideoProgress = async (position, duration) => {
  try {
    const progress = duration > 0 ? (position / duration) * 100 : 0
    const isCompleted = progress >= 95 // 播放进度超过95%认为已完成
    
    await axios.put(`/api/videos/${props.videoId}/progress`, {
      last_position: position,
      watch_progress: progress,
      is_completed: isCompleted
    })
    
    lastSavedPosition = position
  } catch (error) {
    console.error('更新播放进度失败:', error)
  }
}

const getVideoProgress = async () => {
  try {
    const response = await axios.get(`/api/videos/${props.videoId}/progress`)
    return response.data
  } catch (error) {
    console.error('获取播放进度失败:', error)
    return null
  }
}

// 使用potplayer打开视频
const openInPotplayer = () => {
  try {
    const baseUrl = window.location.origin
    const videoUrl = `potplayer://${baseUrl}/api/videos/${props.videoId}/stream`.replace('localhost', '127.0.0.1')
    
    // 直接使用http协议，让PotPlayer打开网络流
    // PotPlayer可以直接打开http链接，无需特殊协议
    console.log('Opening video in PotPlayer:', videoUrl)
    window.open(videoUrl, '_blank')
    player.pause()
  } catch (error) {
    console.error('打开本地播放器失败:', error)
    ElMessageBox.alert(
      '打开本地播放器失败，请确保：\n' +
      '1. 已安装PotPlayer\n' +
      '2. PotPlayer已设置为默认视频播放器或与HTTP链接关联\n' +
      '3. 视频文件格式受支持\n' +
      '4. 如果浏览器阻止了弹出窗口，请允许弹出窗口',
      '播放器启动失败',
      {
        confirmButtonText: '确定',
        type: 'warning',
        duration: 5000
      }
    )
  }
}

// 初始化播放器
const initPlayer = () => {
  if (player) {
    player.destroy()
  }

  const video = document.createElement('video')
  // 添加playsinline和webkit-playsinline属性，防止iOS设备使用原生播放器
  video.setAttribute('playsinline', '')
  video.setAttribute('webkit-playsinline', 'true')
  video.setAttribute('x5-playsinline', 'true')
  video.setAttribute('crossorigin', 'anonymous')
  // 禁用iOS上的默认全屏行为
  video.setAttribute('x5-video-player-type', 'h5')
  video.setAttribute('x5-video-player-fullscreen', 'false')
  // 设置视频控制属性
  video.setAttribute('controlslist', 'nodownload')
  playerContainer.value.appendChild(video)

  // 创建自定义控件 - 截图按钮
  const screenshotButton = document.createElement('button')
  screenshotButton.type = 'button'
  screenshotButton.className = 'plyr__control plyr__control--pressed'
  screenshotButton.setAttribute('data-plyr', 'screenshot')
  screenshotButton.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-camera">
      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
      <circle cx="12" cy="13" r="4"></circle>
    </svg>
    <span class="plyr__tooltip">截图</span>
  `
  screenshotButton.addEventListener('click', takeScreenshot)

  // 创建自定义控件 - 本地播放器按钮
  const potplayerButton = document.createElement('button')
  potplayerButton.type = 'button'
  potplayerButton.className = 'plyr__control plyr__control--pressed'
  potplayerButton.setAttribute('data-plyr', 'potplayer')
  potplayerButton.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-external-link">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
      <polyline points="15 3 21 3 21 9"></polyline>
      <line x1="10" y1="14" x2="21" y2="3"></line>
    </svg>
    <span class="plyr__tooltip">本地播放</span>
  `
  potplayerButton.addEventListener('click', openInPotplayer)

  // 创建自定义控件 - 手动上传封面按钮
  const clipboardImage = document.createElement('button')
  clipboardImage.type = 'button'
  clipboardImage.className = 'plyr__control plyr__control--pressed'
  clipboardImage.setAttribute('data-plyr', 'upload-clipboard-image')
  clipboardImage.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-upload">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
      <polyline points="17 8 12 3 7 8"></polyline>
      <line x1="12" y1="3" x2="12" y2="15"></line>
    </svg>
    <span class="plyr__tooltip">上传封面</span>
  `
  clipboardImage.addEventListener('click', uploadClipboardImage)

  player = new Plyr(video, {
    autoplay: false, // 在iOS上自动播放通常会被阻止，设为false避免问题
    controls: [
      'play-large', // 添加大播放按钮，方便移动设备点击
      'play',
      'rewind',
      'fast-forward',
      'progress',
      'current-time',
      'duration',
      'mute',
      'volume',
      'captions',
      'settings',
      'pip',
      'airplay',
      'fullscreen'
    ],
    settings: ['quality', 'speed', 'loop'],
    quality: {
      default: 720, // 默认使用较低分辨率，适合移动设备
      options: [4320, 2880, 2160, 1440, 1080, 720, 576, 480, 360, 240]
    },
    speed: {
      selected: 1,
      options: [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]
    },
    seekTime: 5,
    keyboard: { focused: true, global: true },
    tooltips: { controls: true, seek: true },
    disableContextMenu: false,
    fullscreen: { enabled: true, fallback: true, iosNative: false }, // 使用自定义全屏而非iOS原生全屏
    clickToPlay: true, // 确保点击视频可以播放/暂停
    hideControls: true, // 自动隐藏控制栏
    resetOnEnd: false, // 播放结束后不重置到开始位置
    i18n: {
      restart: '重新播放',
      rewind: '后退 {seektime} 秒',
      play: '播放',
      pause: '暂停',
      fastForward: '前进 {seektime} 秒',
      seek: '跳转',
      seekLabel: '{currentTime} / {duration}',
      played: '已播放',
      buffered: '已缓冲',
      currentTime: '当前时间',
      duration: '持续时间',
      volume: '音量',
      mute: '静音',
      unmute: '取消静音',
      enableCaptions: '启用字幕',
      disableCaptions: '禁用字幕',
      enterFullscreen: '进入全屏',
      exitFullscreen: '退出全屏',
      frameTitle: '播放器',
      captions: '字幕',
      settings: '设置',
      pip: '画中画',
      menuBack: '返回上级菜单',
      speed: '播放速度',
      normal: '正常',
      quality: '视频质量',
      loop: '循环播放',
      start: '开始',
      end: '结束',
      all: '全部',
      reset: '重置',
      disabled: '禁用',
      enabled: '启用',
      advertisement: '广告',
      qualityBadge: {
        2160: '4K',
        1440: 'HD',
        1080: 'HD',
        720: 'HD',
        576: 'SD',
        480: 'SD'
      }
    }
  })

  // 事件监听
  player.on('ready', async () => {
    loading.value = false
    
    // 手动将自定义按钮添加到控件栏中
    const controlsContainer = player.elements.controls
    if (controlsContainer) {
      // 找到设置按钮，在它前面插入截图按钮和本地播放按钮
      const settingsButton = controlsContainer.querySelector('[data-plyr="settings"]')
      if (settingsButton && settingsButton.parentNode) {
        settingsButton.parentNode.insertBefore(potplayerButton, settingsButton)
        settingsButton.parentNode.insertBefore(screenshotButton, settingsButton)
        settingsButton.parentNode.insertBefore(clipboardImage, settingsButton)
      } else {
        // 如果找不到设置按钮，就添加到控件栏末尾
        controlsContainer.appendChild(potplayerButton)
        controlsContainer.appendChild(screenshotButton)
        controlsContainer.appendChild(clipboardImage)
      }
    }
    
    // 获取并恢复播放进度
    const progressData = await getVideoProgress()
    if (progressData && progressData.last_position > MIN_PROGRESS_SAVE_THRESHOLD && !progressData.is_completed) {
      // 显示断点续播提示
      const resumeTime = Math.floor(progressData.last_position)
      const minutes = Math.floor(resumeTime / 60)
      const seconds = resumeTime % 60
      const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`
      
      ElMessageBox.confirm(
        `检测到上次播放进度：${timeStr}，是否从上次位置继续播放？`,
        '断点续播',
        {
          confirmButtonText: '继续播放',
          cancelButtonText: '从头播放',
          type: 'info'
        }
      ).then(() => {
        // 用户选择继续播放
        player.currentTime = progressData.last_position
        ElMessage.success('已跳转到上次播放位置')
      }).catch(() => {
        // 用户选择从头播放，清除播放进度
        updateVideoProgress(0, player.duration || 0)
      })
    }
    
    // 检测是否为iOS设备
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
    
    // 尝试播放视频
    try {
      const playPromise = player.play()
      
      if (playPromise !== undefined) {
        playPromise.then(() => {
          // 自动播放成功
          console.log('视频自动播放成功')
        }).catch(error => {
          // 自动播放被阻止
          console.warn('视频自动播放被阻止:', error)
          
          if (isIOS) {
            // 在iOS上显示播放提示
            ElMessage.info({
              message: '点击视频区域开始播放',
              duration: 3000
            })
          }
        })
      }
    } catch (error) {
      console.error('播放器初始化错误:', error)
    }
  })
  
  // 添加播放进度跟踪事件监听
  player.on('play', () => {
    // 开始播放时启动进度更新定时器
    if (progressUpdateTimer) {
      clearInterval(progressUpdateTimer)
    }
    
    progressUpdateTimer = setInterval(() => {
      if (player && !player.paused && player.duration > 0) {
        const currentTime = player.currentTime
        const duration = player.duration
        
        // 只有当播放位置变化超过阈值时才更新
        if (Math.abs(currentTime - lastSavedPosition) >= MIN_PROGRESS_SAVE_THRESHOLD) {
          updateVideoProgress(currentTime, duration)
        }
      }
    }, PROGRESS_UPDATE_INTERVAL)
  })
  
  player.on('pause', () => {
    // 暂停时立即保存当前进度
    if (player && player.duration > 0) {
      updateVideoProgress(player.currentTime, player.duration)
    }
  })
  
  player.on('ended', () => {
    // 播放结束时标记为已完成
    if (player && player.duration > 0) {
      updateVideoProgress(player.duration, player.duration)
    }
    
    // 清除定时器
    if (progressUpdateTimer) {
      clearInterval(progressUpdateTimer)
      progressUpdateTimer = null
    }
  })
  
  player.on('seeked', () => {
    // 用户手动跳转时立即保存进度
    if (player && player.duration > 0) {
      updateVideoProgress(player.currentTime, player.duration)
    }
  })
  
  // 添加iOS设备上的交互事件处理
  if (/iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream) {
    player.on('enterfullscreen', () => {
      // 在iOS上进入全屏时锁定屏幕方向为横向
      try {
        if (screen.orientation && screen.orientation.lock) {
          screen.orientation.lock('landscape').catch(e => console.warn('无法锁定屏幕方向:', e))
        }
      } catch (error) {
        console.warn('屏幕方向API不可用:', error)
      }
    })
  }

  return player
}

// 截图功能实现
const takeScreenshot = () => {
  const videoElement = player.media
  if (!videoElement.readyState >= 2) {
    ElMessage.warning('视频正在加载中，请稍后再试')
    return
  }

  const canvas = document.createElement('canvas')
  canvas.width = videoElement.videoWidth
  canvas.height = videoElement.videoHeight
  const context = canvas.getContext('2d')
  context.drawImage(videoElement, 0, 0, canvas.width, canvas.height)

  canvas.toBlob(blob => {
    const formData = new FormData()
    const timestamp = new Date().getTime()
    formData.append('thumbnail', blob, `thumbnail_${timestamp}.jpg`)

    axios.put(`/api/videos/${props.videoId}/thumbnail`, formData)
      .then(() => {
        ElMessage.success('视频封面上传成功')
        emit('thumbnail-updated', props.videoId)
      })
      .catch((error) => {
        console.error('缩略图上传失败:', error)
        ElMessage.error('视频封面上传失败，请稍后重试')
      })
  }, 'image/jpeg')
}

async function uploadClipboardImage() {
  try {
    const clipboardItems = await navigator.clipboard.read();
    for (const item of clipboardItems) {
      if (item.types.includes('image/png') || item.types.includes('image/jpeg')) {
        const blob = await item.getType(item.types.find(t => t.startsWith('image/')));
        const formData = new FormData();
        const timestamp = new Date().getTime();
        formData.append('thumbnail', blob, `clipboard_thumbnail_${timestamp}.jpg`);

        await axios.put(`/api/videos/${props.videoId}/thumbnail`, formData);
        ElMessage.success('粘贴板图片上传成功');
        emit('thumbnail-updated', props.videoId);
        return;
      }
    }
    ElMessage.warning('剪贴板中没有图片，请先复制图片');
  } catch (error) {
    console.error('剪贴板读取失败:', error);
    ElMessage.error('读取剪贴板失败，请使用支持的浏览器（如Chrome）');
  }
}

// 处理关闭对话框
const handleClose = () => {
  isClosing.value = true  // 设置关闭状态标志
  
  // 清除播放进度更新定时器
  if (progressUpdateTimer) {
    clearInterval(progressUpdateTimer)
    progressUpdateTimer = null
  }
  
  if (player) {
    // 在关闭前保存最后的播放进度
    if (player.duration > 0 && player.currentTime > MIN_PROGRESS_SAVE_THRESHOLD) {
      updateVideoProgress(player.currentTime, player.duration)
    }
    
    // 暂停播放
    player.pause()
    // 清空视频源以停止加载
    player.source = {
      type: 'video',
      sources: []
    }
    // 重置播放器状态
    try {
      if (player.media) {
        player.media.src = ''
        player.media.load()
      }
    } catch (e) {
      console.error('重置播放器状态失败:', e)
    }
  }
  
  // 重置播放进度相关变量
  lastSavedPosition = 0
  
  // 清空视频URL
  videoUrl.value = ''
  // 清空播放器容器
  if (playerContainer.value) {
    playerContainer.value.innerHTML = ''
  }
  
  // 重置关闭状态标志
  setTimeout(() => {
    isClosing.value = false
  }, 100)
  
  emit('update:visible', false)
}

// 检测视频格式并返回适当的MIME类型
const detectVideoType = (url) => {
  const extension = url.split('?')[0].split('.').pop().toLowerCase()
  
  const mimeTypes = {
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'ogg': 'video/ogg',
    'mov': 'video/quicktime',
    'mkv': 'video/x-matroska',
    'm3u8': 'application/x-mpegURL'
  }
  
  return mimeTypes[extension] || 'video/mp4'
}

// 加载视频
const loadVideo = (videoId, retryCount = 0) => {
  if (!videoId || !playerContainer.value) return
  
  // 重置关闭状态标志
  isClosing.value = false
  loading.value = true
  const timestamp = new Date().getTime()
  videoUrl.value = `/api/videos/${videoId}/stream?t=${timestamp}`
  
  playerContainer.value.innerHTML = ''
  const newPlayer = initPlayer()
  
  // 检测是否为iOS设备
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
  
  newPlayer.source = {
    type: 'video',
    title: props.title,
    sources: [{
      src: videoUrl.value,
      // 对于iOS设备，优先使用MP4格式
      type: isIOS ? 'video/mp4' : detectVideoType(videoUrl.value),
      // 添加size属性以帮助播放器选择合适的分辨率
      size: 720
    }]
  }
  
  newPlayer.on('error', (error) => {
    // 如果正在关闭对话框，不显示错误信息和重试，也不输出控制台错误
    if (isClosing.value) {
      return
    }
    
    console.error('视频加载错误:', error)
    
    if (retryCount < 2) {
      ElMessage.warning(`视频加载失败，正在进行第${retryCount + 1}次重试...`)
      setTimeout(() => loadVideo(videoId, retryCount + 1), 1500)
    } else {
      loading.value = false
      ElMessage.error({
        message: '视频加载失败，请检查视频格式或网络连接',
        duration: 5000
      })
    }
  })
}

// 监听props变化
watchEffect(() => {
  if (props.visible && props.videoId) {
    loadVideo(props.videoId)
  }
})

// 组件卸载时清理
onBeforeUnmount(() => {
  // 清除播放进度更新定时器
  if (progressUpdateTimer) {
    clearInterval(progressUpdateTimer)
    progressUpdateTimer = null
  }
  
  if (player) {
    // 在卸载前保存最后的播放进度
    if (player.duration > 0 && player.currentTime > MIN_PROGRESS_SAVE_THRESHOLD) {
      updateVideoProgress(player.currentTime, player.duration)
    }
    
    // 先暂停播放并清空源
    player.pause()
    player.source = {
      type: 'video',
      sources: []
    }
    // 重置媒体元素
    try {
      if (player.media) {
        player.media.src = ''
        player.media.load()
      }
    } catch (e) {
      console.error('重置媒体元素失败:', e)
    }
    // 销毁播放器实例
    player.destroy()
    player = null
  }
  
  // 重置播放进度相关变量
  lastSavedPosition = 0
  
  // 清空视频URL和播放器容器
  videoUrl.value = ''
  if (playerContainer.value) {
    playerContainer.value.innerHTML = ''
  }
})
</script>

<style scoped>
.video-player-container :deep(.el-dialog) {
  display: flex;
  flex-direction: column;
  margin: 0 !important;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  max-height: 90vh;
  max-width: 90vw;
  height: 90vh;
}

.video-player-container :deep(.el-dialog__title) {
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
}

.video-player-container :deep(.el-dialog__body) {
  flex: 1;
  overflow: hidden;
  padding: 0;
  height: calc(100% - 54px);
}

.video-player {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #000;
}

.plyr-container {
  width: 100%;
  height: 100%;
  max-height: 100%;
}

:deep(.plyr),
:deep(.plyr--video),
:deep(.plyr__video-wrapper) {
  width: 100%;
  height: 100%;
}

:deep(.plyr--video) {
  background: transparent;
}

:deep(.plyr video) {
  width: 100%;
  height: 100%;
  object-fit: contain;
  /* 确保iOS设备上视频正确显示 */
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}

/* 增强移动设备上的控制按钮大小和触摸区域 */
:deep(.plyr__controls button) {
  padding: 8px;
}

:deep(.plyr__control--overlaid) {
  padding: 20px;
  background: rgba(0, 0, 0, 0.6);
}

/* 确保在iOS设备上全屏模式正常工作 */
:deep(.plyr--fullscreen-active) {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  height: 100% !important;
  width: 100% !important;
  background: #000;
  z-index: 10000;
}

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: center;
}
</style>
