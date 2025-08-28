import apiClient from './api_client'

class SettingService {
  // 获取每页视频数量设置
  async getVideosPerPage() {
    try {
      const response = await apiClient.get('/settings/videos_per_page')
      return response.data.videos_per_page
    } catch (error) {
      console.error('获取每页视频数量设置失败:', error)
      // 如果获取失败，返回默认值
      return 20
    }
  }

  // 设置每页视频数量
  async setVideosPerPage(value) {
    const response = await apiClient.post('/settings/videos_per_page', {
      videos_per_page: value
    })
    return response.data
  }

  // 获取通用设置
  async getSetting(key) {
    const response = await apiClient.get(`/settings/${key}`)
    return response.data
  }

  // 设置通用设置
  async setSetting(key, value) {
    const response = await apiClient.post(`/settings/${key}`, {
      key,
      value
    })
    return response.data
  }

  // 获取根目录设置
  async getRootDirectory() {
    try {
      const response = await apiClient.get('/settings/root_directory')
      return response.data.root_directory
    } catch (error) {
      console.error('获取根目录设置失败:', error)
      throw error
    }
  }

  // 设置根目录
  async setRootDirectory(path) {
    const response = await apiClient.post('/settings/root_directory', {
      root_directory: path
    })
    return response.data
  }

  // 扫描视频
  async scanVideos() {
    const response = await apiClient.get('/videos/scan')
    return response.data
  }

  // 获取扫描进度
  async getScanProgress() {
    const response = await apiClient.get('/videos/scan/progress')
    return response.data
  }
}

export default new SettingService()