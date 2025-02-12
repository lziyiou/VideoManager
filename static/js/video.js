/**
 * 更新视频数据到服务器
 * @param {string} filename - 视频文件名
 * @param {object} data - 要更新的数据（如标签或封面）
 * @param {function} onSuccess - 成功回调函数
 * @param {function} onError - 失败回调函数
 */
async function updateVideoData(filename, data, onSuccess, onError) {
    try {
        data.filename = filename;
        const response = await fetch('/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await response.json();
        if (!result.success) {
            throw new Error(result.message || '更新失败');
        }
        if (onSuccess) onSuccess(result); // 调用成功回调
        return result;
    } catch (error) {
        console.error('更新视频数据时出错:', error);
        if (onError) onError(error); // 调用失败回调
        showErrorMessage(error.message || '更新视频数据时发生错误');
        throw error;
    }
}

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
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// 封面更新
function captureFrame() {
    const videoPlayer = document.getElementById('videoPlayer');
    const canvas = document.createElement('canvas');
    canvas.width = videoPlayer.videoWidth;
    canvas.height = videoPlayer.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoPlayer, 0, 0, canvas.width, canvas.height);

    // 将画布内容转换为 Base64 格式
    const base64Image = canvas.toDataURL('image/jpeg');

    updateVideoData(currentVideoFilename, { cover: base64Image.split(',')[1] })
        .then(() => {
            showSuccessMessage('封面更新成功！');
            const videoCard = document.querySelector(`.video-card[data-filename="${currentVideoFilename}"]`);
            const coverImg = videoCard.querySelector('.cover img');
            if (coverImg) {
                coverImg.src = base64Image;
            } else {
                const coverDiv = videoCard.querySelector('.cover');
                coverDiv.innerHTML = `<img src="${base64Image}">`;
            }
        },
            (error) => {
                console.error('封面更新失败:', error);
            }
        );
}

// 删除视频
function deleteVideo(filename) {
    Swal.fire({
        title: '确定要删除吗？',
        text: `你将删除视频 "${filename}"`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '确定',
        cancelButtonText: '取消',
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/delete_video/${filename}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showSuccessMessage(`视频 "${filename}" 已成功删除`);
                        const videoCard = document.querySelector(`.video-card[data-filename="${filename}"]`);
                        if (videoCard) {
                            videoCard.classList.add('removing');
                            setTimeout(() => videoCard.remove(), 300);
                        }
                        // 更新 Select2 的标签列表
                        updateTagSearch();
                    } else {
                        showErrorMessage(`删除视频 "${filename}" 失败: ${data.message}`);
                    }
                })
                .catch(error => {
                    console.error('删除视频时出错:', error);
                    showErrorMessage(`删除视频 "${filename}" 时发生错误`);
                });
        }
    });
}