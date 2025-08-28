# Video Manager

一个简单高效的本地视频管理系统，支持视频在线播放和管理。

## 功能特点

- 📺 在线流式播放视频
- 🔄 实时同步本地视频文件
- 🔍 视频搜索功能
- 🏷️ 视频标签管理
- 📱 支持多设备访问
- 🗑️ 视频文件删除（同步到磁盘）

## 系统功能

### 1. 视频文件管理
- 实时监控和同步磁盘上的视频文件
- 支持文件删除操作（同步到磁盘）
- 视频文件元数据缓存
- 视频缩略图自动生成
- 视频封面图提取

### 2. 视频播放功能
- 支持在线流式播放
- 确保播放流畅性
- 支持视频断点续播
- 多格式视频支持

### 3. 搜索与组织
- 基础视频搜索
- 标签系统管理
- 视频信息编辑（标题、标签等）
- 多维度排序（时间、大小、名称）

### 4. 系统特性
- 前后端分离架构
- 跨平台访问支持
- 操作日志记录
- 视频元数据缓存优化

## 技术栈

### 后端
- FastAPI：Web框架
- SQLite：数据存储
- SQLAlchemy：ORM框架
- ffmpeg-python：视频处理
- watchdog：文件监控

### 前端
- Vue.js：前端框架
- Video.js：视频播放器
- Element Plus：UI组件库
- Axios：HTTP客户端

## 项目结构

```plaintext
VideoManager/
├── backend/                # 后端项目目录
│   ├── app/               # 应用主目录
│   │   ├── __init__.py
│   │   ├── main.py       # 主程序入口
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # 数据校验
│   │   ├── services/     # 业务逻辑
│   │   └── api/          # API接口
│   ├── requirements.txt   # 依赖清单
│   └── config.py         # 配置文件
└── frontend/             # 前端项目目录
    ├── src/             # 源代码
    ├── public/          # 静态资源
    ├── package.json     # 项目配置
    └── index.html       # 入口页面

```

## 安装与运行
1. 克隆项目到本地
   ```bash
   git clone
   git clone URL_ADDRESS.com/yourusername/VideoManager.git
   ```
2. 直接运行start.bat文件即可以启动项目（若成功，则跳过2-7步，可直接从第8步访问项目）
2. 进入后端目录
   ```bash
   cd VideoManager/backend
   ```
3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
4. 运行后端服务
   ```bash
   uvicorn app.main:app --reload
   ```
5. 进入前端目录
   ```bash
   cd ../frontend
   ```
6. 安装依赖
   ```bash
   npm install
   ```
7. 运行前端服务
   ```bash
   npm run dev
   ```
8. 访问前端页面
    ```bash
    URL_ADDRESS:8080
    ```

