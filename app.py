import base64

from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import os
from config import Config, VIDEO_FOLDER, COVERS_FOLDER
from moviepy.editor import VideoFileClip
from sqlalchemy import func

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# 确保封面目录存在
os.makedirs(COVERS_FOLDER, exist_ok=True)


# 标签模型
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)


# 视频模型
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    cover = db.Column(db.String(255))

    # 多对多关系
    tags = db.relationship(
        'Tag',
        secondary='video_tags',  # 中间表名称
        backref=db.backref('videos', lazy='dynamic'),
        lazy='dynamic'
    )


# 中间表
video_tags = db.Table(
    'video_tags',
    db.Column('video_id', db.Integer, db.ForeignKey('video.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


# 自动生成视频封面
def generate_cover(video_path, cover_path):
    clip = VideoFileClip(video_path)
    clip.save_frame(cover_path, t=0)  # 提取第 1 秒的画面作为封面
    clip.close()


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 8  # 每页显示8个视频
    
    # 首先扫描视频目录，确保数据库中的记录是最新的
    video_files = set()
    for f in os.listdir(VIDEO_FOLDER):
        if f.lower().endswith(('.mp4', '.avi', '.mkv', '.ts', '.mpeg', '.wmv')):
            full_path = os.path.join(VIDEO_FOLDER, f)
            if os.path.isfile(full_path):  # 确保是文件而不是目录
                video_files.add(f)
                # 检查数据库中是否存在该视频记录
                video = Video.query.filter_by(filename=f).first()
                if not video:
                    # 如果数据库中没有，则添加新记录
                    video = Video(filename=f)
                    db.session.add(video)
                
                # 检查并生成封面
                cover_path = os.path.join(COVERS_FOLDER, f"{f}.jpg")
                if not os.path.exists(cover_path):
                    generate_cover(full_path, cover_path)
                    video.cover = f"covers/{f}.jpg"

    # 删除数据库中不存在的视频记录
    for video in Video.query.all():
        if video.filename not in video_files:
            db.session.delete(video)
    
    db.session.commit()
    
    # 获取分页后的视频数据
    pagination = Video.query.paginate(
        page=page, 
        per_page=per_page,
        error_out=False
    )
    
    # 准备视频数据
    videos = []
    for video in pagination.items:
        videos.append({
            'filename': video.filename,
            'tags': [tag.name for tag in video.tags],
            'cover': video.cover
        })
    
    return render_template('index.html', 
                         videos=videos, 
                         current_page=page,
                         total_pages=pagination.pages)


@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.get_json()
        filename = data.get('filename')
        if not filename:
            return jsonify({'success': False, 'message': '文件名不能为空'}), 400

        # 处理标签更新
        if 'tags' in data:
            tags = data.get('tags', [])
            video = Video.query.filter_by(filename=filename).first()
            if not video:
                return jsonify({'success': False, 'message': '视频不存在'}), 404
            
            # 清除现有标签
            video.tags = []
            
            # 添加新标签
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                video.tags.append(tag)
            
            db.session.commit()
            return jsonify({'success': True})

        # 处理封面更新
        if 'cover' in data:
            cover_data = data.get('cover')
            if not cover_data:
                return jsonify({'success': False, 'message': '封面数据不能为空'}), 400

            # 确保封面目录存在
            if not os.path.exists(COVERS_FOLDER):
                os.makedirs(COVERS_FOLDER)

            # 保存封面图片
            cover_filename = f"{filename}.jpg"
            cover_path = os.path.join(COVERS_FOLDER, cover_filename)
            
            # 解码 base64 数据并保存为图片
            import base64
            try:
                image_data = base64.b64decode(cover_data)
                with open(cover_path, 'wb') as f:
                    f.write(image_data)
            except Exception as e:
                return jsonify({'success': False, 'message': f'保存封面失败: {str(e)}'}), 500

            # 更新数据库中的封面路径
            video = Video.query.filter_by(filename=filename).first()
            if video:
                video.cover = f"covers/{cover_filename}"
                db.session.commit()

            return jsonify({'success': True})

        return jsonify({'success': False, 'message': '无效的更新请求'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/play/<filename>')
def play(filename):
    video_path = os.path.join(VIDEO_FOLDER, filename)
    return send_file(
        video_path,
        mimetype='video/mp4',
        as_attachment=False,
        conditional=True  # 启用范围请求
    )


@app.route('/get-tags', methods=['GET'])
def get_tags():
    tags = [tag.name for tag in Tag.query.all()]
    return jsonify(tags)


@app.route('/delete_video/<filename>', methods=['DELETE'])
def delete_video(filename):
    try:
        # 查询数据库中的视频记录
        video = Video.query.filter_by(filename=filename).first()
        if not video:
            return jsonify(success=False, message="视频不存在"), 404

        # 删除封面文件（如果存在）
        cover_path = os.path.join(COVERS_FOLDER, f"{filename}.jpg")
        if os.path.exists(cover_path):
            os.remove(cover_path)

        # 删除视频文件
        video_path = os.path.join(VIDEO_FOLDER, filename)
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
                print("文件删除成功:", video_path)
            except PermissionError:
                print("权限不足，无法删除文件:", video_path)
            except Exception as e:
                print("删除文件时发生未知错误:", str(e))

        # 从数据库中删除记录
        db.session.delete(video)
        db.session.commit()

        # 清理未使用的标签
        cleanup_unused_tags()

        return jsonify(success=True, message="视频删除成功")
    except Exception as e:
        return jsonify(success=False, message=f"删除失败: {str(e)}"), 500


def cleanup_unused_tags():
    """
    清理未使用的标签（即没有关联任何视频的标签）
    """
    # 查询所有没有关联视频的标签
    unused_tags = Tag.query.filter(~Tag.videos.any()).all()
    for tag in unused_tags:
        db.session.delete(tag)
    db.session.commit()


@app.route('/search')
def search():
    page = request.args.get('page', 1, type=int)
    per_page = 8
    name_query = request.args.get('name', '').lower()
    tag_query = request.args.getlist('tags[]')  # 获取多个标签

    # 构建查询
    query = Video.query
    
    # 按名称搜索
    if name_query:
        query = query.filter(func.lower(Video.filename).like(f'%{name_query}%'))
    
    # 按标签搜索
    if tag_query:
        for tag in tag_query:
            query = query.filter(Video.tags.any(Tag.name == tag))
    
    # 获取分页数据
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # 准备视频数据
    videos = []
    for video in pagination.items:
        videos.append({
            'filename': video.filename,
            'tags': [tag.name for tag in video.tags],
            'cover': video.cover
        })
    
    return jsonify({
        'videos': videos,
        'current_page': page,
        'total_pages': pagination.pages
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
