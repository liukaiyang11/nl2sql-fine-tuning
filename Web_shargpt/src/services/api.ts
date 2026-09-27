/**
 * API服务层 - 连接后端API
 */

// API基础URL - 根据环境自动选择
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// 数据库配置接口
export interface DatabaseConfig {
  type: string;
  host: string;
  port: number;
  user: string;
  password: string;
  database: string;
}

// LLM配置接口
export interface LLMConfig {
  api_base: string;
  api_key: string;
  model_name: string;
  temperature: number;
  top_p: number;
  max_tokens: number;
  timeout: number;
  max_retries: number;
}

// 生成配置接口
export interface GenerateConfig {
  total_samples: number;
  dialect: string;
  output_path: string;
  output_format: string;
  enable_validation: boolean;
  min_tables_per_topic: number;
  max_tables_per_topic: number;
}

// 完整任务配置
export interface TaskConfig {
  db: DatabaseConfig;
  llm: LLMConfig;
  generate: GenerateConfig;
}

// WebSocket消息类型
export interface WSMessage {
  type: 'log' | 'progress' | 'status';
  level?: string;
  message?: string;
  timestamp?: string;
  step?: number;
  total_steps?: number;
  step_name?: string;
  progress?: number;
  details?: string;
  data?: any;
}

// API类
class API {
  /**
   * 健康检查
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return response.ok;
    } catch (error) {
      console.error('健康检查失败:', error);
      return false;
    }
  }

  /**
   * 测试数据库连接
   */
  async testDatabaseConnection(config: DatabaseConfig): Promise<{
    success: boolean;
    message?: string;
    tables_count?: number;
    detail?: string;
  }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test-db-connection`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, detail: error.detail };
      }

      return await response.json();
    } catch (error) {
      console.error('测试数据库连接失败:', error);
      return { success: false, detail: String(error) };
    }
  }

  /**
   * 测试LLM连接
   */
  async testLLMConnection(config: LLMConfig): Promise<{
    success: boolean;
    message?: string;
    response?: string;
    detail?: string;
  }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test-llm-connection`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, detail: error.detail };
      }

      return await response.json();
    } catch (error) {
      console.error('测试LLM连接失败:', error);
      return { success: false, detail: String(error) };
    }
  }

  /**
   * 启动生成任务
   */
  async startGeneration(config: TaskConfig): Promise<{
    success: boolean;
    task_id?: string;
    message?: string;
    detail?: string;
  }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/start-generation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, detail: error.detail };
      }

      return await response.json();
    } catch (error) {
      console.error('启动生成任务失败:', error);
      return { success: false, detail: String(error) };
    }
  }

  /**
   * 获取任务状态
   */
  async getStatus(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/status`);
      return await response.json();
    } catch (error) {
      console.error('获取状态失败:', error);
      return null;
    }
  }

  /**
   * 获取日志
   */
  async getLogs(limit: number = 100): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/logs?limit=${limit}`);
      return await response.json();
    } catch (error) {
      console.error('获取日志失败:', error);
      return { logs: [] };
    }
  }

  /**
   * 取消任务
   */
  async cancelTask(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/cancel`, {
        method: 'POST',
      });
      return response.ok;
    } catch (error) {
      console.error('取消任务失败:', error);
      return false;
    }
  }

  /**
   * 下载文件
   */
  downloadFile(filename: string = 'latest') {
    const url = filename === 'latest' 
      ? `${API_BASE_URL}/api/download/latest`
      : `${API_BASE_URL}/api/download/${filename}`;
    
    // 创建隐藏的下载链接
    const link = document.createElement('a');
    link.href = url;
    link.download = filename === 'latest' ? 'nl2sql.jsonl' : filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * 创建WebSocket连接
   */
  createWebSocket(onMessage: (message: WSMessage) => void, onError?: (error: Event) => void): WebSocket {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/all`);
    
    ws.onopen = () => {
      console.log('✅ WebSocket已连接');
    };
    
    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        onMessage(message);
      } catch (error) {
        console.error('解析WebSocket消息失败:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('❌ WebSocket错误:', error);
      if (onError) onError(error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket已断开');
    };
    
    return ws;
  }
}

// 导出单例
export const api = new API();
export default api;

