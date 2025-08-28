<template>
  <div class="video-search-bar">
    <div class="top-controls">
      <div class="left-section">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索视频文件"
          class="search-input"
          @input="handleSearch"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-switch
          v-model="onlyFavorites"
          class="favorite-filter"
          @change="handleSearch"
          active-text="只看收藏"
          inactive-text=""
        >
        </el-switch>
        
        <el-select
          v-model="durationFilter"
          placeholder="视频时长"
          clearable
          @change="handleSearch"
          class="duration-filter"
        >
          <el-option
            v-for="option in durationOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>

        <el-select
          v-model="sortFilter"
          placeholder="排序方式"
          clearable
          @change="handleSortChange"
          class="sort-filter"
        >
          <el-option
            v-for="option in sortOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
        
        <el-button 
          v-if="sortFilter === 'random'"
          @click="refreshRandom"
          :icon="Refresh"
          size="small"
          type="primary"
          plain
          class="refresh-random-btn"
        >
          重新随机
        </el-button>
      </div>
      <div class="right-section">
        <el-radio-group v-model="viewMode" size="large" @change="handleViewModeChange">
          <el-radio-button value="list">
            <el-icon><List /></el-icon>
          </el-radio-button>
          <el-radio-button value="grid">
            <el-icon><Grid /></el-icon>
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>
    
    <!-- 标签过滤组件 -->
    <div class="tag-filter-container">
      <TagList
        v-model:selected-tag-ids="selectedTagIds"
        @update:selected-tag-ids="handleSearch"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search, Refresh, List, Grid } from '@element-plus/icons-vue'
import TagList from './TagList.vue'

const emit = defineEmits([
  'search',
  'sort-change',
  'view-mode-change',
  'refresh-random'
])

// 使用 v-model 的响应式数据
const searchKeyword = ref('')
const onlyFavorites = ref(false)
const selectedTagIds = ref([])
const durationFilter = ref('')
const sortFilter = ref('random')
const viewMode = ref('grid')

// 选项数据
const durationOptions = [
  { label: '全部', value: '' },
  { label: '短视频', value: 'short' },
  { label: '长视频', value: 'long' }
]

const sortOptions = [
  { label: '文件名', value: 'filename' },
  { label: '时长', value: 'duration' },
  { label: '添加时间', value: 'created_at' },
  { label: '随机', value: 'random' },
]

// 事件处理函数
const handleSearch = () => {
  emit('search', {
    keyword: searchKeyword.value,
    onlyFavorites: onlyFavorites.value,
    selectedTagIds: selectedTagIds.value,
    durationFilter: durationFilter.value
  })
}

const handleSortChange = () => {
  emit('sort-change', {
    sortFilter: sortFilter.value
  })
}

const handleViewModeChange = () => {
  emit('view-mode-change', {
    viewMode: viewMode.value
  })
}

const refreshRandom = () => {
  emit('refresh-random')
}

</script>

<style scoped>
.video-search-bar {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
}

.top-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.left-section {
  display: flex;
  gap: 12px;
}

.search-input {
  width: 300px;
}

.tag-filter-container {
  width: 100%;
}

.favorite-filter {
  margin-left: 12px;
}

.duration-filter {
  width: 180px;
  margin-left: 12px;
}

.sort-filter {
  width: 130px;
  margin-left: 12px;
}

.refresh-random-btn {
  margin-left: 8px;
  font-size: 12px;
}
</style>