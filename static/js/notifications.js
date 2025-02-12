// 成功提示
function showSuccessMessage(message) {
    Toastify({
        text: message,
        duration: 3000, // 显示时间（毫秒）
        close: true,
        gravity: "top", // 位置：'top' 或 'bottom'
        position: "center", // 对齐方式：'left', 'center', 'right'
        backgroundColor: "#4caf50", // 绿色背景
    }).showToast();
}

// 错误提示
function showErrorMessage(message) {
    Toastify({
        text: message,
        duration: 3000,
        close: true,
        gravity: "top",
        position: "center",
        backgroundColor: "#f44336", // 红色背景
    }).showToast();
}