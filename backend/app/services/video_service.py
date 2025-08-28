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
            
            # 首先尝试从format中获取时长
            if 'format' in probe and 'duration' in probe['format']:
                duration = float(probe['format']['duration'])
                if duration > 0:
                    return duration
            
            # 如果format中没有时长信息，尝试从视频流中获取
            video_streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'video']
            if video_streams:
                video_info = video_streams[0]
                if 'duration' in video_info:
                    duration = float(video_info['duration'])
                    if duration > 0:
                        return duration
            
            # 如果都没有找到有效时长，返回错误值
            print(f"No valid duration found for {filepath}")
            return -1.0
            
        except ffmpeg.Error as e:
            print(f"FFmpeg error getting duration for {filepath}: {str(e)}")
            return -1.0
        except Exception as e:
            print(f"Error getting duration for {filepath}: {str(e)}")
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
        cleaned_thumbnails = 0
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        for video in all_videos:
            abs_path = VideoService._get_abs_path(root_path, video.filepath)
            if not os.path.exists(abs_path) or not abs_path.startswith(root_path):
                # 删除对应的缩略图文件
                if video.thumbnail_path:
                    thumbnail_abs_path = os.path.join(project_root, video.thumbnail_path)
                    if os.path.exists(thumbnail_abs_path):
                        try:
                            os.remove(thumbnail_abs_path)
                            cleaned_thumbnails += 1
                            print(f"Deleted orphaned thumbnail: {thumbnail_abs_path}")
                        except Exception as e:
                            print(f"Failed to delete thumbnail {thumbnail_abs_path}: {str(e)}")
                
                db.delete(video)
                deleted_count += 1
        
        if deleted_count > 0:
            db.commit()
            message = f"已清理 {deleted_count} 个无效的视频记录"
            if cleaned_thumbnails > 0:
                message += f"和 {cleaned_thumbnails} 个对应的缩略图文件"
            update_scan_progress(0, message + "...")
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '3gp', 'ts', '.flv', '.webm', '.m3u8', 'mpeg')
        def process_video_file(file_info):
            filepath, rel_path = file_info
            try:
                # 使用原生SQL查询避免ORM问题
                from sqlalchemy import text
                result = db.execute(text(
                    "SELECT id FROM videos WHERE filepath = :rel_path OR filepath = :full_path LIMIT 1"
                ), {"rel_path": rel_path, "full_path": filepath})
                existing_id = result.scalar()
                
                # 检查文件修改时间，如果数据库记录较新则跳过
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if existing_id:
                    video = db.query(Video).filter(Video.id == existing_id).first()
                    if video and video.updated_at and video.updated_at >= file_mtime:
                        return None
                
                # 获取文件信息
                size = os.path.getsize(filepath) / (1024 * 1024)
                duration = VideoService.get_video_duration(filepath)
                
                if duration > 0:
                    # 扫描时不生成缩略图，只保存基本信息
                    if existing_id:
                        # 使用原生SQL更新现有记录
                        db.execute(text(
                            "UPDATE videos SET filepath = :rel_path, size = :size, duration = :duration, updated_at = :updated_at WHERE id = :id"
                        ), {
                            "rel_path": rel_path,
                            "size": round(size, 2),
                            "duration": duration,
                            "updated_at": datetime.now(),
                            "id": existing_id
                        })
                        # 返回更新后的视频对象
                        return db.query(Video).filter(Video.id == existing_id).first()
                    else:
                        # 创建新记录
                        video = Video(
                            filename=os.path.basename(filepath),
                            filepath=rel_path,  # 使用相对路径存储
                            size=round(size, 2),
                            duration=duration,
                            thumbnail_path=None,  # 扫描时不生成缩略图
                            thumbnail_generated=False,  # 标记缩略图未生成
                            updated_at=datetime.now()
                        )
                        db.add(video)
                        return video
            except Exception as e:
                import traceback
                print(f"Error processing {filepath}: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                
                # 如果是数据库约束错误，尝试查找已存在的记录并更新
                if "UNIQUE constraint failed" in str(e):
                    try:
                        existing_video = db.query(Video).filter(
                            (Video.filepath == rel_path) | (Video.filepath == filepath)
                        ).first()
                        if existing_video:
                            existing_video.filepath = rel_path
                            try:
                                existing_video.size = round(os.path.getsize(filepath) / (1024 * 1024), 2)
                                existing_video.duration = VideoService.get_video_duration(filepath)
                                existing_video.updated_at = datetime.now()
                                return existing_video
                            except Exception as size_e:
                                print(f"Error updating file info for {filepath}: {str(size_e)}")
                                return existing_video
                    except Exception as inner_e:
                        print(f"Error handling duplicate record for {filepath}: {str(inner_e)}")
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
            # 使用批量处理来减少数据库锁定时间
            batch_size = 10
            for i in range(0, len(video_files), batch_size):
                batch = video_files[i:i + batch_size]
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [executor.submit(process_video_file, file_info) for file_info in batch]
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            result = future.result()
                            processed_files += 1
                            update_progress()
                        except Exception as e:
                            print(f"Error processing video: {str(e)}")
                            processed_files += 1  # 即使出错也要增加计数
                            update_progress()
                
                # 每个批次提交一次
                try:
                    db.commit()
                except Exception as e:
                    print(f"Error committing batch: {str(e)}")
                    db.rollback()
            
            # 最终提交
            try:
                db.commit()
            except Exception as e:
                print(f"Error in final commit: {str(e)}")
                db.rollback()
            
            # 扫描完成后清理孤立的缩略图文件
            update_scan_progress(0.95, "正在清理孤立的缩略图文件...")
            try:
                cleanup_result = VideoService.cleanup_orphaned_thumbnails(db)
                if cleanup_result["success"] and cleanup_result["cleaned_count"] > 0:
                    print(f"Cleaned {cleanup_result['cleaned_count']} orphaned thumbnails during scan")
                    update_scan_progress(1, f"扫描完成，清理了 {cleanup_result['cleaned_count']} 个孤立缩略图", True)
                else:
                    update_scan_progress(1, "扫描完成", True)
            except Exception as e:
                print(f"Error cleaning thumbnails during scan: {str(e)}")
                update_scan_progress(1, "扫描完成（缩略图清理失败）", True)
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
    def generate_thumbnail(video_path: str, force_regenerate: bool = False, old_thumbnail_path: str = None) -> str:
        """生成视频缩略图
        
        Args:
            video_path: 视频文件路径
            force_regenerate: 是否强制重新生成缩略图
            old_thumbnail_path: 旧的缩略图路径，如果提供则在生成新缩略图前删除
        """
        try:
            # 使用项目根目录下的thumbnails目录，而不是视频文件所在目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            thumbnails_dir = os.path.join(project_root, 'thumbnails')
            os.makedirs(thumbnails_dir, exist_ok=True)

            # 生成缩略图文件名，使用视频文件的完整路径hash来避免重名
            import hashlib
            path_hash = hashlib.md5(video_path.encode()).hexdigest()[:8]
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            thumbnail_filename = f"{video_name}_{path_hash}_thumb.jpg"
            thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)

            # 如果提供了旧缩略图路径，先删除旧文件
            if old_thumbnail_path:
                old_thumbnail_abs_path = os.path.join(project_root, old_thumbnail_path) if not os.path.isabs(old_thumbnail_path) else old_thumbnail_path
                if os.path.exists(old_thumbnail_abs_path) and old_thumbnail_abs_path != thumbnail_path:
                    try:
                        os.remove(old_thumbnail_abs_path)
                        print(f"Deleted old thumbnail: {old_thumbnail_abs_path}")
                    except Exception as e:
                        print(f"Failed to delete old thumbnail {old_thumbnail_abs_path}: {str(e)}")

            # 检查是否已经存在同名的缩略图文件
            if os.path.exists(thumbnail_path) and not force_regenerate:
                return os.path.relpath(thumbnail_path, project_root)

            # 如果强制重新生成，删除现有文件
            if force_regenerate and os.path.exists(thumbnail_path):
                try:
                    os.remove(thumbnail_path)
                    print(f"Deleted existing thumbnail for regeneration: {thumbnail_path}")
                except Exception as e:
                    print(f"Failed to delete existing thumbnail {thumbnail_path}: {str(e)}")

            # 使用ffmpeg生成缩略图
            stream = ffmpeg.input(video_path, ss='00:00:01')
            stream = ffmpeg.filter(stream, 'scale', 320, -1)
            stream = ffmpeg.output(stream, thumbnail_path, vframes=1)
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            # 验证缩略图文件是否成功生成
            if not os.path.exists(thumbnail_path) or os.path.getsize(thumbnail_path) == 0:
                raise Exception("Generated thumbnail file is empty or does not exist")
            
            # 返回相对路径
            return os.path.relpath(thumbnail_path, project_root)
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

            # 使用项目根目录下的thumbnails目录，而不是视频文件所在目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            thumbnails_dir = os.path.join(project_root, 'thumbnails')
            os.makedirs(thumbnails_dir, exist_ok=True)

            # 如果已有缩略图，先删除旧文件
            if video.thumbnail_path:
                old_thumbnail_abs_path = os.path.join(project_root, video.thumbnail_path)
                if os.path.exists(old_thumbnail_abs_path):
                    try:
                        os.remove(old_thumbnail_abs_path)
                        print(f"Deleted old thumbnail: {old_thumbnail_abs_path}")
                    except Exception as e:
                        print(f"Failed to delete old thumbnail {old_thumbnail_abs_path}: {str(e)}")

            # 生成缩略图文件名，使用视频文件的完整路径hash来避免重名
            import hashlib
            path_hash = hashlib.md5(video.filepath.encode()).hexdigest()[:8]
            video_name = os.path.splitext(os.path.basename(video.filename))[0]
            thumbnail_filename = f"{video_name}_{path_hash}_thumb.jpg"
            thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
            
            # 读取并保存文件
            content = await thumbnail_file.read()
            with open(thumbnail_path, "wb") as f:
                f.write(content)
            
            # 更新数据库中的缩略图路径（存储相对路径）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            video.thumbnail_path = os.path.relpath(thumbnail_path, project_root)
            video.thumbnail_generated = True
            video.updated_at = datetime.now()
            db.commit()
            
            return thumbnail_path
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save thumbnail: {str(e)}")

    @staticmethod
    def cleanup_orphaned_thumbnails(db: Session) -> dict:
        """清理孤立的缩略图文件"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            thumbnails_dir = os.path.join(project_root, 'thumbnails')
            
            if not os.path.exists(thumbnails_dir):
                return {"success": True, "message": "缩略图目录不存在", "cleaned_count": 0, "cleaned_size": 0}
            
            # 获取所有缩略图文件
            thumbnail_files = []
            for file in os.listdir(thumbnails_dir):
                if file.endswith('_thumb.jpg'):
                    thumbnail_files.append(file)
            
            if not thumbnail_files:
                return {"success": True, "message": "没有找到缩略图文件", "cleaned_count": 0, "cleaned_size": 0}
            
            # 获取数据库中的所有视频记录
            videos = db.query(Video).all()
            
            # 生成所有期望的缩略图文件名
            expected_thumbnails = set()
            db_thumbnail_paths = set()
            
            for video in videos:
                # 根据视频信息生成期望的缩略图文件名
                import hashlib
                path_hash = hashlib.md5(video.filepath.encode()).hexdigest()[:8]
                video_name = os.path.splitext(video.filename)[0]
                expected_name = f"{video_name}_{path_hash}_thumb.jpg"
                expected_thumbnails.add(expected_name)
                
                # 如果数据库中有缩略图路径，也加入到期望列表中
                if video.thumbnail_path:
                    db_thumbnail_name = os.path.basename(video.thumbnail_path)
                    db_thumbnail_paths.add(db_thumbnail_name)
            
            # 合并期望的缩略图文件名
            all_expected = expected_thumbnails.union(db_thumbnail_paths)
            
            # 找出并删除孤立的缩略图文件
            cleaned_count = 0
            cleaned_size = 0
            
            for thumbnail_file in thumbnail_files:
                if thumbnail_file not in all_expected:
                    file_path = os.path.join(thumbnails_dir, thumbnail_file)
                    if os.path.exists(file_path):
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleaned_count += 1
                            cleaned_size += file_size
                            print(f"Deleted orphaned thumbnail: {thumbnail_file}")
                        except Exception as e:
                            print(f"Failed to delete orphaned thumbnail {thumbnail_file}: {str(e)}")
            
            return {
                "success": True,
                "message": f"清理完成，删除了 {cleaned_count} 个孤立的缩略图文件",
                "cleaned_count": cleaned_count,
                "cleaned_size": cleaned_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"清理失败: {str(e)}",
                "cleaned_count": 0,
                "cleaned_size": 0
            }

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
                # 构建缩略图的绝对路径
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                thumbnail_abs_path = os.path.join(project_root, thumbnail_path)
                ok, msg = VideoService._safe_remove(thumbnail_abs_path)
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

    @staticmethod
    def update_video_progress(db: Session, video_id: int, last_position: float, 
                            watch_progress: float = None, is_completed: bool = None) -> bool:
        """更新视频播放进度"""
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return False

            video.last_position = last_position
            video.last_watched_at = datetime.now()
            
            if watch_progress is not None:
                video.watch_progress = watch_progress
            else:
                # 自动计算观看进度百分比
                if video.duration > 0:
                    video.watch_progress = min(100.0, (last_position / video.duration) * 100)
            
            if is_completed is not None:
                video.is_completed = is_completed
            else:
                # 自动判断是否看完（观看进度超过95%）
                video.is_completed = video.watch_progress >= 95.0

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error updating video progress: {str(e)}")
            return False

    @staticmethod
    def get_video_progress(db: Session, video_id: int) -> dict:
        """获取视频播放进度"""
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return None

            return {
                "video_id": video.id,
                "last_position": video.last_position,
                "watch_progress": video.watch_progress,
                "last_watched_at": video.last_watched_at,
                "is_completed": video.is_completed
            }
        except Exception as e:
            print(f"Error getting video progress: {str(e)}")
            return None

    @staticmethod
    def get_recently_watched_videos(db: Session, limit: int = 10) -> List[Video]:
        """获取最近观看的视频列表"""
        try:
            return db.query(Video).filter(
                Video.last_watched_at.isnot(None)
            ).order_by(
                Video.last_watched_at.desc()
            ).limit(limit).all()
        except Exception as e:
            print(f"Error getting recently watched videos: {str(e)}")
            return []

    @staticmethod
    def get_continue_watching_videos(db: Session, limit: int = 10) -> List[Video]:
        """获取可继续观看的视频列表（有播放进度但未看完）"""
        try:
            return db.query(Video).filter(
                Video.last_position > 0,
                Video.is_completed == False,
                Video.last_watched_at.isnot(None)
            ).order_by(
                Video.last_watched_at.desc()
            ).limit(limit).all()
        except Exception as e:
            print(f"Error getting continue watching videos: {str(e)}")
            return []

    @staticmethod
    def clear_video_progress(db: Session, video_id: int) -> bool:
        """清除视频播放进度"""
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return False

            video.last_position = 0.0
            video.watch_progress = 0.0
            video.last_watched_at = None
            video.is_completed = False

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error clearing video progress: {str(e)}")
            return False