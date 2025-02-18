// 通用工具函数
class Utils {
    // 防抖函数
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 显示成功提示
    static showSuccessMessage(message) {
        Toastify({
            text: message,
            duration: 3000,
            close: true,
            gravity: "top",
            position: "center",
            backgroundColor: "#4caf50",
        }).showToast();
    }

    // 显示错误提示
    static showErrorMessage(message) {
        Toastify({
            text: message,
            duration: 3000,
            close: true,
            gravity: "top",
            position: "center",
            backgroundColor: "#f44336",
        }).showToast();
    }

    // API 请求封装
    static async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || '请求失败');
            }
            return data;
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    }
} 