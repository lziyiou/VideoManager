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
   * @param {string} [params.keyword] - 搜索关键词
   * @param {boolean} [params.favorite] - 是否只返回收藏的视频
   * @param {string} [params.tags] - 标签ID列表，逗号分隔
   * @param {string} [params.duration] - 时长过滤
   * @param {string} [params.sort_by] - 排序方式
   * @param {number} [params.seed] - 随机种子
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

  /**
   * 获取继续观看的视频列表
   * @param {number} [limit=10] - 返回的记录数
   */
  async getContinueWatching(limit = 10) {
    try {
      const response = await apiClient.get('/videos/continue-watching', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 获取最近观看的视频列表
   * @param {number} [limit=10] - 返回的记录数
   */
  async getRecentlyWatched(limit = 10) {
    try {
      const response = await apiClient.get('/videos/recently-watched', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 更新视频播放进度
   * @param {number} videoId - 视频ID
   * @param {Object} progressData - 播放进度数据
   * @param {number} progressData.last_position - 最后播放位置（秒）
   * @param {number} progressData.watch_progress - 观看进度（0-1）
   * @param {boolean} progressData.is_completed - 是否已完成观看
   */
  async updateProgress(videoId, progressData) {
    try {
      const response = await apiClient.put(`/videos/${videoId}/progress`, progressData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 获取视频播放进度
   * @param {number} videoId - 视频ID
   */
  async getProgress(videoId) {
    try {
      const response = await apiClient.get(`/videos/${videoId}/progress`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 删除视频播放进度
   * @param {number} videoId - 视频ID
   */
  async deleteProgress(videoId) {
    try {
      const response = await apiClient.delete(`/videos/${videoId}/progress`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 批量删除播放进度
   * @param {number[]} videoIds - 视频ID列表
   */
  async deleteMultipleProgress(videoIds) {
    try {
      const response = await apiClient.delete('/videos/progress/batch', {
        data: videoIds
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 上传视频缩略图
   * @param {number} videoId - 视频ID
   * @param {File} thumbnailFile - 缩略图文件
   */
  async uploadThumbnail(videoId, thumbnailFile) {
    try {
      const formData = new FormData();
      formData.append('thumbnail', thumbnailFile);
      const response = await apiClient.put(`/videos/${videoId}/thumbnail`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

};