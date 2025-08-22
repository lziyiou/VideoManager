import os
import time
import ffmpeg
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..models.video import Video
from ..models.setting import Setting
from ..models.tag import Tag
from fastapi import HTTPException, UploadFile
from sqlalchemy import func


class VideoService:
    @staticmethod
    def get_video_duration(filepath: str) -> float:
        """获取视频时长（秒）"""
        try:
            probe = ffmpeg.probe(filepath)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            duration = float(probe['format']['duration'])
            if duration <= 0:
                raise ValueError(f"Invalid duration value: {duration}")
            return duration
        except Exception as e:
            print(f"Error getting duration for {filepath}: {str(e)}")
            # 如果获取时长失败，返回一个负数表示错误
            return -1.0

    @staticmethod
    def _get_abs_path(root_dir, path):
        """确保路径为绝对路径"""
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(root_dir, path))

    @staticmethod
    def _safe_remove(path):
        """安全删除文件，处理被占用等异常，添加重试机制"""
        max_attempts = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_attempts):
            try:
                if os.path.exists(path):
                    os.remove(path)
                return True, ""
            except PermissionError as e:
                if hasattr(e, 'winerror') and e.winerror == 32:
                    error_msg = f"文件被占用，无法删除：{path}"
                    # 如果不是最后一次尝试，则等待后重试
                    if attempt < max_attempts - 1:
                        print(f"删除文件被占用，等待 {retry_delay} 秒后重试 (尝试 {attempt + 1}/{max_attempts})")
                        time.sleep(retry_delay)
                        continue
                    return False, error_msg
                return False, f"删除文件失败：{str(e)}"
            except Exception as e:
                return False, f"删除文件失败：{str(e)}"
        return False, f"删除文件失败：达到最大重试次数 ({max_attempts})"

    @staticmethod
    def _update_progress(processed, total, msg):
        from ..core.scan_status import update_scan_progress
        progress = processed / total if total > 0 else 0
        update_scan_progress(progress, msg)

    @staticmethod
    def scan_videos(db: Session) -> None:
        import concurrent.futures
        from datetime import datetime
        from ..core.scan_status import update_scan_progress
        root_dir = db.query(Setting).filter(Setting.key == "root_directory").first()
        if not root_dir or not root_dir.value:
            update_scan_progress(0, "未设置根目录", True)
            return
        root_path = os.path.abspath(root_dir.value)
        update_scan_progress(0, "正在清理不存在的视频记录...")
        all_videos = db.query(Video).all()
        deleted_count = 0
        for video in all_videos:
            abs_path = VideoService._get_abs_path(root_path, video.filepath)
            if not os.path.exists(abs_path) or not abs_path.startswith(root_path):
                db.delete(video)
                deleted_count += 1
        if deleted_count > 0:
            db.commit()
            update_scan_progress(0, f"已清理 {deleted_count} 个无效的视频记录...")
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '3gp', 'ts', '.flv', '.webm', '.m3u8', 'mpeg')
        def process_video_file(file_info):
            filepath, rel_path = file_info
            try:
                video = db.query(Video).filter(Video.filepath == filepath).first()
                if not video:
                    video = db.query(Video).filter(Video.filepath == rel_path).first()
                    if video:
                        video.filepath = filepath
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if video and video.updated_at and video.updated_at >= file_mtime:
                    return None
                size = os.path.getsize(filepath) / (1024 * 1024)
                duration = VideoService.get_video_duration(filepath)
                if duration > 0:
                    thumbnail_path = VideoService.generate_thumbnail(filepath)
                    if video:
                        video.size = round(size, 2)
                        video.duration = duration
                        video.thumbnail_path = thumbnail_path
                        video.updated_at = datetime.now()
                    else:
                        video = Video(
                            filename=os.path.basename(filepath),
                            filepath=filepath,
                            size=round(size, 2),
                            duration=duration,
                            thumbnail_path=thumbnail_path,
                            updated_at=datetime.now()
                        )
                        db.add(video)
                    return video
            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")
            return None
        try:
            video_files = []
            update_scan_progress(0, "正在扫描视频文件...")
            for root, _, files in os.walk(root_path):
                for file in files:
                    if file.lower().endswith(video_extensions):
                        filepath = os.path.abspath(os.path.join(root, file))
                        rel_path = os.path.relpath(filepath, root_path)
                        video_files.append((filepath, rel_path))
            if not video_files:
                update_scan_progress(1, "未找到视频文件", True)
                return
            total_files = len(video_files)
            processed_files = 0
            def update_progress():
                nonlocal processed_files
                VideoService._update_progress(processed_files, total_files, f"正在处理第 {processed_files}/{total_files} 个文件...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(process_video_file, file_info) for file_info in video_files]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                        processed_files += 1
                        update_progress()
                    except Exception as e:
                        print(f"Error processing video: {str(e)}")
            db.commit()
            update_scan_progress(1, "扫描完成", True)
        except Exception as e:
            print(f"Scan error: {str(e)}")
            update_scan_progress(1, f"扫描出错: {str(e)}", True)

    @staticmethod
    def get_total_videos(db: Session) -> int:
        """获取视频总数"""
        return db.query(Video).count()

    @staticmethod
    def get_video_by_id(db: Session, video_id: int) -> Optional[Video]:
        """根据ID获取视频信息"""
        return db.query(Video).filter(Video.id == video_id).first()

    @staticmethod
    def generate_thumbnail(video_path: str) -> str:
        """生成视频缩略图"""
        try:
            # 确保thumbnails目录存在
            video_dir = os.path.dirname(video_path)
            thumbnails_dir = os.path.join(video_dir, 'thumbnails')
            os.makedirs(thumbnails_dir, exist_ok=True)

            # 生成缩略图文件名
            thumbnail_filename = f"{os.path.basename(video_path).replace('.', '_')}_thumb.jpg"
            thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)

            # 检查是否已经存在同名的缩略图文件
            if os.path.exists(thumbnail_path):
                return thumbnail_path

            # 使用ffmpeg生成缩略图
            stream = ffmpeg.input(video_path, ss='00:00:01')
            stream = ffmpeg.filter(stream, 'scale', 320, -1)
            stream = ffmpeg.output(stream, thumbnail_path, vframes=1)
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            return thumbnail_path
        except Exception as e:
            print(f"Error generating thumbnail for {video_path}: {str(e)}")
            return ""

    @staticmethod
    def get_thumbnail(db: Session, video_id: int) -> str:
        """获取视频缩略图路径"""
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return video.thumbnail_path

    @staticmethod
    def update_video_status(db: Session, video_id: int, is_favorite: bool = None, web_playable: bool = None) -> bool:
        """更新视频的标记状态"""
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            if is_favorite is not None:
                video.is_favorite = 1 if is_favorite else 0
            if web_playable is not None:
                video.web_playable = 1 if web_playable else 0
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error updating video status: {str(e)}")
            return False

    @staticmethod
    async def save_thumbnail(db: Session, video_id: int, thumbnail_file: UploadFile) -> str:
        """保存上传的缩略图文件并更新数据库"""
        try:
            # 获取视频信息
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")

            # 确保thumbnails目录存在
            video_dir = os.path.dirname(video.filepath)
            thumbnails_dir = os.path.join(video_dir, 'thumbnails')
            os.makedirs(thumbnails_dir, exist_ok=True)

            # 生成缩略图文件名
            thumbnail_filename = f"{os.path.basename(video.filename).replace('.', '_')}_thumb.jpg"
            thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
            
            # 读取并保存文件
            content = await thumbnail_file.read()
            with open(thumbnail_path, "wb") as f:
                f.write(content)
            
            # 更新数据库中的缩略图路径
            video.thumbnail_path = thumbnail_path
            video.updated_at = datetime.now()
            db.commit()
            
            return thumbnail_path
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save thumbnail: {str(e)}")

    @staticmethod
    def delete_video(db: Session, video_id: int) -> bool:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return False
        try:
            root_dir_setting = db.query(Setting).filter(Setting.key == "root_directory").first()
            root_dir = os.path.abspath(root_dir_setting.value) if root_dir_setting else None
            video_filepath = VideoService._get_abs_path(root_dir, video.filepath)
            ok, msg = VideoService._safe_remove(video_filepath)
            if not ok:
                print(msg)
                return False
            thumbnail_path = video.thumbnail_path
            if thumbnail_path:
                ok, msg = VideoService._safe_remove(thumbnail_path)
                if not ok:
                    print(msg)
                    return False
            db.delete(video)
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting video {video_id}: {str(e)}")
            db.rollback()
            return False

    @staticmethod
    def get_videos_by_filters(db: Session, skip: int = 0, limit: int = 12, 
                    keyword: str = None, is_favorite: bool = None,
                    tags: List[int] = None,
                    duration: str = None,
                    sort_by: str = 'filename',
                    seed: int = None) -> tuple[List[Video], int]:
        """按条件过滤视频列表，支持关键字搜索、收藏状态和标签ID过滤"""
        query = db.query(Video).distinct()
        
        # 添加关键字过滤
        if keyword:
            query = query.filter(Video.filename.ilike(f"%{keyword}%"))
        
        # 添加收藏状态过滤
        if is_favorite is not None:
            query = query.filter(Video.is_favorite == (1 if is_favorite else 0))
        
        # 添加标签过滤
        if tags and len(tags) > 0:
            # 对每个标签ID应用一个子查询，确保视频包含所有选中的标签
            for tag_id in tags:
                query = query.filter(Video.tags.any(Tag.id == tag_id))

        # 从设置中获取短视频时长阈值（分钟）
        short_duration_setting = db.query(Setting).filter(Setting.key == "short_video_duration").first()
        short_duration = float(short_duration_setting.value) if short_duration_setting else 5.0

        # 添加时长过滤
        if duration:
            if duration == "short":
                query = query.filter(Video.duration <= short_duration * 60)
            elif duration == "long":
                query = query.filter(Video.duration > short_duration * 60)

        # 排序
        if sort_by:
            if sort_by == 'filename':
                query = query.order_by(Video.filename.asc())
            elif sort_by == 'duration':
                query = query.order_by(Video.duration.desc())
            elif sort_by == 'size':
                query = query.order_by(Video.size.desc())
            elif sort_by == 'created_at':
                query = query.order_by(Video.created_at.desc())
            elif sort_by == 'random':
                if seed is not None:
                    # 把 seed 压缩到 64-bit
                    int_seed = abs(seed) % (2**63)

                    # Python 里算好乘加模，得到一个 31-bit 正整数
                    multiplier  = 2654435761
                    addend      = 1103515245
                    final_mod   = 2147483647
                    # 注意：先乘后模，保证不会溢出 Python int
                    scramble_value = (int_seed * addend) % final_mod

                    # 现在只把 scramble_value 作为绑定参数
                    hash_expr = func.abs(
                        (Video.id * multiplier + scramble_value) % final_mod
                    )
                    query = query.order_by(hash_expr)
                else:
                    query = query.order_by(func.random())

        # 获取总数和分页数据
        total = query.count()
        videos = query.offset(skip).limit(limit).all()
        
        return videos, total

    @staticmethod
    def get_all_tags(db: Session) -> List[Tag]:
        """获取所有标签列表"""
        return db.query(Tag).all()

    @staticmethod
    def create_tag(db: Session, tag_name: str) -> Tag:
        """创建新标签"""
        tag = Tag(name=tag_name)
        try:
            db.add(tag)
            db.commit()
            db.refresh(tag)
            return tag
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"创建标签失败：{str(e)}")

    @staticmethod
    def add_tags_to_video(db: Session, video_id: int, tag_names: List[str]) -> bool:
        """为视频添加标签"""
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")

            for tag_name in tag_names:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                if tag not in video.tags:
                    video.tags.append(tag)

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"添加标签失败：{str(e)}")

    @staticmethod
    def remove_tag_from_video(db: Session, video_id: int, tag_name: str) -> bool:
        """从视频中移除标签"""
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")

            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if tag and tag in video.tags:
                video.tags.remove(tag)
                db.commit()

            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"移除标签失败：{str(e)}")