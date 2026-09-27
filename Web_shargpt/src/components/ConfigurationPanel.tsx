import { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Slider } from './ui/slider';
import { Switch } from './ui/switch';
import { Database, Server, Play } from 'lucide-react';
import { api, TaskConfig } from '../services/api';
import { storage } from '../services/storage';
import { useToast } from './ui/use-toast';

interface ConfigurationPanelProps {
  onStartGeneration: (config: TaskConfig) => void;
  isGenerating: boolean;
  rememberSettings: boolean;
}

export function ConfigurationPanel({ onStartGeneration, isGenerating, rememberSettings }: ConfigurationPanelProps) {
  // 数据库配置
  const [dbType, setDbType] = useState('mysql');
  const [host, setHost] = useState('localhost');
  const [port, setPort] = useState('3306');
  const [database, setDatabase] = useState('');
  const [username, setUsername] = useState('root');
  const [password, setPassword] = useState('');
  const [dbConnectionStatus, setDbConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');

  // LLM配置
  const [apiEndpoint, setApiEndpoint] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [modelName, setModelName] = useState('qwen2.5-7b-instruct');
  const [temperature, setTemperature] = useState([0.7]);
  const [topP, setTopP] = useState([0.9]);
  const [llmConnectionStatus, setLlmConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');

  // 生成配置
  const [dialect, setDialect] = useState('mysql');
  const [dataFormat, setDataFormat] = useState('alpaca');
  const [sampleCount, setSampleCount] = useState('100');
  const [outputPath, setOutputPath] = useState('./data/nl2sql.jsonl');
  const [validation, setValidation] = useState(true);

  const { toast } = useToast();

  // 从localStorage加载配置
  useEffect(() => {
    if (rememberSettings) {
      const dbConfig = storage.loadDBConfig();
      if (dbConfig) {
        if (dbConfig.type) setDbType(dbConfig.type);
        if (dbConfig.host) setHost(dbConfig.host);
        if (dbConfig.port) setPort(String(dbConfig.port));
        if (dbConfig.database) setDatabase(dbConfig.database);
        if (dbConfig.user) setUsername(dbConfig.user);
      }

      const llmConfig = storage.loadLLMConfig();
      if (llmConfig) {
        if (llmConfig.api_base) setApiEndpoint(llmConfig.api_base);
        if (llmConfig.model_name) setModelName(llmConfig.model_name);
        if (llmConfig.temperature !== undefined) setTemperature([llmConfig.temperature]);
        if (llmConfig.top_p !== undefined) setTopP([llmConfig.top_p]);
      }

      const genConfig = storage.loadGenerateConfig();
      if (genConfig) {
        if (genConfig.dialect) setDialect(genConfig.dialect);
        if (genConfig.output_format) setDataFormat(genConfig.output_format);
        if (genConfig.total_samples) setSampleCount(String(genConfig.total_samples));
        if (genConfig.output_path) setOutputPath(genConfig.output_path);
        if (genConfig.enable_validation !== undefined) setValidation(genConfig.enable_validation);
      }
    }
  }, [rememberSettings]);

  // 测试数据库连接
  const testDatabaseConnection = async () => {
    setDbConnectionStatus('testing');
    
    try {
      const result = await api.testDatabaseConnection({
        type: dbType,
        host,
        port: parseInt(port),
        user: username,
        password,
        database,
      });

      if (result.success) {
        setDbConnectionStatus('success');
        toast({
          title: '✅ 数据库连接成功',
          description: `找到 ${result.tables_count || 0} 个数据表`,
        });
        setTimeout(() => setDbConnectionStatus('idle'), 3000);
      } else {
        setDbConnectionStatus('error');
        toast({
          title: '❌ 数据库连接失败',
          description: result.detail || '请检查配置',
          variant: 'destructive',
        });
        setTimeout(() => setDbConnectionStatus('idle'), 3000);
      }
    } catch (error) {
      setDbConnectionStatus('error');
      toast({
        title: '❌ 连接错误',
        description: String(error),
        variant: 'destructive',
      });
      setTimeout(() => setDbConnectionStatus('idle'), 3000);
    }
  };

  // 测试LLM连接
  const testLLMConnection = async () => {
    setLlmConnectionStatus('testing');
    
    try {
      const result = await api.testLLMConnection({
        api_base: apiEndpoint,
        api_key: apiKey,
        model_name: modelName,
        temperature: temperature[0],
        top_p: topP[0],
        max_tokens: 2000,
        timeout: 120,  // 增加到 120 秒
        max_retries: 3,
      });

      if (result.success) {
        setLlmConnectionStatus('success');
        toast({
          title: '✅ LLM连接成功',
          description: '模型响应正常',
        });
        setTimeout(() => setLlmConnectionStatus('idle'), 3000);
      } else {
        setLlmConnectionStatus('error');
        toast({
          title: '❌ LLM连接失败',
          description: result.detail || '请检查配置',
          variant: 'destructive',
        });
        setTimeout(() => setLlmConnectionStatus('idle'), 3000);
      }
    } catch (error) {
      setLlmConnectionStatus('error');
      toast({
        title: '❌ 连接错误',
        description: String(error),
        variant: 'destructive',
      });
      setTimeout(() => setLlmConnectionStatus('idle'), 3000);
    }
  };

  // 开始生成
  const handleStartGeneration = () => {
    // 验证必填字段
    if (!database) {
      toast({
        title: '配置不完整',
        description: '请填写数据库名称',
        variant: 'destructive',
      });
      return;
    }

    if (!apiEndpoint || !apiKey) {
      toast({
        title: '配置不完整',
        description: '请填写LLM API端点和密钥',
        variant: 'destructive',
      });
      return;
    }

    // 验证样本数量
    const samples = parseInt(sampleCount);
    if (isNaN(samples) || samples < 1) {
      toast({
        title: '样本数量无效',
        description: '请设置至少1个样本',
        variant: 'destructive',
      });
      return;
    }

    // 建议合理的样本数量
    if (samples < 10) {
      toast({
        title: '⚠️ 样本数量较少',
        description: '建议设置至少10个样本以获得更好的效果',
      });
    }

    // 构建配置
    const config: TaskConfig = {
      db: {
        type: dbType,
        host,
        port: parseInt(port),
        user: username,
        password,
        database,
      },
      llm: {
        api_base: apiEndpoint,
        api_key: apiKey,
        model_name: modelName,
        temperature: temperature[0],
        top_p: topP[0],
        max_tokens: 2000,
        timeout: 120,  // 增加到 120 秒
        max_retries: 3,
      },
      generate: {
        total_samples: parseInt(sampleCount),
        dialect,
        output_path: outputPath,
        output_format: dataFormat,
        enable_validation: validation,
        min_tables_per_topic: 1,
        max_tables_per_topic: 3,
      },
    };

    onStartGeneration(config);
  };

  return (
    <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm p-8 rounded-2xl shadow-2xl">
      <div className="space-y-8">
        {/* Database Settings */}
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-[#1F5EFF]/20 to-[#8C4AFF]/20 border border-[#1F5EFF]/30">
              <Database className="w-5 h-5 text-[#1F5EFF]" />
            </div>
            <h2 className="text-slate-100">数据库设置</h2>
          </div>

          <div className="space-y-4 pl-11">
            <div className="space-y-2">
              <Label htmlFor="dbType" className="text-slate-300">数据库类型</Label>
              <Select value={dbType} onValueChange={setDbType}>
                <SelectTrigger id="dbType" className="bg-slate-800/50 border-slate-700 text-slate-100">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mysql">MySQL</SelectItem>
                  <SelectItem value="postgresql">PostgreSQL</SelectItem>
                  <SelectItem value="sqlserver">SQL Server</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="host" className="text-slate-300">主机地址</Label>
                <Input
                  id="host"
                  value={host}
                  onChange={(e) => setHost(e.target.value)}
                  placeholder="localhost"
                  className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="port" className="text-slate-300">端口</Label>
                <Input
                  id="port"
                  value={port}
                  onChange={(e) => setPort(e.target.value)}
                  placeholder="3306"
                  className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="dbName" className="text-slate-300">数据库名称 *</Label>
              <Input
                id="dbName"
                value={database}
                onChange={(e) => setDatabase(e.target.value)}
                placeholder="my_database"
                className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-slate-300">用户名</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="root"
                  className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-300">密码</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={testDatabaseConnection}
              disabled={dbConnectionStatus === 'testing'}
              className={`w-full border-slate-700 ${
                dbConnectionStatus === 'success'
                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                  : dbConnectionStatus === 'error'
                  ? 'bg-red-500/20 border-red-500/50 text-red-400'
                  : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800'
              }`}
            >
              {dbConnectionStatus === 'testing' && '正在测试...'}
              {dbConnectionStatus === 'success' && '✓ 连接成功'}
              {dbConnectionStatus === 'error' && '✗ 连接失败'}
              {dbConnectionStatus === 'idle' && '测试连接'}
            </Button>
          </div>
        </div>

        {/* Model Settings */}
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-[#1F5EFF]/20 to-[#8C4AFF]/20 border border-[#8C4AFF]/30">
              <Server className="w-5 h-5 text-[#8C4AFF]" />
            </div>
            <h2 className="text-slate-100">模型设置</h2>
          </div>

          <div className="space-y-4 pl-11">
            <div className="space-y-2">
              <Label htmlFor="apiEndpoint" className="text-slate-300">API 端点 *</Label>
              <Input
                id="apiEndpoint"
                value={apiEndpoint}
                onChange={(e) => setApiEndpoint(e.target.value)}
                placeholder="https://api.example.com/v1"
                className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="modelName" className="text-slate-300">模型名称</Label>
              <Input
                id="modelName"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="qwen2.5-7b-instruct"
                className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="apiKey" className="text-slate-300">API 密钥 *</Label>
              <Input
                id="apiKey"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-••••••••••••••••"
                className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="temperature" className="text-slate-300">Temperature</Label>
                <span className="text-slate-400 text-sm">{temperature[0]}</span>
              </div>
              <Slider
                id="temperature"
                min={0}
                max={1}
                step={0.1}
                value={temperature}
                onValueChange={setTemperature}
                className="[&_[role=slider]]:bg-gradient-to-r [&_[role=slider]]:from-[#1F5EFF] [&_[role=slider]]:to-[#8C4AFF] [&_[role=slider]]:border-0"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="topP" className="text-slate-300">Top P</Label>
                <span className="text-slate-400 text-sm">{topP[0]}</span>
              </div>
              <Slider
                id="topP"
                min={0}
                max={1}
                step={0.1}
                value={topP}
                onValueChange={setTopP}
                className="[&_[role=slider]]:bg-gradient-to-r [&_[role=slider]]:from-[#1F5EFF] [&_[role=slider]]:to-[#8C4AFF] [&_[role=slider]]:border-0"
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={testLLMConnection}
              disabled={llmConnectionStatus === 'testing' || !apiEndpoint || !apiKey}
              className={`w-full border-slate-700 ${
                llmConnectionStatus === 'success'
                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                  : llmConnectionStatus === 'error'
                  ? 'bg-red-500/20 border-red-500/50 text-red-400'
                  : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800'
              }`}
            >
              {llmConnectionStatus === 'testing' && '正在测试...'}
              {llmConnectionStatus === 'success' && '✓ 连接成功'}
              {llmConnectionStatus === 'error' && '✗ 连接失败'}
              {llmConnectionStatus === 'idle' && '测试LLM连接'}
            </Button>
          </div>
        </div>

        {/* Generation Parameters */}
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-[#1F5EFF]/20 to-[#8C4AFF]/20 border border-[#1F5EFF]/30">
              <Play className="w-5 h-5 text-[#1F5EFF]" />
            </div>
            <h2 className="text-slate-100">生成参数</h2>
          </div>

          <div className="space-y-4 pl-11">
            <div className="space-y-2">
              <Label htmlFor="dialect" className="text-slate-300">SQL 方言</Label>
              <Select value={dialect} onValueChange={setDialect}>
                <SelectTrigger id="dialect" className="bg-slate-800/50 border-slate-700 text-slate-100">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mysql">MySQL</SelectItem>
                  <SelectItem value="postgresql">PostgreSQL</SelectItem>
                  <SelectItem value="sqlite">SQLite</SelectItem>
                  <SelectItem value="tsql">T-SQL</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="dataFormat" className="text-slate-300">数据格式</Label>
              <Select value={dataFormat} onValueChange={setDataFormat}>
                <SelectTrigger id="dataFormat" className="bg-slate-800/50 border-slate-700 text-slate-100">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="alpaca">Alpaca</SelectItem>
                  <SelectItem value="sharegpt">ShareGPT</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="sampleCount" className="text-slate-300">样本数量</Label>
                <Input
                  id="sampleCount"
                  type="number"
                  value={sampleCount}
                  onChange={(e) => setSampleCount(e.target.value)}
                  placeholder="100"
                  className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="outputPath" className="text-slate-300">输出文件名</Label>
                <Input
                  id="outputPath"
                  value={outputPath}
                  onChange={(e) => setOutputPath(e.target.value)}
                  placeholder="./data/nl2sql.jsonl"
                  className="bg-slate-800/50 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-between py-2">
              <Label htmlFor="validation" className="text-slate-300">启用SQL验证</Label>
              <Switch
                id="validation"
                checked={validation}
                onCheckedChange={setValidation}
              />
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4">
          <Button
            onClick={handleStartGeneration}
            disabled={isGenerating}
            className="w-full bg-gradient-to-r from-[#1F5EFF] to-[#8C4AFF] hover:opacity-90 transition-opacity shadow-lg shadow-[#1F5EFF]/20 disabled:opacity-50"
          >
            <Play className="w-4 h-4 mr-2" />
            {isGenerating ? '生成中...' : '开始生成'}
          </Button>
        </div>
      </div>
    </Card>
  );
}
