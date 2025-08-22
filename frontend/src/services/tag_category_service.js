import apiClient from './api_client'

const TagCategoryService = {
  /**
   * 获取所有标签分类
   */
  async getAllCategories() {
    try {
      const response = await apiClient.get('/tag-categories/');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 根据ID获取标签分类
   * @param {number} categoryId - 分类ID
   */
  async getCategoryById(categoryId) {
    try {
      const response = await apiClient.get(`/tag-categories/${categoryId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 创建标签分类
   * @param {Object} categoryData - 分类数据
   */
  async createCategory(categoryData) {
    try {
      const response = await apiClient.post('/tag-categories/', categoryData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 更新标签分类
   * @param {number} categoryId - 分类ID
   * @param {Object} categoryData - 更新的分类数据
   */
  async updateCategory(categoryId, categoryData) {
    try {
      const response = await apiClient.put(`/tag-categories/${categoryId}`, categoryData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 删除标签分类
   * @param {number} categoryId - 分类ID
   */
  async deleteCategory(categoryId) {
    try {
      const response = await apiClient.delete(`/tag-categories/${categoryId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * 获取分类下的所有标签
   * @param {number} categoryId - 分类ID
   */
  async getCategoryTags(categoryId) {
    try {
      const response = await apiClient.get(`/tag-categories/${categoryId}/tags`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};

export default TagCategoryService;