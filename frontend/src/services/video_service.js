import apiClient from './api_client';

export default {
  /**
   * 修改文件名
   * @param {number} videoId - 视频ID
   * @param {string} newName - 新的文件名
   */
  async rename(videoId, newName) {
    try {
      const response = await apiClient.put(`/videos/${videoId}?new_name=${newName}`);
      return response;
    } catch (error) {
      // console.error('更新视频文件名失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 删除视频
   * @param {number} videoId - 视频ID
   */
  async delete(videoId) {
    try {
      const response = await apiClient.delete(`/videos/${videoId}`);
      return response.data; 
    } catch (error) {
      // console.error('删除视频失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 获取视频列表
   * @param {Object} params - 查询参数
   * @param {number} params.skip - 跳过的记录数
   * @param {number} params.limit - 返回的记录数
   * @param {boolean} [params.favorite] - 是否只返回收藏的视频
   * @param {string} [params.tags] - 标签ID列表，逗号分隔
   */
  async getVideos(params) {
    try {
      const response = await apiClient.get('/videos/list', { params });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 搜索视频
   * @param {Object} params - 查询参数
   * @param {string} params.keyword - 搜索关键词
   * @param {number} params.skip - 跳过的记录数
   * @param {number} params.limit - 返回的记录数
   * @param {boolean} [params.favorite] - 是否只返回收藏的视频
   * @param {string} [params.tags] - 标签ID列表，逗号分隔
   */
  async searchVideos(params) {
    try {
      const response = await apiClient.get('/videos/search', { params });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 更新视频收藏状态
   * @param {number} videoId - 视频ID
   * @param {boolean} isFavorite - 是否收藏
   */
  async updateFavorite(videoId, isFavorite) {
    try {
      const response = await apiClient.post(`/videos/${videoId}/favorite`, null, {
        params: { is_favorite: isFavorite }
      });
      return response.data;
    } catch (error) {
      // console.error('更新视频收藏状态失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 更新视频网页播放状态
   * @param {number} videoId - 视频ID
   * @param {boolean} webPlayable - 是否可以网页播放
   */
  async updateWebPlayable(videoId, webPlayable) {
    try {
      const response = await apiClient.post(`/videos/${videoId}/web_playable`, null, {
        params: { web_playable: webPlayable }
      });
      return response.data;
    } catch (error) {
      // console.error('更新视频网页播放状态失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

};