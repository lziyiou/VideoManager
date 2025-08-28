<template>
  <div class="video-actions">
    <el-button link type="primary" @click="handleEdit">
      <el-icon :size="16"><Edit style="color: #409EFF; transform: scale(1.1);" /></el-icon>
    </el-button>
    <el-button 
      link 
      :type="video.is_favorite ? 'danger' : 'primary'" 
      @click="handleToggleFavorite"
    >
      <el-icon :size="16">
        <StarFilled v-if="video.is_favorite" style="color: rgb(255, 183, 0); transform: scale(1.1); border-radius: 50%;" />
        <Star v-else style="color: #409EFF; transform: scale(1.1); border-radius: 50%;" />
      </el-icon>
    </el-button>
    <el-button 
      link 
      :type="!video.web_playable ? 'danger' : 'primary'" 
      :style="!video.web_playable ? 'font-weight: bold; text-decoration: underline;' : ''"
      @click="handleToggleWebPlayable"
    >
      <el-icon :size="16">
        <WarningFilled v-if="!video.web_playable" style="color: #F56C6C; transform: scale(1.1);" />
        <Warning v-else style="color: #409EFF; transform: scale(1.1);" />
      </el-icon>
    </el-button>
    <el-button link type="danger" @click="handleDelete">
      <el-icon :size="16"><Delete style="color: #F56C6C; transform: scale(1.1);" /></el-icon>
    </el-button>
  </div>
</template>

<script setup>
import { Edit, Star, StarFilled, Warning, WarningFilled, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  video: {
    type: Object,
    required: true
  },
  showLabels: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'edit',
  'update-status', 
  'delete'
])

const handleEdit = () => {
  emit('edit')
}

const handleToggleFavorite = () => {
  emit('update-status', 'favorite', !props.video.is_favorite)
}

const handleToggleWebPlayable = () => {
  emit('update-status', 'webPlayable', !props.video.web_playable)
}

const handleDelete = () => {
  emit('delete')
}
</script>

<style scoped>
.video-actions {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-left: auto;
}
</style>