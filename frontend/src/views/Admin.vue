<template>
  <div class="admin-container">
    <h1>系统设置</h1>
    <div v-if="settings" class="settings-section">
      <h2>根目录设置</h2>
      <!-- <p class="description">请选择系统的根目录，该目录将用于视频文件的管理。</p> -->
      
      <div class="directory-selector">
        <div class="input-group">
          <input
            v-model="selectedDirectory"
            type="text"
            class="directory-input"
            placeholder="请输入目录路径"
            @blur="saveDirectory"
          />
        </div>
      </div>

      <div v-if="message" :class="['message', messageType]">
        {{ message }}
      </div>

      <div class="scan-section">
        <h2>文件扫描</h2>
        <p class="description">扫描视频文件并更新数据库。</p>
        
        <div class="scan-controls">
          <el-button 
            type="primary" 
            @click="handleScan" 
            :loading="scanning"
            :disabled="scanning"
          >
            <el-icon><Refresh /></el-icon>
            {{ scanning ? '扫描中...' : '开始扫描' }}
          </el-button>

          <div v-if="scanning" class="progress-info">
            <el-progress 
              :percentage="scanProgress" 
              :status="scanProgress === 100 ? 'success' : ''"
            />
            <p class="scan-status">{{ scanStatus }}</p>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="loading-section">
      <p>正在加载配置信息...</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'AdminView',
  components: {
    Refresh
  },
  data() {
    return {
      selectedDirectory: '',
      message: '',
      messageType: 'success',
      unsavedChanges: false,
      settings: null,
      scanning: false,
      scanProgress: 0,
      scanStatus: '',
      scanInterval: null
    }
  },
  watch: {
    selectedDirectory(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.unsavedChanges = true
      }
    }
  },
  beforeRouteLeave(to, from, next) {
    if (this.unsavedChanges) {
      this.saveDirectory()
    }
    next()
  },
  mounted() {
    window.addEventListener('beforeunload', this.handleBeforeUnload)
    this.loadSettings()
  },
  beforeDestroy() {
    window.removeEventListener('beforeunload', this.handleBeforeUnload)
    if (this.scanInterval) {
      clearInterval(this.scanInterval)
    }
  },
  methods: {
    async loadSettings() {
      try {
        const response = await axios.get('/api/settings/settings')
        const rootDirSetting = response.data.find(setting => setting.key === 'root_directory')
        this.settings = { root_directory: rootDirSetting ? rootDirSetting.value : '' }
        this.selectedDirectory = this.settings.root_directory || ''
      } catch (error) {
        this.showMessage('加载配置失败：' + (error.response?.data?.detail || error.message), 'error')
      }
    },
    handleBeforeUnload(e) {
      if (this.unsavedChanges) {
        this.saveDirectory()
      }
    },
    async saveDirectory() {
      if (!this.selectedDirectory || this.selectedDirectory === this.settings.root_directory) {
        this.unsavedChanges = false;
        return;
      }

      try {
        await axios.post('/api/settings/root_directory', {
          directory_path: this.selectedDirectory
        })
        this.showMessage('根目录设置已保存', 'success')
        this.unsavedChanges = false
        this.settings.root_directory = this.selectedDirectory
      } catch (error) {
        this.showMessage('保存设置失败：' + (error.response?.data?.detail || error.message), 'error')
      }
    },
    showMessage(text, type = 'success') {
      ElMessage({
        message: text,
        type: type,
      })
    },

    async handleScan() {
      try {
        this.scanning = true
        this.scanProgress = 0
        this.scanStatus = '正在扫描文件...'

        // 启动扫描
        await axios.get('/api/videos/scan')

        // 开始轮询进度
        this.scanInterval = setInterval(async () => {
          try {
            const response = await axios.get('/api/videos/scan/progress')
            const { progress, status, completed } = response.data

            this.scanProgress = Math.round(progress * 100)
            this.scanStatus = status

            if (completed) {
              clearInterval(this.scanInterval)
              this.scanning = false
              this.showMessage('扫描完成', 'success')
            }
          } catch (error) {
            console.error('获取扫描进度失败:', error)
            clearInterval(this.scanInterval)
            this.scanning = false
            this.showMessage('获取扫描进度失败', 'error')
          }
        }, 1000)
      } catch (error) {
        this.scanning = false
        this.showMessage('启动扫描失败: ' + (error.response?.data?.detail || error.message), 'error')
      }
    }
  }
}
</script>

<style scoped>
.admin-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 30px;
  background: linear-gradient(to bottom, #f8f9fa, #ffffff);
}

h1 {
  font-size: 32px;
  margin-bottom: 30px;
  color: #1a365d;
  font-weight: 600;
  text-align: center;
  position: relative;
}

h1::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background: #3498db;
  border-radius: 2px;
}

.settings-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.settings-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12);
}

h2 {
  font-size: 24px;
  margin-bottom: 20px;
  color: #2c5282;
  font-weight: 500;
}

.description {
  color: #4a5568;
  margin-bottom: 25px;
  font-size: 16px;
  line-height: 1.6;
}

.directory-selector {
  margin-bottom: 30px;
}

.input-group {
  display: flex;
  gap: 15px;
}

.directory-input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 15px;
  color: #2d3748;
  transition: all 0.3s ease;
  background: #f8fafc;
}

.directory-input:focus {
  outline: none;
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.15);
  background: #ffffff;
}

.directory-input::placeholder {
  color: #a0aec0;
}

.message {
  margin-top: 20px;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  font-weight: 500;
  opacity: 0;
  transform: translateY(-10px);
  animation: slideIn 0.3s ease forwards;
}

@keyframes slideIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.success {
  background-color: #c6f6d5;
  color: #276749;
  border: 1px solid #9ae6b4;
}

.error {
  background-color: #fed7d7;
  color: #9b2c2c;
  border: 1px solid #feb2b2;
}

.loading-section {
  text-align: center;
  padding: 60px;
  color: #4a5568;
  background: #f7fafc;
  border-radius: 12px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06);
}

.loading-section p {
  font-size: 16px;
  animation: pulse 1.5s ease infinite;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}

.scan-section {
  margin-top: 40px;
  background: #ffffff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.scan-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12);
}

.scan-controls {
  margin-top: 20px;
}

.progress-info {
  margin-top: 20px;
  max-width: 400px;
}

.scan-status {
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}
</style>