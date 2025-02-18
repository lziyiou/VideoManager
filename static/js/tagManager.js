class TagManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 50;
        this.init();
    }

    init() {
        this.initTagSearch();
        this.loadTags();
        this.bindEvents();
    }

    // 初始化标签搜索
    initTagSearch() {
        const tagSearch = document.getElementById('tagSearch');
        $(tagSearch).select2({
            placeholder: "选择标签",
            allowClear: true,
        });
    }

    // 更新标签
    async updateTags(filename, tags) {
        try {
            const data = await Utils.apiRequest('/update', {
                method: 'POST',
                body: JSON.stringify({ filename, tags }),
            });
            if (data.success) {
                this.updateTagSearch();
            }
        } catch (error) {
            Utils.showErrorMessage('标签更新失败');
        }
    }

    // 加载标签列表
    async loadTags(page = 1) {
        try {
            const tags = await Utils.apiRequest(`/get-tags?page=${page}&limit=${this.pageSize}`);
            this.updateTagOptions(tags);
            if (tags.length === this.pageSize) {
                this.currentPage++;
                this.loadTags(this.currentPage);
            }
        } catch (error) {
            Utils.showErrorMessage('加载标签失败');
        }
    }

    // 绑定事件
    bindEvents() {
        const tagInputs = document.querySelectorAll('.tags-input');
        tagInputs.forEach(input => {
            const debouncedUpdate = Utils.debounce(() => {
                const filename = input.dataset.filename;
                const uniqueTags = this.removeDuplicatesFromString(input.value);
                input.value = uniqueTags.join(',');
                this.updateTags(filename, uniqueTags);
            }, 1000);
            input.addEventListener('input', debouncedUpdate);
        });
    }

    // 去重处理
    removeDuplicatesFromString(input) {
        return [...new Set(input.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0))];
    }

    // 添加更新标签选项方法
    updateTagOptions(tags) {
        const tagSearch = document.getElementById('tagSearch');
        tags.forEach(tag => {
            const option = document.createElement('option');
            option.value = tag;
            option.textContent = tag;
            tagSearch.appendChild(option);
        });
    }

    // 添加更新标签搜索方法
    updateTagSearch() {
        const tagSearch = document.getElementById('tagSearch');
        tagSearch.innerHTML = ''; // 清空现有选项
        this.currentPage = 1;
        this.loadTags();
    }

    // 添加初始化标签输入框的方法
    initTagInputs() {
        const tagInputs = document.querySelectorAll('.tags-input');
        tagInputs.forEach(input => {
            input.addEventListener('change', (event) => {
                const filename = event.target.dataset.filename;
                const tags = this.removeDuplicatesFromString(event.target.value);
                this.updateTags(filename, tags);
            });
        });
    }
} 