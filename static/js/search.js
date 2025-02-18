class VideoSearch {
    constructor() {
        this.init();
    }

    init() {
        this.restoreState();
        this.bindSearchEvents();
    }

    // 保存当前状态
    saveState() {
        const state = {
            nameQuery: document.getElementById('nameSearch').value,
            selectedTags: $(document.getElementById('tagSearch')).val() || [],
            currentPage: this.currentPage
        };
        
        // 更新 URL 参数
        const params = new URLSearchParams(window.location.search);
        params.set('page', state.currentPage);
        params.set('name', state.nameQuery);
        params.delete('tags[]'); // 清除旧的标签参数
        state.selectedTags.forEach(tag => params.append('tags[]', tag));
        
        // 更新 URL，但不刷新页面
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.history.pushState(state, '', newUrl);
        
        // 保存到 localStorage
        localStorage.setItem('videoSearchState', JSON.stringify(state));
    }

    // 恢复状态
    restoreState() {
        // 首先从 URL 参数获取状态
        const params = new URLSearchParams(window.location.search);
        const state = {
            currentPage: parseInt(params.get('page')) || 1,
            nameQuery: params.get('name') || '',
            selectedTags: params.getAll('tags[]') || []
        };

        // 如果 URL 没有参数，尝试从 localStorage 获取
        if (!params.has('page') && !params.has('name') && !params.has('tags[]')) {
            const savedState = localStorage.getItem('videoSearchState');
            if (savedState) {
                Object.assign(state, JSON.parse(savedState));
            }
        }

        // 应用状态
        this.currentPage = state.currentPage;
        document.getElementById('nameSearch').value = state.nameQuery;
        
        // 设置标签选择
        const tagSearch = document.getElementById('tagSearch');
        $(tagSearch).val(state.selectedTags).trigger('change');

        // 如果有任何搜索条件，执行搜索
        if (state.nameQuery || state.selectedTags.length > 0 || state.currentPage > 1) {
            this.searchVideos(state.currentPage);
        }
    }

    async searchVideos(page = 1) {
        this.currentPage = page;
        const nameQuery = document.getElementById('nameSearch').value.trim();
        const selectedTags = $(document.getElementById('tagSearch')).val() || [];
        
        try {
            // 构建查询参数
            const params = new URLSearchParams({
                page: page,
                name: nameQuery
            });
            
            // 添加标签参数
            selectedTags.forEach(tag => {
                params.append('tags[]', tag);
            });
            
            // 发送请求
            const response = await fetch(`/search?${params.toString()}`);
            const data = await response.json();
            
            this.updateUI(data);
            
            // 搜索完成后保存状态
            this.saveState();
        } catch (error) {
            Utils.showErrorMessage('搜索失败');
            console.error('搜索错误:', error);
        }
    }

    updateUI(data) {
        // 更新视频网格
        const videoGrid = document.querySelector('.video-grid');
        if (data.videos.length === 0) {
            videoGrid.innerHTML = `
                <div id="no-results-message" style="display: block;">
                    没有找到符合条件的视频。
                </div>`;
            return;
        }

        videoGrid.innerHTML = data.videos.map(video => `
            <div class="video-card" data-filename="${video.filename}">
                <div class="cover" onclick="window.videoPlayer.playVideo('${video.filename}')">
                    ${video.cover ? 
                        `<img src="/static/${video.cover}" alt="${video.filename}">` :
                        '<div class="default-cover">点击播放视频</div>'}
                </div>
                <div class="info">
                    <div class="tags-and-delete">
                        <input type="text" class="tags-input"
                               value="${video.tags.join(',')}"
                               data-filename="${video.filename}"
                               placeholder="输入标签，用逗号分隔">
                        <button class="delete-btn" onclick="window.videoPlayer.deleteVideo('${video.filename}')" title="删除视频">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                    <div class="filename" title="${video.filename}">${video.filename}</div>
                </div>
            </div>
        `).join('');

        // 更新分页控件
        this.updatePagination(data.current_page, data.total_pages);
        
        // 重新初始化标签输入框
        window.tagManager.initTagInputs();
    }

    updatePagination(currentPage, totalPages) {
        const pagination = document.querySelector('.pagination');
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        const start = Math.max(currentPage - 6, 1);
        const end = Math.min(currentPage + 6, totalPages);
        
        let html = '';
        
        // 上一页按钮
        if (currentPage > 1) {
            html += `<button class="page-btn" onclick="window.videoSearch.searchVideos(${currentPage - 1})" title="上一页">
                <i class="fas fa-chevron-up"></i>
            </button>`;
        }
        
        // 第一页按钮
        if (start > 1) {
            html += `<button class="page-btn" onclick="window.videoSearch.searchVideos(1)" title="第1页">
                <i class="fas fa-angle-double-up"></i>
            </button>`;
            if (start > 2) html += '<span class="page-ellipsis">•••</span>';
        }
        
        // 中间的页码按钮
        for (let i = start; i <= end; i++) {
            html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" 
                            onclick="window.videoSearch.searchVideos(${i})" title="第${i}页">
                ${i}
            </button>`;
        }
        
        // 最后一页按钮
        if (end < totalPages) {
            if (end < totalPages - 1) html += '<span class="page-ellipsis">•••</span>';
            html += `<button class="page-btn" onclick="window.videoSearch.searchVideos(${totalPages})" title="最后一页">
                <i class="fas fa-angle-double-down"></i>
            </button>`;
        }
        
        // 下一页按钮
        if (currentPage < totalPages) {
            html += `<button class="page-btn" onclick="window.videoSearch.searchVideos(${currentPage + 1})" title="下一页">
                <i class="fas fa-chevron-down"></i>
            </button>`;
        }
        
        pagination.innerHTML = html;
    }

    bindSearchEvents() {
        const nameSearchInput = document.getElementById('nameSearch');
        const debouncedSearch = Utils.debounce(() => this.searchVideos(1), 300);
        nameSearchInput.addEventListener('input', debouncedSearch);

        const tagSearch = document.getElementById('tagSearch');
        $(tagSearch).on('change', () => this.searchVideos(1));
    }

    // 修改 changePage 方法使用新的搜索
    async changePage(page) {
        await this.searchVideos(page);
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    clearSearch() {
        // 清空名称搜索
        const nameSearchInput = document.getElementById('nameSearch');
        nameSearchInput.value = '';
        
        // 清空标签选择
        const tagSearch = document.getElementById('tagSearch');
        $(tagSearch).val(null).trigger('change');
        
        // 重置页码
        this.currentPage = 1;
        
        // 清除保存的状态
        localStorage.removeItem('videoSearchState');
        
        // 更新 URL
        window.history.pushState({}, '', window.location.pathname);
        
        // 重新搜索以显示所有视频
        this.searchVideos(1);
    }
} 