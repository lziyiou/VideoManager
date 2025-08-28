<template>
  <el-dialog
    v-model="dialogVisible"
    title="管理标签"
    width="30%"
    :show-close="false"
    :close-on-click-modal="true"
  >
    <div class="tags-container">
      <div class="current-tags" v-if="currentTags.length > 0">
        <h4>当前标签</h4>
        <div class="tags-list">
          <el-tag
            v-for="tag in currentTags"
            :key="tag.id"
            closable
            size="small"
            class="tag-item"
            @close="removeTag(tag)"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </div>
      
      <div class="available-tags">
        <h4>可用标签</h4>
        <div class="categories-container">
          <div 
            v-for="(categoryData, categoryName) in groupedAvailableTags" 
            :key="categoryName"
            class="category-group"
          >
            <div class="category-header">
              <el-tag 
                v-if="categoryData.category"
                :style="{ color: categoryData.category?.color || '#606266' }"
                size="small"
                class="category-tag"
              >
                {{ categoryName }}
              </el-tag>
              <span v-else class="category-name">{{ categoryName }}</span>
            </div>
            <div class="tags-list">
              <el-tag
                v-for="tag in categoryData.tags"
                :key="tag.id"
                size="small"
                class="tag-item"
                @click="addTag(tag)"
              >
                {{ tag.name }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import TagService from '../services/tag_service'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  video: {
    type: Object,
    required: false,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'tags-updated'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const allTags = ref([])
const groupedTags = ref({})
const currentTags = computed(() => props.video?.tags || [])
const availableTags = computed(() => {
  return allTags.value.filter(tag => 
    !currentTags.value.some(currentTag => currentTag.id === tag.id)
  )
})

// 按分类分组可用标签
const groupedAvailableTags = computed(() => {
  const grouped = {}
  
  availableTags.value.forEach(tag => {
    const categoryName = tag.category ? tag.category.name : '未分类'
    
    if (!grouped[categoryName]) {
      grouped[categoryName] = {
        category: tag.category,
        tags: []
      }
    }
    
    grouped[categoryName].tags.push(tag)
  })
  
  return grouped
})

// 加载所有标签
const loadTags = async () => {
  try {
    const tags = await TagService.getAllTags()
    allTags.value = tags
    
    // 也可以使用分组接口
    const grouped = await TagService.getTagsGroupedByCategory()
    groupedTags.value = grouped
  } catch (error) {
    ElMessage.error('加载标签失败')
    console.error('加载标签失败:', error)
  }
}

// 添加标签
const addTag = async (tag) => {
  if (!props.video) return
  
  try {
    await TagService.addTagToVideo(props.video.id, tag.id)
    // 更新本地标签数组
    props.video.tags = [...currentTags.value, tag]
    emit('tags-updated', props.video.tags)
  } catch (error) {
    ElMessage.error('添加标签失败')
    console.error('添加标签失败:', error)
  }
}

// 移除标签
const removeTag = async (tag) => {
  if (!props.video) return
  
  try {
    await TagService.removeTagFromVideo(props.video.id, tag.id)
    // 更新本地标签数组
    props.video.tags = currentTags.value.filter(t => t.id !== tag.id)
    emit('tags-updated', props.video.tags)
  } catch (error) {
    ElMessage.error('移除标签失败')
    console.error('移除标签失败:', error)
  }
}

// 监听对话框显示状态
watch(dialogVisible, (newValue) => {
  if (newValue) {
    loadTags()
  }
})
</script>

<style scoped>
.tags-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.current-tags,
.available-tags {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

h4 {
  margin: 0;
  color: #606266;
}

.categories-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-height: 400px;
  overflow-y: auto;
}

.category-group {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
  background-color: #fafafa;
}

.category-header {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.category-tag {
  font-weight: 600;
  border: none;
}

.category-name {
  font-size: 14px;
  font-weight: 600;
  color: #909399;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  cursor: pointer;
  transition: all 0.3s;
  background-color: #fff;
  border: 1px solid #dcdfe6;
}

.tag-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}
</style>