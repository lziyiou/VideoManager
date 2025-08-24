from fastapi import APIRouter, Depends, Query, HTTPException, Request, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict
import os
import time
import asyncio
import logging
from ..core.database import get_db
from ..services.video_service import VideoService
from ..services.tag_service import TagService
from ..models.video import Video as VideoModel
from ..models.setting import Setting
from ..schemas.videos import Video
from ..schemas.page import Page
from ..schemas.tags import VideoTagUpdate
from ..core.scan_status import get_scan_status, reset_scan_status

logger = logging.getLogger(__name__)

videosRouter = APIRouter()

@videosRouter.get("/scan", summary="异步扫描视频文件")
def scan_videos(db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """异步扫描并同步视频文件"""
    # 重置扫描状态
    reset_scan_status()
    
    # 启动异步扫描任务
    background_tasks.add_task(VideoService.scan_videos, db)
    
    # 立即返回响应
    return JSONResponse({
        "message": "视频扫描任务已启动",
        "status": "processing"
    })

@videosRouter.get("/scan/progress", summary="获取视频扫描进度")
def get_scan_progress():
    """获取视频扫描进度"""
    return get_scan_status()

@videosRouter.get("/list", response_model=Page[Video], summary="获取视频列表")
def get_videos(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(12, description="返回的记录数"),
    keyword: str = Query(None, description="搜索关键词"),
    favorite: bool = Query(None, description="收藏状态"),
    tags: str = Query(None, description="标签ID列表，逗号分隔的字符串"),
    duration: str = Query(None, description="视频时长"),
    sort_by: str = Query('filename', description="排序字段"),
    seed: int = Query(None, description="随机排序种子"),
    db: Session = Depends(get_db)
):
    """获取视频列表，支持按关键字、收藏状态和标签ID进行过滤"""
    # 处理标签参数
    tag_list = None
    if tags:
        try:
            tag_list = [int(tag_id) for tag_id in tags.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tag format. Expected comma-separated integers.")
    
    videos, total = VideoService.get_videos_by_filters(
        db, 
        skip=skip, 
        limit=limit, 
        keyword=keyword,
        is_favorite=favorite,
        tags=tag_list,
        duration=duration,
        sort_by=sort_by,
        seed=seed
    )
    total_pages = (total + limit - 1) // limit
    return Page(
        total=total,
        total_pages=total_pages,
        items=[Video.model_validate(video) for video in videos]
    )

@videosRouter.get("/{video_id}", response_model=Video, summary="获取视频信息")
def get_video(video_id: int, db: Session = Depends(get_db)):
    """根据ID获取视频信息"""
    video = VideoService.get_video_by_id(db, video_id)
    return Video.model_validate(video)

@videosRouter.post("/{video_id}/favorite", summary="更新视频收藏状态")
def update_video_favorite(video_id: int, is_favorite: bool, db: Session = Depends(get_db)):
    """更新视频收藏状态"""
    success = VideoService.update_video_status(db, video_id, is_favorite=is_favorite)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update video favorite status")
    return {"message": "Video favorite status updated successfully"}

@videosRouter.post("/{video_id}/web_playable", summary="更新视频网页播放状态")
def update_video_web_playable(video_id: int, web_playable: bool, db: Session = Depends(get_db)):
    """更新视频网页播放状态"""
    success = VideoService.update_video_status(db, video_id, web_playable=web_playable)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update video web playable status")
    return {"message": "Video web playable status updated successfully"}

@videosRouter.get("/{video_id}/thumbnail", summary="获取视频缩略图")
def get_video_thumbnail(video_id: int, db: Session = Depends(get_db)):
    """获取视频缩略图，按需生成"""
    
    # 获取视频信息
    video = VideoService.get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 检查是否已有缩略图且文件存在
    if video.thumbnail_generated and video.thumbnail_path and os.path.exists(video.thumbnail_path):
        return FileResponse(video.thumbnail_path)
    
    # 按需生成缩略图
    try:
        thumbnail_path = VideoService.generate_thumbnail(video.filepath)
        if thumbnail_path and os.path.exists(thumbnail_path):
            # 更新数据库中的缩略图路径和状态
            video.thumbnail_path = thumbnail_path
            video.thumbnail_generated = True
            db.commit()
            logger.info(f"Generated thumbnail for video {video_id}: {thumbnail_path}")
            return FileResponse(thumbnail_path)
        else:
            # 标记生成失败，避免重复尝试
            video.thumbnail_generated = False
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to generate thumbnail")
    except Exception as e:
        # 标记生成失败
        video.thumbnail_generated = False
        db.commit()
        logger.error(f"Error generating thumbnail for video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate thumbnail")

@videosRouter.get("/{video_id}/stream", summary="流式播放视频")
async def stream_video(video_id: int, request: Request, db: Session = Depends(get_db)):
    """流式播放视频文件，支持自适应分块传输和网络拥塞控制"""
    try:
        # 获取视频信息
        video = VideoService.get_video_by_id(db, video_id)
        if not video:
            logger.warning(f"Video not found: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        # 获取root_directory设置
        root_dir = db.query(Setting).filter(Setting.key == "root_directory").first()
        if not root_dir or not root_dir.value:
            logger.error("Root directory not configured")
            raise HTTPException(status_code=404, detail="Root directory not set")
        
        # 获取视频文件完整路径
        video_path = os.path.join(root_dir.value, video.filepath)
        if not os.path.exists(video_path):
            logger.error(f"Video file not found at path: {video_path}")
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # 获取文件大小
        file_size = os.path.getsize(video_path)
        logger.info(f"Starting video stream for video_id: {video_id}, size: {file_size} bytes")
        
        # 自适应分块大小设置（根据文件大小调整）
        base_chunk_size = 512 * 1024  # 基础块大小512KB
        if file_size > 2 * 1024 * 1024 * 1024:  # 大于2GB
            chunk_size = 4 * 1024 * 1024  # 4MB
        elif file_size > 1024 * 1024 * 1024:  # 大于1GB
            chunk_size = 2 * 1024 * 1024  # 2MB
        elif file_size > 100 * 1024 * 1024:  # 大于100MB
            chunk_size = 1024 * 1024  # 1MB
        else:
            chunk_size = base_chunk_size
        
        # 设置超时和重试参数
        timeout = 60  # 增加超时时间到60秒
        max_retries = 3  # 最大重试次数
        retry_delay = 1  # 重试延迟（秒）
        
        # 获取和验证Range请求头
        range_header = request.headers.get("range")
        start = 0
        end = file_size - 1
        
        if range_header:
            try:
                range_data = range_header.replace("bytes=", "").split("-")
                start = int(range_data[0])
                if range_data[1]:
                    end = int(range_data[1])
                if not (0 <= start <= end < file_size):
                    raise ValueError("Range out of bounds")
            except ValueError as e:
                logger.warning(f"Invalid range header: {range_header}, error: {str(e)}")
                raise HTTPException(status_code=416, detail="Requested range not satisfiable")
        
        content_length = end - start + 1
        
        # 定义视频流生成器
        async def video_stream():
            retry_count = 0
            last_activity = time.time()
            last_throughput = 0
            congestion_window = chunk_size
            min_sleep = 0.001  # 最小休眠时间1ms
            max_sleep = 0.05   # 最大休眠时间50ms
            
            try:
                with open(video_path, "rb") as video_file:
                    video_file.seek(start)
                    remaining = content_length
                    
                    while remaining > 0:
                        current_time = time.time()
                        
                        # 检查超时
                        if current_time - last_activity > timeout:
                            logger.warning(f"Stream timeout for video {video_id}")
                            break
                        
                        try:
                            # 动态调整读取大小，确保使用整数类型
                            chunk_size_to_read = int(min(int(congestion_window), remaining, chunk_size))
                            read_start_time = current_time
                            
                            data = video_file.read(chunk_size_to_read)
                            if not data:
                                logger.info(f"Reached end of file for video {video_id}")
                                break
                            
                            # 计算传输速率和调整拥塞窗口
                            transfer_time = time.time() - read_start_time
                            if transfer_time > 0:
                                current_throughput = len(data) / transfer_time
                                throughput_ratio = current_throughput / (last_throughput if last_throughput > 0 else current_throughput)
                                
                                if throughput_ratio < 0.8:  # 速度下降超过20%
                                    # 更激进的拥塞窗口调整
                                    congestion_window = int(max(base_chunk_size, int(congestion_window * 0.7)))
                                    sleep_time = min(max_sleep, transfer_time * 0.1)
                                    await asyncio.sleep(sleep_time)
                                elif throughput_ratio > 1.2:  # 速度提升超过20%
                                    # 更保守的拥塞窗口增长
                                    congestion_window = int(min(chunk_size * 2, int(congestion_window * 1.2)))
                                    await asyncio.sleep(min_sleep)
                                else:
                                    # 保持稳定状态
                                    await asyncio.sleep(min_sleep)
                                    
                                last_throughput = current_throughput
                            
                            remaining -= len(data)
                            last_activity = time.time()
                            
                            yield data
                            
                        except (ConnectionResetError, BrokenPipeError) as e:
                            logger.error(f"Connection error while streaming video {video_id}: {str(e)}")
                            if retry_count < max_retries:
                                retry_count += 1
                                logger.info(f"Retrying stream for video {video_id}, attempt {retry_count}")
                                await asyncio.sleep(retry_delay)
                                continue
                            break
                            
                        except Exception as e:
                            logger.error(f"Unexpected error while streaming video {video_id}: {str(e)}")
                            break
                            
            except Exception as e:
                logger.error(f"Failed to stream video {video_id}: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")
            
            finally:
                logger.info(f"Stream completed for video {video_id}, remaining bytes: {remaining}")
        
        # 根据文件扩展名设置Content-Type
        file_ext = os.path.splitext(video_path)[1].lower()
        content_type_map = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv',
            '.m4v': 'video/x-m4v',
            '.3gp': 'video/3gpp',
            '.ts': 'video/mp2t',
            '.mpg': 'video/mpeg',
            '.mpeg': 'video/mpeg'
        }
        content_type = content_type_map.get(file_ext, 'application/octet-stream')
        
        # 设置响应头
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=31536000",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Connection": "keep-alive"
        }
        
        return StreamingResponse(
            video_stream(),
            status_code=206 if range_header else 200,
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Global error in stream_video for video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@videosRouter.put("/{video_id}/thumbnail", summary="设置视频缩略图")
async def set_video_thumbnail(video_id: int, thumbnail: UploadFile = File(...), db: Session = Depends(get_db)):
    """设置视频的缩略图"""
    # 获取视频信息
    video = VideoService.get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 验证文件类型
    if not thumbnail.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # 保存缩略图并更新数据库
    try:
        thumbnail_path = await VideoService.save_thumbnail(db, video_id, thumbnail)
        return {"message": "Thumbnail updated successfully", "thumbnail_path": thumbnail_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@videosRouter.put("/{video_id}", summary="重命名")
async def rename(video_id: int, new_name: str, db: Session = Depends(get_db)):
    """重命名视频文件"""
    # 获取视频信息
    video = VideoService.get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # 获取root_directory设置
    root_dir = db.query(Setting).filter(Setting.key == "root_directory").first()
    if not root_dir or not root_dir.value:
        raise HTTPException(status_code=404, detail="Root directory not set")

    # 获取视频文件完整路径
    video_path = os.path.join(root_dir.value, video.filepath)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    # 构建新的文件路径
    new_filepath = os.path.join(os.path.dirname(video_path), new_name)

    # 重命名文件，最多重试3次
    max_retries = 3
    retry_delay = 1  # 每次重试间隔1秒
    last_error = None
    
    for attempt in range(max_retries):
        try:
            os.rename(video_path, new_filepath)
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                # 如果不是最后一次尝试，等待后重试
                import time
                time.sleep(retry_delay)
                continue
            # 最后一次尝试也失败，返回错误
            error_msg = f"Failed to rename video file after {max_retries} attempts: {str(last_error)}"
            if "另一个程序正在使用此文件" in str(last_error):
                error_msg += "\n请确保没有其他程序（如播放器）正在使用该文件，然后重试。"
            raise HTTPException(status_code=500, detail=error_msg)

    # 更新数据库中的文件名和文件路径
    video.filename = new_name
    video.filepath = os.path.relpath(new_filepath, root_dir.value)
    db.commit()

    return {"message": "Video renamed successfully"}


@videosRouter.delete("/{video_id}", summary="删除视频文件")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    """删除视频文件"""
    # 获取视频信息
    video = VideoService.get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # 获取root_directory设置
    root_dir = db.query(Setting).filter(Setting.key == "root_directory").first()
    if not root_dir or not root_dir.value:
        raise HTTPException(status_code=404, detail="Root directory not set")

    # 获取视频文件完整路径
    video_path = os.path.join(root_dir.value, video.filepath)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    # 删除视频文件
    try:
        os.remove(video_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete video file: {str(e)}")

    # 删除数据库中的视频记录
    db.delete(video)
    db.commit()

    return {"message": "Video deleted successfully"}