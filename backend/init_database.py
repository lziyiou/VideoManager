#!/usr/bin/env python3
"""
数据库初始化脚本

此脚本用于：
1. 创建所有数据库表
2. 创建默认的标签分类
3. 初始化系统设置

使用方法：
python init_database.py
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import SQLALCHEMY_DATABASE_URL
from app.models.setting import Base, Setting
from app.models.video import Video
from app.models.tag import Tag
from app.models.tag_category import TagCategory

def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    # 创建数据库连接
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 创建所有表
    print("1. 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("   ✅ 数据库表创建完成")
    
    # 初始化默认数据
    with SessionLocal() as db:
        try:
            # 创建默认标签分类
            print("2. 创建默认标签分类...")
            default_categories = [
                {
                    'name': '通用',
                    'color': '#409EFF',
                    'sort_order': 0,
                    'description': '通用标签分类'
                },
                {
                    'name': '类型',
                    'color': '#67C23A',
                    'sort_order': 1,
                    'description': '视频类型相关标签'
                },
                {
                    'name': '主题',
                    'color': '#E6A23C',
                    'sort_order': 2,
                    'description': '视频主题相关标签'
                },
                {
                    'name': '质量',
                    'color': '#F56C6C',
                    'sort_order': 3,
                    'description': '视频质量相关标签'
                }
            ]
            
            for cat_data in default_categories:
                # 检查分类是否已存在
                existing = db.query(TagCategory).filter(TagCategory.name == cat_data['name']).first()
                if not existing:
                    category = TagCategory(**cat_data)
                    db.add(category)
                    print(f"   创建分类: {cat_data['name']}")
                else:
                    print(f"   分类已存在: {cat_data['name']}")
            
            # 创建默认系统设置
            print("3. 创建默认系统设置...")
            default_settings = [
                {'key': 'root_directory', 'value': ''},
                {'key': 'thumbnail_quality', 'value': '80'},
                {'key': 'max_thumbnail_size', 'value': '200'},
            ]
            
            for setting_data in default_settings:
                existing = db.query(Setting).filter(Setting.key == setting_data['key']).first()
                if not existing:
                    setting = Setting(**setting_data)
                    db.add(setting)
                    print(f"   创建设置: {setting_data['key']}")
                else:
                    print(f"   设置已存在: {setting_data['key']}")
            
            # 提交事务
            db.commit()
            print("\n✅ 数据库初始化完成！")
            
            # 显示统计信息
            print("\n📊 数据库统计:")
            categories_count = db.query(TagCategory).count()
            tags_count = db.query(Tag).count()
            videos_count = db.query(Video).count()
            settings_count = db.query(Setting).count()
            
            print(f"   - 标签分类数: {categories_count}")
            print(f"   - 标签数: {tags_count}")
            print(f"   - 视频数: {videos_count}")
            print(f"   - 系统设置数: {settings_count}")
            
        except Exception as e:
            print(f"❌ 初始化失败: {str(e)}")
            db.rollback()
            raise

def reset_database():
    """重置数据库（删除所有数据）"""
    print("⚠️  警告：此操作将删除所有数据！")
    response = input("是否继续？(yes/no): ")
    if response.lower() != 'yes':
        print("操作已取消")
        return
    
    print("开始重置数据库...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # 删除所有表
    Base.metadata.drop_all(bind=engine)
    print("✅ 数据库重置完成")
    
    # 重新初始化
    init_database()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库初始化脚本')
    parser.add_argument('--reset', action='store_true', help='重置数据库（删除所有数据后重新初始化）')
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    else:
        init_database()