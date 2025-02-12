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