from typing import Dict

# 全局扫描状态
scan_status: Dict = {
    "progress": 0.0,  # 扫描进度（0-1）
    "status": "",    # 当前状态描述
    "completed": False,  # 是否完成
    "total_files": 0,  # 总文件数
    "processed_files": 0  # 已处理文件数
}

def update_scan_progress(progress: float, status: str = None, completed: bool = None):
    """更新扫描进度"""
    scan_status["progress"] = max(0.0, min(1.0, progress))
    if status is not None:
        scan_status["status"] = status
    if completed is not None:
        scan_status["completed"] = completed

def get_scan_status() -> Dict:
    """获取当前扫描状态"""
    return scan_status.copy()

def reset_scan_status():
    """重置扫描状态"""
    scan_status.update({
        "progress": 0.0,
        "status": "",
        "completed": False,
        "total_files": 0,
        "processed_files": 0
    })