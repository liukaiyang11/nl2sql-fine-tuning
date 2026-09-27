/**
 * 本地存储服务
 * 用于保存和加载配置
 */

import { DatabaseConfig, LLMConfig, GenerateConfig } from './api';

const STORAGE_KEYS = {
  DB_CONFIG: 'nl2sql_db_config',
  LLM_CONFIG: 'nl2sql_llm_config',
  GENERATE_CONFIG: 'nl2sql_generate_config',
  REMEMBER_SETTINGS: 'nl2sql_remember_settings',
};

class StorageService {
  /**
   * 保存数据库配置
   */
  saveDBConfig(config: Partial<DatabaseConfig>) {
    try {
      // 不保存密码到localStorage（安全考虑）
      const { password, ...safeConfig } = config;
      localStorage.setItem(STORAGE_KEYS.DB_CONFIG, JSON.stringify(safeConfig));
    } catch (error) {
      console.error('保存数据库配置失败:', error);
    }
  }

  /**
   * 加载数据库配置
   */
  loadDBConfig(): Partial<DatabaseConfig> | null {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.DB_CONFIG);
      return saved ? JSON.parse(saved) : null;
    } catch (error) {
      console.error('加载数据库配置失败:', error);
      return null;
    }
  }

  /**
   * 保存LLM配置
   */
  saveLLMConfig(config: Partial<LLMConfig>) {
    try {
      // 不保存API密钥到localStorage（安全考虑）
      const { api_key, ...safeConfig } = config;
      localStorage.setItem(STORAGE_KEYS.LLM_CONFIG, JSON.stringify(safeConfig));
    } catch (error) {
      console.error('保存LLM配置失败:', error);
    }
  }

  /**
   * 加载LLM配置
   */
  loadLLMConfig(): Partial<LLMConfig> | null {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.LLM_CONFIG);
      return saved ? JSON.parse(saved) : null;
    } catch (error) {
      console.error('加载LLM配置失败:', error);
      return null;
    }
  }

  /**
   * 保存生成配置
   */
  saveGenerateConfig(config: Partial<GenerateConfig>) {
    try {
      localStorage.setItem(STORAGE_KEYS.GENERATE_CONFIG, JSON.stringify(config));
    } catch (error) {
      console.error('保存生成配置失败:', error);
    }
  }

  /**
   * 加载生成配置
   */
  loadGenerateConfig(): Partial<GenerateConfig> | null {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.GENERATE_CONFIG);
      return saved ? JSON.parse(saved) : null;
    } catch (error) {
      console.error('加载生成配置失败:', error);
      return null;
    }
  }

  /**
   * 保存"记住配置"选项
   */
  setRememberSettings(remember: boolean) {
    localStorage.setItem(STORAGE_KEYS.REMEMBER_SETTINGS, String(remember));
  }

  /**
   * 获取"记住配置"选项
   */
  getRememberSettings(): boolean {
    return localStorage.getItem(STORAGE_KEYS.REMEMBER_SETTINGS) === 'true';
  }

  /**
   * 清除所有配置
   */
  clearAll() {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  }
}

export const storage = new StorageService();
export default storage;

