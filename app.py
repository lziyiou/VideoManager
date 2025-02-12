import base64

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from config import Config, VIDEO_FOLDER, COVERS_FOLDER
from moviepy.editor import VideoFileClip

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
    videos = []
    for f in os.listdir(VIDEO_FOLDER):
        if f.lower().endswith(('.mp4', '.avi', '.mkv')):
            video = Video.query.filter_by(filename=f).first()
            cover_path = os.path.join(COVERS_FOLDER, f"{f}.jpg")
            if not os.path.exists(cover_path):
                generate_cover(os.path.join(VIDEO_FOLDER, f), cover_path)
                if not video:
                    video = Video(filename=f, cover=f"covers/{f}.jpg")
                    db.session.add(video)
                    db.session.commit()
            videos.append({
                'filename': f,
                'tags': [tag.name for tag in video.tags] if video else [],
                'cover': video.cover if video else ''
            })
    return render_template('index.html', videos=videos)


@app.route('/update', methods=['POST'])
def update():
    data = request.json
    video = Video.query.filter_by(filename=data['filename']).first()
    if not video:
        video = Video(filename=data['filename'])
        db.session.add(video)

    if 'tags' in data:
        # 获取或创建标签
        tag_names = set(data['tags'])  # 去重
        tags = []
        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)
            tags.append(tag)

        # 更新视频的标签
        video.tags = tags

    if 'cover' in data:
        cover_path = f"covers/{data['filename']}.jpg"
        with open(os.path.join(COVERS_FOLDER, f"{data['filename']}.jpg"), 'wb') as f:
            imgdata = base64.b64decode(data['cover'])
            f.write(imgdata)
        video.cover = cover_path

    db.session.commit()

    # 清理未使用的标签
    cleanup_unused_tags()

    return jsonify(success=True)


@app.route('/play/<filename>')
def play(filename):
    os.path.join(VIDEO_FOLDER, filename)
    return send_from_directory(
        VIDEO_FOLDER,  # 视频存储路径
        filename,
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
            os.remove(video_path)

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
