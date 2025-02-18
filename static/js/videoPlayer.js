class VideoPlayer {
    constructor() {
        this.currentVideoFilename = null;
        this.isClosing = false;
        this.player = null;
        this.init();
    }

    init() {
        // 初始化 Plyr 播放器
        const videoElement = document.getElementById('videoPlayer');
        this.player = new Plyr(videoElement, {
            controls: [
                'play-large', // 大播放按钮
                'play', // 播放/暂停
                'progress', // 进度条
                'current-time', // 当前时间
                'duration', // 总时长
                'mute', // 静音
                'volume', // 音量
                'capture-frame', // 自定义控制按钮
                'settings', // 设置
                'pip', // 画中画
                'fullscreen' // 全屏
            ],
            keyboard: { focused: true, global: true },
            tooltips: { controls: true, seek: true },
            seekTime: 5,
            quality: {
                default: 1080,
                options: [4320, 2880, 2160, 1440, 1080, 720, 576, 480, 360, 240]
            }
        });

        // 注册自定义控制按钮
        Plyr.defaults.controls.push('capture-frame');
        
        // 添加自定义按钮到控制栏
        this.player.on('ready', () => {
            const container = this.player.elements.controls.querySelector('.plyr__controls__item:nth-last-child(3)');
            const captureBtn = document.createElement('button');
            captureBtn.type = 'button';
            captureBtn.className = 'plyr__control';
            captureBtn.setAttribute('data-plyr', 'capture-frame');
            captureBtn.innerHTML = '<i class="fas fa-camera"></i>';
            captureBtn.title = '捕获当前帧作为封面';
            captureBtn.onclick = () => this.captureFrame();
            container.parentNode.insertBefore(captureBtn, container);
        });

        this.bindEvents();
        // 初始化时添加一次性错误处理
        const videoPlayer = document.getElementById('videoPlayer');
        this.setupErrorHandler(videoPlayer);
    }

    setupErrorHandler(videoPlayer) {
        let errorShown = false;
        videoPlayer.addEventListener('error', () => {
            // 如果是主动关闭模态框导致的，不显示错误
            if (!errorShown && !this.isClosing) {
                errorShown = true;
                Utils.showErrorMessage('视频加载失败');
                this.closeModal();
                setTimeout(() => {
                    errorShown = false;
                }, 1000);
            }
        });
    }

    playVideo(filename) {
        this.currentVideoFilename = filename;
        const modal = document.getElementById('videoModal');
        
        // 设置新的视频源
        this.player.source = {
            type: 'video',
            sources: [{
                src: `/play/${filename}`,
                type: 'video/mp4',
            }]
        };

        this.updateFilenameDisplay(filename);
        modal.style.display = 'block';
        
        // 自动播放
        this.player.play().catch(error => {
            console.error('视频播放失败:', error);
        });
    }

    closeModal() {
        const modal = document.getElementById('videoModal');
        this.isClosing = true;
        
        // 停止播放
        this.player.stop();
        modal.style.display = 'none';
        this.currentVideoFilename = null;
        
        setTimeout(() => {
            this.isClosing = false;
        }, 100);
    }

    async captureFrame() {
        try {
            // 使用 Plyr 的 API 获取原生视频元素
            const video = this.player.elements.original;
            
            // 检查视频元素是否有效
            if (!video || !video.videoWidth || !video.videoHeight) {
                Utils.showErrorMessage('视频尚未准备好，请等待一会再试');
                return;
            }
            
            // 暂停视频并等待一小段时间确保画面稳定
            const wasPlaying = this.player.playing;
            await this.player.pause();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            const canvas = document.createElement('canvas');
            
            try {
                // 设置画布尺寸为视频的实际尺寸
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                
                // 在画布上绘制当前视频帧
                const ctx = canvas.getContext('2d');
                if (!ctx) {
                    throw new Error('无法创建画布上下文');
                }
                
                // 尝试绘制视频帧
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                // 检查是否成功绘制
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                if (!imageData || !imageData.data.some(pixel => pixel !== 0)) {
                    throw new Error('无法捕获视频帧');
                }
                
                // 获取图片数据，使用较高的质量
                const base64Image = canvas.toDataURL('image/jpeg', 0.95);
                if (!base64Image || base64Image === 'data:,') {
                    throw new Error('无法生成图片数据');
                }
                
                const base64Data = base64Image.split(',')[1];
                if (!base64Data) {
                    throw new Error('图片数据格式错误');
                }

                // 发送请求前显示加载提示
                Utils.showSuccessMessage('正在保存封面...');

                // 发送请求
                const response = await Utils.apiRequest('/update', {
                    method: 'POST',
                    body: JSON.stringify({
                        filename: this.currentVideoFilename,
                        cover: base64Data
                    })
                });
                
                if (response.success) {
                    // 更新封面图片
                    const coverPath = `covers/${this.currentVideoFilename}.jpg`;
                    this.updateCoverImage(`/static/${coverPath}?t=${Date.now()}`);
                    Utils.showSuccessMessage('封面更新成功！');
                } else {
                    throw new Error(response.message || '更新失败');
                }
            } finally {
                // 如果之前在播放，则继续播放
                if (wasPlaying) {
                    this.player.play().catch(() => {});
                }
            }
        } catch (error) {
            console.error('捕获封面失败:', error);
            Utils.showErrorMessage(
                error.message === '无法获取图像数据' 
                    ? '请等待视频加载后再试' 
                    : error.message || '封面更新失败'
            );
        }
    }

    // 修改更新封面图片的方法
    updateCoverImage(imageSrc) {
        const videoCard = document.querySelector(`.video-card[data-filename="${this.currentVideoFilename}"]`);
        if (videoCard) {
            const coverImg = videoCard.querySelector('.cover img');
            if (coverImg) {
                coverImg.src = imageSrc;
            } else {
                const coverDiv = videoCard.querySelector('.cover');
                const img = document.createElement('img');
                img.src = imageSrc;
                img.alt = this.currentVideoFilename;
                coverDiv.innerHTML = '';
                coverDiv.appendChild(img);
            }
        }
    }

    async deleteVideo(filename) {
        const result = await Swal.fire({
            title: '确定要删除吗？',
            text: `你将删除视频 "${filename}"`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: '确定',
            cancelButtonText: '取消',
        });

        if (result.isConfirmed) {
            try {
                await Utils.apiRequest(`/delete_video/${filename}`, { method: 'DELETE' });
                this.removeVideoCard(filename);
                Utils.showSuccessMessage(`视频 "${filename}" 已成功删除`);
            } catch (error) {
                Utils.showErrorMessage(`删除视频失败: ${error.message}`);
            }
        }
    }

    bindEvents() {
        // 使用事件委托处理模态框点击事件
        document.addEventListener('click', (event) => {
            const modal = document.getElementById('videoModal');
            if (modal.style.display === 'block') {
                const modalContent = document.querySelector('.modal-content');
                if (!modalContent.contains(event.target) && !event.target.closest('.video-card')) {
                    this.closeModal();
                }
            }
        });

        // ESC键关闭模态框
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    updateFilenameDisplay(filename) {
        const filenameElement = document.getElementById('videoFilename');
        filenameElement.textContent = filename;
    }

    removeVideoCard(filename) {
        const videoCard = document.querySelector(`.video-card[data-filename="${filename}"]`);
        if (videoCard) {
            videoCard.classList.add('removing');
            setTimeout(() => videoCard.remove(), 300);
        }
    }
} 