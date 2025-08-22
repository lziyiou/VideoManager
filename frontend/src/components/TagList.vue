<template>
  <div class="tag-list-container">
    <div class="tag-list-header">
      <span class="tag-list-title">按标签过滤</span>
      <el-button 
        v-if="selectedTagIds.length > 0" 
        type="primary" 
        link 
        size="small" 
        @click="clearAllTags"
      >
        清除全部
      </el-button>
    </div>
    
    <div class="tag-categories">
      <div 
        v-for="(categoryData, categoryName) in groupedTags" 
        :key="categoryName"
        class="tag-category"
      >
        <div class="category-header">
          <span 
            class="category-name"
            :style="{ color: categoryData.category?.color || '#606266' }"
          >
            {{ categoryName }}
          </span>
          <span class="category-count">({{ categoryData.tags.length }})</span>
        </div>
        <div class="category-tags">
          <el-tag
            v-for="tag in categoryData.tags"
            :key="tag.id"
            :class="{ 'tag-selected': isTagSelected(tag.id) }"
            class="tag-item"
            @click="toggleTag(tag.id)"
            :effect="isTagSelected(tag.id) ? 'dark' : 'plain'"
            size="small"
            :style="{
              '--el-tag-text-color': isTagSelected(tag.id) 
                ? getTextColor(categoryData.category?.color) 
                : getUnselectedTextColor(categoryData.category?.color),
              '--el-tag-bg-color': isTagSelected(tag.id) 
                ? (categoryData.category?.color || '#409EFF') 
                : 'rgba(255, 255, 255, 0.8)',
              'border-color': categoryData.category?.color || '#409EFF',
              'border-width': '1px',
              'border-style': 'solid'
            }"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </div>
      <div v-if="Object.keys(groupedTags).length === 0" class="no-tags">
        暂无标签
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TagService from '@/services/tag_service'
import { ElMessage } from 'element-plus'

// 计算颜色的亮度
const getLuminance = (color) => {
  // 如果没有颜色，返回1表示亮色
  if (!color) return 1
  
  // 移除#号并转换为RGB
  const hex = color.replace('#', '')
  const r = parseInt(hex.substr(0, 2), 16) / 255
  const g = parseInt(hex.substr(2, 2), 16) / 255
  const b = parseInt(hex.substr(4, 2), 16) / 255
  
  // 计算亮度（基于人眼对RGB的敏感度）
  return 0.299 * r + 0.587 * g + 0.114 * b
}

// 根据背景色决定文字颜色
const getTextColor = (backgroundColor) => {
  const luminance = getLuminance(backgroundColor)
  // 调整阈值，使用更严格的对比度标准
  return luminance > 0.6 ? '#303133' : '#ffffff'
}

// 获取未选中状态的文字颜色
const getUnselectedTextColor = (categoryColor) => {
  if (!categoryColor) return '#409EFF'
  const luminance = getLuminance(categoryColor)
  // 对于未选中状态，确保有足够的对比度
  if (luminance > 0.7) {
    // 浅色背景，使用深色文字
    return '#303133'
  } else if (luminance < 0.3) {
    // 深色背景，使用浅色文字
    return '#ffffff'
  } else {
    // 中等亮度，使用原色但加深
    return categoryColor
  }
}

const props = defineProps({
  selectedTagIds: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['update:selectedTagIds'])

// 分组标签数据
const groupedTags = ref({})

// 加载标签数据
const loadTags = async () => {
  try {
    groupedTags.value = await TagService.getTagsGroupedByCategory()
  } catch (error) {
    console.error('加载标签失败:', error)
    ElMessage.error('加载标签失败')
  }
}

// 检查标签是否被选中
const isTagSelected = (tagId) => {
  return props.selectedTagIds.includes(tagId)
}

// 切换标签选中状态
const toggleTag = (tagId) => {
  const newSelectedTags = [...props.selectedTagIds]
  const index = newSelectedTags.indexOf(tagId)
  
  if (index === -1) {
    // 添加标签
    newSelectedTags.push(tagId)
  } else {
    // 移除标签
    newSelectedTags.splice(index, 1)
  }
  
  emit('update:selectedTagIds', newSelectedTags)
}

// 清除所有选中的标签
const clearAllTags = () => {
  emit('update:selectedTagIds', [])
}

// 组件挂载时加载标签
onMounted(() => {
  loadTags()
})
</script>

<style scoped>
.tag-list-container {
  width: 100%;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 8px;
  margin-top: 8px;
  background-color: #fff;
}

.tag-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.tag-list-title {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.tag-categories {
  max-height: 200px;
  overflow-y: auto;
}

.tag-category {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.tag-category:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.category-header {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  gap: 4px;
}

.category-name {
  font-size: 12px;
  font-weight: 500;
  color: #606266;
}

.category-count {
  font-size: 11px;
  color: #909399;
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-item {
  cursor: pointer;
  transition: all 0.3s;
  margin-right: 0;
  font-weight: 500;
}

.tag-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.tag-selected {
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.no-tags {
  width: 100%;
  text-align: center;
  color: #909399;
  font-size: 14px;
  padding: 10px 0;
}
</style>