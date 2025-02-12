function updateVideo(filename, data) {
    data.filename = filename;
    fetch('/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(() => location.reload());
}

// 标签输入防抖处理
const tagInputs = document.querySelectorAll('.tags-input');
tagInputs.forEach(input => {
    input.addEventListener('input', function() {
        clearTimeout(this.timer);
        this.timer = setTimeout(() => {
            updateVideo(this.dataset.filename, {
                tags: this.value.split(',').map(t => t.trim())
            });
        }, 500);
    });
});


//捕获帧
let currentVideoFilename = null;

// 打开模态框并设置视频
function playVideo(filename) {
    currentVideoFilename = filename;
    const videoPlayer = document.getElementById('videoPlayer');
    videoPlayer.src = `/play/${filename}`;
    document.getElementById('videoModal').style.display = 'block';
}

// 关闭模态框
function closeModal() {
    document.getElementById('videoModal').style.display = 'none';
    const videoPlayer = document.getElementById('videoPlayer');
    videoPlayer.pause();
    videoPlayer.currentTime = 0;
}

// 捕获当前帧
function captureFrame() {
    const videoPlayer = document.getElementById('videoPlayer');
    const canvas = document.createElement('canvas');
    canvas.width = videoPlayer.videoWidth;
    canvas.height = videoPlayer.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoPlayer, 0, 0, canvas.width, canvas.height);

    // 将画布内容转换为 Base64 格式
    const base64Image = canvas.toDataURL('image/jpeg');

    // 调用后端 API 更新封面
    fetch('/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            filename: currentVideoFilename,
            cover: base64Image.split(',')[1], // 去掉 Base64 的前缀
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                location.reload(); // 刷新页面以显示新封面
            } else {
                alert('封面更新失败！');
            }
        });
}

// 加监听器，当用户编辑标签时自动保存
document.addEventListener("DOMContentLoaded", function () {
    // 监听标签输入框的失焦事件
    document.querySelectorAll('.tags-input').forEach(input => {
        input.addEventListener('blur', function () {
            const filename = this.dataset.filename;
            const tags = this.value.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);

            // 调用后端 API 更新标签
            fetch('/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
                    tags: tags,
                }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // alert('标签更新成功！');
                    } else {
                        alert('标签更新失败！');
                    }
                });
        });
    });
});

// 动态加载标签列表，并实现搜索功能
document.addEventListener("DOMContentLoaded", function () {
    // 加载所有标签
    fetch('/get-tags')
        .then(response => response.json())
        .then(tags => {
            const tagSearch = document.getElementById('tagSearch');

            // 填充标签选项
            tags.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                tagSearch.appendChild(option);
            });

            // 初始化 Select2
            $(tagSearch).select2({
                placeholder: "选择标签",
                allowClear: true,
            });

            // 监听标签选择事件
            $(tagSearch).on('change', function () {
                const selectedTags = $(this).val() || []; // 获取用户选择的标签

                // 过滤视频卡片
                document.querySelectorAll('.video-card').forEach(card => {
                    const cardTags = card.querySelector('.tags-input').value.split(',').map(tag => tag.trim());
                    if (selectedTags.length === 0 || selectedTags.every(tag => cardTags.includes(tag))) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
});

