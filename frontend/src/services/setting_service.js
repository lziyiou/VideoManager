import apiClient from './api_client'

class SettingService {
  // 获取每页视频数量设置
  async getVideosPerPage() {
    try {
      const response = await apiClient.get('/api/settings/videos_per_page')
      return response.data.videos_per_page
    } catch (error) {
      console.error('获取每页视频数量设置失败:', error)
      // 如果获取失败，返回默认值
      return 20
    }
  }

  // 设置每页视频数量
  async setVideosPerPage(value) {
    const response = await apiClient.post('/api/settings/videos_per_page', {
      videos_per_page: value
    })
    return response.data
  }

  // 获取通用设置
  async getSetting(key) {
    const response = await apiClient.get(`/api/settings/${key}`)
    return response.data
  }

  // 设置通用设置
  async setSetting(key, value) {
    const response = await apiClient.post(`/api/settings/${key}`, {
      key,
      value
    })
    return response.data
  }
}

export default new SettingService()