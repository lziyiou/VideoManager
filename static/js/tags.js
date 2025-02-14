/**
 * 更新视频标签到后端
 * @param {string} filename - 视频文件名
 * @param {string[]} tags - 标签
 */
function updateTags(filename, tags) {
    fetch('/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, tags: tags }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // showSuccessMessage('标签更新成功！');
                // 更新 Select2 的标签列表
                updateTagSearch();
            } else {
                showErrorMessage('标签更新失败！');
            }
        })
        .catch(error => {
            console.error('标签更新时出错:', error);
            showErrorMessage('标签更新时发生错误');
        });
}

/**
 * 去除字符串中的重复标签
 * @param {string} input - 标签字符串（以逗号分隔）
 * @returns {string[]} 唯一的标签字符串数组
 */
function removeDuplicatesFromString(input) {
    return [...new Set(input.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0))];
}

/**
 * 更新 Select2 的标签列表
 */
function updateTagSearch() {
    const tagSearch = document.getElementById('tagSearch');

    // 从后端获取所有标签
    fetch('/get-tags', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP 错误！状态码: ${response.status}`);
            }
            return response.json();
        })
        .then(serverTags => {
            // 获取当前 Select2 中的所有标签
            const currentOptions = Array.from(tagSearch.options).map(option => option.value);

            // 找出需要新增的标签（后端有但前端没有）
            const tagsToAdd = serverTags.filter(tag => !currentOptions.includes(tag));

            // 找出需要移除的标签（前端有但后端没有）
            const tagsToRemove = currentOptions.filter(tag => !serverTags.includes(tag));

            // 动态添加新标签
            tagsToAdd.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                tagSearch.appendChild(option);
            });

            // 移除多余的标签
            tagsToRemove.forEach(tag => {
                const optionToRemove = Array.from(tagSearch.options).find(option => option.value === tag);
                if (optionToRemove) {
                    tagSearch.removeChild(optionToRemove);
                }
            });

            // 重新初始化 Select2
            $(tagSearch).trigger('change'); // 触发 change 事件以刷新 Select2
        })
        .catch(error => {
            console.error('获取标签时出错:', error);
            showErrorMessage('无法加载标签，请稍后重试');
        });
}

/**
 * 按名称模糊搜索视频
 * @param {string} query - 用户输入的搜索关键字
 */
function searchByFilename(query) {
    const videoCards = document.querySelectorAll('.video-card');

    videoCards.forEach(card => {
        const filename = card.querySelector('.filename').textContent.toLowerCase();
        const isMatch = query.trim().toLowerCase() === '' || filename.includes(query.trim().toLowerCase());
        card.dataset.nameMatch = isMatch; // 保存名称匹配状态
    });
}

/**
 * 过滤视频卡片（按标签）
 * @param {string[]} selectedTags - 用户选择的标签
 */
function filterVideoCards(selectedTags) {
    const videoCards = document.querySelectorAll('.video-card');

    videoCards.forEach(card => {
        const cardTags = card.querySelector('.tags-input').value.split(',').map(tag => tag.trim());
        const isMatch = selectedTags.length === 0 || selectedTags.every(tag => cardTags.includes(tag));
        card.dataset.tagMatch = isMatch; // 保存标签匹配状态
    });
}

/**
 * 整合名称和标签搜索结果
 */
function integrateSearchResults() {
    const nameQuery = document.getElementById('nameSearch').value.trim().toLowerCase();
    const tagSearch = document.getElementById('tagSearch');
    const selectedTags = $(tagSearch).val() || [];

    // 执行名称搜索
    searchByFilename(nameQuery);

    // 执行标签搜索
    filterVideoCards(selectedTags);

    // 整合结果
    const videoCards = document.querySelectorAll('.video-card');
    let hasVisibleCards = false;

    videoCards.forEach(card => {
        const isNameMatch = card.dataset.nameMatch === 'true'; // 名称是否匹配
        const isTagMatch = card.dataset.tagMatch === 'true'; // 标签是否匹配

        if (isNameMatch && isTagMatch) {
            card.style.display = 'block';
            hasVisibleCards = true;
        } else {
            card.style.display = 'none';
        }
    });

    // 显示“无结果”提示
    const noResultsMessage = document.getElementById('no-results-message');
    noResultsMessage.style.display = hasVisibleCards ? 'none' : 'block';
}

// 初始化事件监听器
document.addEventListener("DOMContentLoaded", function () {
    // 防抖处理名称搜索
    const nameSearchInput = document.getElementById('nameSearch');
    const debouncedSearch = _.debounce(() => {
        integrateSearchResults();
    }, 300);

    nameSearchInput.addEventListener('input', debouncedSearch);

    // 标签选择事件
    const tagSearch = document.getElementById('tagSearch');
    $(tagSearch).on('change', () => {
        integrateSearchResults();
    });

    // 动态加载标签列表
    loadTags();

    // 初始化 Select2
    $(tagSearch).select2({
        placeholder: "选择标签",
        allowClear: true,
    });

    // 视频标签输入防抖
    const tagInputs = document.querySelectorAll('.tags-input');
    tagInputs.forEach(input => {
        const debouncedUpdate = _.debounce(() => {
            const filename = input.dataset.filename;
            // 获取输入框中的标签并去重
            const uniqueTags = removeDuplicatesFromString(input.value);
            // 更新输入框内容
            input.value = uniqueTags.join(',');
            // 提交到后端
            updateTags(filename, uniqueTags);
        }, 1000);
        input.addEventListener('input', debouncedUpdate);
    });
});

/**
 * 动态加载标签列表
 */
let currentPage = 1;
const pageSize = 50;
function loadTags(page = 1) {
    fetch(`/get-tags?page=${page}&limit=${pageSize}`)
        .then(response => response.json())
        .then(tags => {
            const tagSearch = document.getElementById('tagSearch');
            tags.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                tagSearch.appendChild(option);
            });
            // 如果还有更多数据，加载下一页
            if (tags.length === pageSize) {
                currentPage++;
                loadTags(currentPage);
            }
        });
}