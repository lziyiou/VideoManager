<template>
  <div class="tags">
    <el-row :gutter="20">
      <!-- 标签分类管理 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h2>标签分类管理</h2>
              <el-button type="primary" @click="showCreateCategoryDialog">创建分类</el-button>
            </div>
          </template>
          
          <el-table :data="categories" style="width: 100%">
            <el-table-column prop="name" label="分类名称" />
            <el-table-column prop="color" label="颜色" width="80">
              <template #default="{ row }">
                <div 
                  class="color-preview" 
                  :style="{ backgroundColor: row.color || '#409EFF' }"
                ></div>
              </template>
            </el-table-column>
            <el-table-column prop="sort_order" label="排序" width="80" />
            <el-table-column label="标签数量" width="100">
              <template #default="{ row }">
                {{ row.tags_count || 0 }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button-group>
                  <el-button
                    type="primary"
                    size="small"
                    @click="showEditCategoryDialog(row)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    @click="deleteCategory(row)"
                  >
                    删除
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <!-- 标签管理 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h2>标签管理</h2>
              <el-button type="primary" @click="showCreateDialog">创建标签</el-button>
            </div>
          </template>
          
          <el-table :data="tags" style="width: 100%">
            <el-table-column prop="name" label="标签名称" />
            <el-table-column label="分类" width="120">
              <template #default="{ row }">
                <span v-if="row.category" :style="{ color: row.category.color }">
                  {{ row.category.name }}
                </span>
                <span v-else class="no-category">未分类</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="150">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button-group>
                  <el-button
                    type="primary"
                    size="small"
                    @click="showEditDialog(row)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    type="warning"
                    size="small"
                    @click="showAssignCategoryDialog(row)"
                  >
                    分类
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    @click="deleteTag(row)"
                  >
                    删除
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 标签编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑标签' : '创建标签'"
      width="30%"
    >
      <el-form :model="tagForm" label-width="80px">
        <el-form-item label="标签名称">
          <el-input v-model="tagForm.name" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="选择分类">
          <el-select v-model="tagForm.category_id" placeholder="请选择分类（可选）" clearable>
            <el-option label="无分类" :value="null" />
            <el-option 
              v-for="category in categories" 
              :key="category.id" 
              :label="category.name" 
              :value="category.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTag">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分类编辑对话框 -->
    <el-dialog
      v-model="categoryDialogVisible"
      :title="isCategoryEdit ? '编辑分类' : '创建分类'"
      width="40%"
    >
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="分类名称">
          <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="分类颜色">
          <el-color-picker v-model="categoryForm.color" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="categoryForm.description" 
            type="textarea" 
            placeholder="请输入分类描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="categoryDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCategory">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 标签分类分配对话框 -->
    <el-dialog
      v-model="assignDialogVisible"
      title="分配标签分类"
      width="30%"
    >
      <el-form label-width="80px">
        <el-form-item label="标签名称">
          <span>{{ currentTag?.name }}</span>
        </el-form-item>
        <el-form-item label="选择分类">
          <el-select v-model="selectedCategoryId" placeholder="请选择分类" clearable>
            <el-option label="无分类" :value="null" />
            <el-option 
              v-for="category in categories" 
              :key="category.id" 
              :label="category.name" 
              :value="category.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="assignDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="assignTagToCategory">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import TagService from '../services/tag_service'
import TagCategoryService from '../services/tag_category_service'

// 标签相关状态
const tags = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const tagForm = ref({
  id: null,
  name: '',
  category_id: null
})

// 分类相关状态
const categories = ref([])
const categoryDialogVisible = ref(false)
const isCategoryEdit = ref(false)
const categoryForm = ref({
  id: null,
  name: '',
  color: '#409EFF',
  sort_order: 0,
  description: ''
})

// 分类分配相关状态
const assignDialogVisible = ref(false)
const currentTag = ref(null)
const selectedCategoryId = ref(null)

const loading = ref(false)

// 加载所有标签
const loadTags = async () => {
  try {
    loading.value = true
    tags.value = await TagService.getAllTags()
  } catch (error) {
    ElMessage.error('加载标签失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 加载所有分类
const loadCategories = async () => {
  try {
    categories.value = await TagCategoryService.getAllCategories()
  } catch (error) {
    ElMessage.error('加载分类失败：' + error.message)
  }
}

// 初始化加载数据
onMounted(() => {
  loadTags()
  loadCategories()
})

// 方法
const formatDate = (date) => {
  return new Date(date).toLocaleString()
}

const showCreateDialog = () => {
  isEdit.value = false
  tagForm.value = { id: null, name: '', category_id: null }
  dialogVisible.value = true
}

const showEditDialog = (tag) => {
  isEdit.value = true
  tagForm.value = { 
    id: tag.id, 
    name: tag.name, 
    category_id: tag.category?.id || null 
  }
  dialogVisible.value = true
}

const saveTag = async () => {
  try {
    if (!tagForm.value.name.trim()) {
      ElMessage.warning('请输入标签名称')
      return
    }

    if (isEdit.value) {
      await TagService.updateTag(tagForm.value.id, tagForm.value.name)
    } else {
      await TagService.createTag(tagForm.value.name, tagForm.value.category_id)
    }
    
    dialogVisible.value = false
    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    loadTags() // 重新加载标签列表
    loadCategories() // 重新加载分类列表以更新标签数量
  } catch (error) {
    ElMessage.error('操作失败：' + error.message)
  }
}

const deleteTag = (tag) => {
  ElMessageBox.confirm(
    '确定要删除这个标签吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await TagService.deleteTag(tag.id)
      ElMessage.success('删除成功')
      loadTags() // 重新加载标签列表
    } catch (error) {
      ElMessage.error('删除失败：' + error.message)
    }
  })
}

// 生成随机颜色（排除已使用的颜色）
const generateRandomColor = () => {
  const allColors = [
    '#409EFF', // 蓝色
    '#67C23A', // 绿色
    '#E6A23C', // 橙色
    '#F56C6C', // 红色
    '#909399', // 灰色
    '#9C27B0', // 紫色
    '#FF9800', // 深橙色
    '#4CAF50', // 深绿色
    '#2196F3', // 深蓝色
    '#FF5722', // 深红色
    '#795548', // 棕色
    '#607D8B', // 蓝灰色
    '#E91E63', // 粉红色
    '#00BCD4', // 青色
    '#8BC34A', // 浅绿色
    '#FFC107', // 琥珀色
    '#FF6F00', // 深橙色
    '#6A1B9A'  // 深紫色
  ]
  
  // 获取已使用的颜色
  const usedColors = categories.value.map(category => category.color).filter(color => color)
  
  // 过滤出未使用的颜色
  const availableColors = allColors.filter(color => !usedColors.includes(color))
  
  // 如果所有颜色都被使用了，就从全部颜色中随机选择
  const colorsToChooseFrom = availableColors.length > 0 ? availableColors : allColors
  
  return colorsToChooseFrom[Math.floor(Math.random() * colorsToChooseFrom.length)]
}

// 分类管理方法
const showCreateCategoryDialog = () => {
  isCategoryEdit.value = false
  categoryForm.value = {
    id: null,
    name: '',
    color: generateRandomColor(),
    sort_order: 0,
    description: ''
  }
  categoryDialogVisible.value = true
}

const showEditCategoryDialog = (category) => {
  isCategoryEdit.value = true
  categoryForm.value = { ...category }
  categoryDialogVisible.value = true
}

const saveCategory = async () => {
  try {
    if (!categoryForm.value.name.trim()) {
      ElMessage.warning('请输入分类名称')
      return
    }

    if (isCategoryEdit.value) {
      await TagCategoryService.updateCategory(categoryForm.value.id, categoryForm.value)
    } else {
      await TagCategoryService.createCategory(categoryForm.value)
    }
    
    categoryDialogVisible.value = false
    ElMessage.success(isCategoryEdit.value ? '更新成功' : '创建成功')
    loadCategories() // 重新加载分类列表
  } catch (error) {
    ElMessage.error('操作失败：' + error.message)
  }
}

const deleteCategory = (category) => {
  ElMessageBox.confirm(
    '确定要删除这个分类吗？删除后该分类下的标签将变为未分类状态。',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await TagCategoryService.deleteCategory(category.id)
      ElMessage.success('删除成功')
      loadCategories() // 重新加载分类列表
      loadTags() // 重新加载标签列表以更新分类信息
    } catch (error) {
      ElMessage.error('删除失败：' + error.message)
    }
  })
}

// 标签分类分配方法
const showAssignCategoryDialog = (tag) => {
  currentTag.value = tag
  selectedCategoryId.value = tag.category?.id || null
  assignDialogVisible.value = true
}

const assignTagToCategory = async () => {
  try {
    await TagService.assignTagToCategory(currentTag.value.id, selectedCategoryId.value)
    assignDialogVisible.value = false
    ElMessage.success('分类分配成功')
    loadTags() // 重新加载标签列表以更新分类信息
    loadCategories() // 重新加载分类列表以更新标签数量
  } catch (error) {
    ElMessage.error('分配失败：' + error.message)
  }
}
</script>

<style scoped>
.tags {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.color-preview {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  display: inline-block;
}

.no-category {
  color: #909399;
  font-size: 12px;
  font-style: italic;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>