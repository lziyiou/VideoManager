import axios from 'axios';
import { ElMessage } from 'element-plus';

// 创建 Axios 实例
const apiClient = axios.create({
  baseURL: '/api', // 根据您的API基础路径调整
  timeout: 10000, // 请求超时时间
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么，例如添加认证token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    // 对请求错误做些什么
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    // 例如，如果后端有自定义的成功/错误代码结构
    // if (response.data && response.data.code !== 0) {
    //   ElMessage.error(response.data.message || '操作失败');
    //   return Promise.reject(new Error(response.data.message || '操作失败'));
    // }
    return response;
  },
  (error) => {
    // 对响应错误做点什么
    console.error('Response Error:', error);
    let message = '请求失败，请稍后再试';

    if (error.response) {
      // 请求已发出，但服务器响应的状态码不在 2xx 范围内
      switch (error.response.status) {
        case 400:
          message = error.response.data.detail || '请求参数错误';
          break;
        case 401:
          message = '认证失败，请重新登录';
          // router.push('/login'); // 可选：跳转到登录页
          break;
        case 403:
          message = '您没有权限执行此操作';
          break;
        case 404:
          message = '请求的资源未找到';
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          message = '服务器内部错误，请稍后再试';
          break;
        default:
          message = `发生错误 (${error.response.status})`;
      }
      if (error.response.data && typeof error.response.data.detail === 'string') {
        message = error.response.data.detail;
      } else if (error.response.data && typeof error.response.data.message === 'string') {
        message = error.response.data.message;
      }
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      message = '网络超时，请检查您的网络连接';
    } else {
      // 设置请求时发生了一些事情，触发了错误
      message = error.message || '发生未知错误';
    }

    ElMessage.error(message);
    return Promise.reject(error);
  }
);

export default apiClient;