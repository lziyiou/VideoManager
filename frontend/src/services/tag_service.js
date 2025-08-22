import apiClient from './api_client';

export default {
  /**
   * 获取所有标签
   */
  async getAllTags() {
    try {
      const response = await apiClient.get('/tags/');
      return response.data;
    } catch (error) {
      // console.error('获取标签失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 创建新标签
   * @param {string} name - 标签名称
   */
  async createTag(name) {
    try {
      const response = await apiClient.post('/tags/', { name });
      return response.data;
    } catch (error) {
      // console.error('创建标签失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 更新标签
   * @param {number} tagId - 标签ID
   * @param {string} name - 新标签名称
   */
  async updateTag(tagId, name) {
    try {
      const response = await apiClient.put(`/tags/${tagId}`, { name });
      return response.data;
    } catch (error) {
      // console.error('更新标签失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 删除标签
   * @param {number} tagId - 标签ID
   */
  async deleteTag(tagId) {
    try {
      const response = await apiClient.delete(`/tags/${tagId}`);
      return response.data;
    } catch (error) {
      // console.error('删除标签失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 获取视频的所有标签
   * @param {number} videoId - 视频ID
   */
  async getVideoTags(videoId) {
    try {
      const response = await apiClient.get(`/tags/video/${videoId}`);
      return response.data;
    } catch (error) {
      // console.error('获取视频标签失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 为视频添加标签
   * @param {number} videoId - 视频ID
   * @param {number} tagId - 标签ID
   */
  async addTagToVideo(videoId, tagId) {
    try {
      const response = await apiClient.post(`/tags/video/${videoId}/tag/${tagId}`);
      return response.data;
    } catch (error) {
      // console.error('添加标签到视频失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 从视频中移除标签
   * @param {number} videoId - 视频ID
   * @param {number} tagId - 标签ID
   */
  async removeTagFromVideo(videoId, tagId) {
    try {
      const response = await apiClient.delete(`/tags/video/${videoId}/tag/${tagId}`);
      return response.data;
    } catch (error) {
      // console.error('从视频移除标签失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 更新视频的标签（替换所有标签）
   * @param {number} videoId - 视频ID
   * @param {Array<number>} tagIds - 标签ID数组
   */
  async updateVideoTags(videoId, tagIds) {
    try {
      const response = await apiClient.put(`/tags/video/${videoId}/tags`, { tag_ids: tagIds });
      return response.data;
    } catch (error) {
      // console.error('更新视频标签失败:', error); // 由 apiClient 统一处理
      throw error;
    }
  },

  /**
   * 获取按分类分组的标签
   */
  async getTagsGroupedByCategory() {
    try {
      const response = await apiClient.get('/tags/grouped');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 将标签分配到分类
   * @param {number} tagId - 标签ID
   * @param {number|null} categoryId - 分类ID，null表示移除分类
   */
  async assignTagToCategory(tagId, categoryId) {
    try {
      const response = await apiClient.put(`/tags/${tagId}/category`, null, {
        params: { category_id: categoryId }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};