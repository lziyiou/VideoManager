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
                showSuccessMessage('标签更新成功！');
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

    // 清空现有的选项
    tagSearch.innerHTML = '';

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
        .then(tags => {
            // 动态添加标签到 Select2
            tags.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                tagSearch.appendChild(option);
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
 * 过滤视频卡片
 * @param {string[]} selectedTags - 用户选择的标签
 */
function filterVideoCards(selectedTags) {
    let hasVisibleCards = false;
    document.querySelectorAll('.video-card').forEach(card => {
        const cardTags = card.querySelector('.tags-input').value.split(',').map(tag => tag.trim());
        if (selectedTags.length === 0 || selectedTags.every(tag => cardTags.includes(tag))) {
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

// 动态加载标签列表，并实现搜索功能
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

document.addEventListener("DOMContentLoaded", function () {
    loadTags();
    $(tagSearch).select2({
        placeholder: "选择标签",
        allowClear: true,
    });
});

// 防抖处理
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
    }, 500);

    input.addEventListener('input', debouncedUpdate);
});

// 标签选择事件
$(tagSearch).on('change', function () {
    const selectedTags = $(this).val() || [];
    filterVideoCards(selectedTags);
});