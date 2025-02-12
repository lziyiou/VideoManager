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


# 数据库模型
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    tags = db.Column(db.String(255))
    cover = db.Column(db.String(255))


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
                'tags': video.tags.split(',') if video and video.tags else [],
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
        video.tags = ','.join(data['tags'])

    if 'cover' in data:
        cover_path = f"covers/{data['filename']}.jpg"
        with open(os.path.join(COVERS_FOLDER, f"{data['filename']}.jpg"), 'wb') as f:
            imgdata = base64.b64decode(data['cover'])
            f.write(imgdata)
        video.cover = cover_path

    db.session.commit()
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
    # 从数据库中提取所有标签
    all_tags = set()
    videos = Video.query.all()
    for video in videos:
        if video.tags:
            all_tags.update(video.tags.split(','))
    return jsonify(list(all_tags))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
