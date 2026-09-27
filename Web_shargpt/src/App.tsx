import { useState, useEffect, useRef } from 'react';
import { ConfigurationPanel } from './components/ConfigurationPanel';
import { ProgressPanel } from './components/ProgressPanel';
import { Button } from './components/ui/button';
import { Switch } from './components/ui/switch';
import { Label } from './components/ui/label';
import { api, TaskConfig, DatabaseConfig, LLMConfig, GenerateConfig, WSMessage } from './services/api';
import { storage } from './services/storage';
import { useToast } from './components/ui/use-toast';

export default function App() {
  const [rememberSettings, setRememberSettings] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [taskConfig, setTaskConfig] = useState<TaskConfig | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const { toast } = useToast();

  // 加载保存的配置
  useEffect(() => {
    const remember = storage.getRememberSettings();
    setRememberSettings(remember);
    
    if (remember) {
      const dbConfig = storage.loadDBConfig();
      const llmConfig = storage.loadLLMConfig();
      const genConfig = storage.loadGenerateConfig();
      
      if (dbConfig || llmConfig || genConfig) {
        toast({
          title: '已加载保存的配置',
          description: '之前保存的配置已自动填充',
        });
      }
    }
  }, []);

  // 处理保存配置选项变化
  useEffect(() => {
    storage.setRememberSettings(rememberSettings);
  }, [rememberSettings]);

  // 清理WebSocket连接
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // 启动生成任务
  const handleStartGeneration = async (config: TaskConfig) => {
    setTaskConfig(config);
    setIsGenerating(true);
    setProgress(0);
    setCurrentStep(0);
    setLogs([]);
    
    try {
      // 关闭旧的 WebSocket 连接（如果存在）
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      // 保存配置
      if (rememberSettings) {
        storage.saveDBConfig(config.db);
        storage.saveLLMConfig(config.llm);
        storage.saveGenerateConfig(config.generate);
      }
      
      // 建立WebSocket连接
      wsRef.current = api.createWebSocket(
        (message: WSMessage) => {
          // 处理日志消息
          if (message.type === 'log') {
            const logText = `[${message.timestamp?.split('T')[1]?.substring(0, 8) || ''}] ${message.message}`;
            setLogs(prev => [...prev, logText]);
          }
          
          // 处理进度消息
          if (message.type === 'progress') {
            if (message.step !== undefined) {
              setCurrentStep(message.step);
            }
            if (message.progress !== undefined) {
              setProgress(message.progress);
            }
          }
          
          // 处理状态消息
          if (message.type === 'status' && message.data) {
            if (message.data.status === 'completed') {
              setIsGenerating(false);
              toast({
                title: '✅ 生成完成！',
                description: `成功生成 ${message.data.details?.samples_valid || 0} 条训练数据`,
              });
            } else if (message.data.status === 'failed') {
              setIsGenerating(false);
              toast({
                title: '❌ 生成失败',
                description: message.data.error_message || '未知错误',
                variant: 'destructive',
              });
            }
          }
        },
        (error) => {
          console.error('WebSocket错误:', error);
          toast({
            title: '连接错误',
            description: 'WebSocket连接失败，请检查后端服务',
            variant: 'destructive',
          });
        }
      );
      
      // 启动生成任务
      const result = await api.startGeneration(config);
      
      if (!result.success) {
        setIsGenerating(false);
        toast({
          title: '启动失败',
          description: result.detail || '无法启动生成任务',
          variant: 'destructive',
        });
      }
    } catch (error) {
      setIsGenerating(false);
      console.error('启动生成失败:', error);
      toast({
        title: '错误',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Top Navigation */}
      <nav className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="mx-auto max-w-[1920px] px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="bg-gradient-to-r from-[#1F5EFF] to-[#8C4AFF] bg-clip-text text-transparent">
                NL2SQL 自动数据生成器
              </h1>
              <p className="mt-1 text-slate-400">
                配置数据库与大模型参数，一键生成训练数据
              </p>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3">
                <Switch
                  id="remember"
                  checked={rememberSettings}
                  onCheckedChange={setRememberSettings}
                />
                <Label htmlFor="remember" className="cursor-pointer text-slate-300">
                  保存配置
                </Label>
              </div>
              
              <Button
                size="lg"
                onClick={handleStartGeneration}
                disabled={isGenerating}
                className="bg-gradient-to-r from-[#1F5EFF] to-[#8C4AFF] hover:opacity-90 transition-opacity shadow-lg shadow-[#1F5EFF]/20"
              >
                开始生成
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="mx-auto max-w-[1920px] px-8 py-8">
        <div className="grid grid-cols-2 gap-8">
          <ConfigurationPanel 
            onStartGeneration={handleStartGeneration}
            isGenerating={isGenerating}
            rememberSettings={rememberSettings}
          />
          <ProgressPanel
            isGenerating={isGenerating}
            progress={progress}
            currentStep={currentStep}
            logs={logs}
            onDownload={() => api.downloadFile('latest')}
          />
        </div>
      </div>
    </div>
  );
}
