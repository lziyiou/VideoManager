function uploadCover(input) {
    const file = input.files[0];
    const reader = new FileReader();
    reader.onload = function(e) {
        const base64 = e.target.result.split(',')[1];
        updateVideo(input.dataset.filename, { cover: base64 });
    };
    reader.readAsDataURL(file);
}

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

function playVideo(filename) {
    // 调用后端 API 获取视频文件
    fetch(`/play/${filename}`)
        .then(response => response.blob())
        .then(blob => {
            // 创建一个 URL 对象，指向视频文件的 blob 数据
            const url = URL.createObjectURL(blob);

            // 获取模态框和视频播放器元素
            const modal = document.getElementById('videoModal');
            const videoPlayer = document.getElementById('videoPlayer');

            // 设置视频播放器的 source 为视频 URL
            videoPlayer.src = url;

            // 显示模态框
            modal.style.display = "block";

            // 播放视频
            videoPlayer.play();
        })
        .catch(error => {
            console.error('Error fetching video:', error);
            alert('视频加载失败，请稍后重试。');
        });
}

function closeModal() {
    const modal = document.getElementById('videoModal');
    const videoPlayer = document.getElementById('videoPlayer');

    // 停止视频播放
    videoPlayer.pause();
    videoPlayer.src = "";  // 清空 video 标签的 src，防止继续加载

    // 关闭模态框
    modal.style.display = "none";
}
