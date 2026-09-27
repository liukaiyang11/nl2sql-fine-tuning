import { Card } from './ui/card';
import { Button } from './ui/button';
import { Download } from 'lucide-react';
import { StepProgress } from './StepProgress';
import { motion, AnimatePresence } from 'motion/react';

interface ProgressPanelProps {
  isGenerating: boolean;
  progress: number;
  currentStep: number;
  logs: string[];
  onDownload?: () => void;
}

export function ProgressPanel({ isGenerating, progress, currentStep, logs, onDownload }: ProgressPanelProps) {
  const steps = [
    '连接数据库',
    '加载架构',
    '调用模型',
    '生成SQL',
    '验证结果',
    '保存数据'
  ];

  const estimatedTime = Math.max(0, Math.ceil((6 - currentStep) * 2));
  const isComplete = currentStep === 6 && progress === 100;

  return (
    <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm p-8 rounded-2xl shadow-2xl">
      <div className="space-y-8">
        <div>
          <h2 className="text-slate-100 mb-6">生成进度</h2>
          
          {/* Overall Progress Percentage */}
          <div className="mb-8 bg-slate-950/50 border border-slate-800 rounded-xl p-6">
            <div className="flex items-end justify-between mb-3">
              <span className="text-slate-400">整体进度</span>
              <div className="flex items-baseline gap-1">
                <motion.span
                  key={Math.round(progress)}
                  initial={{ scale: 1.2, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="bg-gradient-to-r from-[#1F5EFF] to-[#8C4AFF] bg-clip-text text-transparent"
                >
                  {Math.round(progress)}
                </motion.span>
                <span className="text-slate-500">%</span>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-[#1F5EFF] to-[#8C4AFF] rounded-full"
                initial={{ width: '0%' }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
              <motion.div
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-[#1F5EFF] to-[#8C4AFF] rounded-full opacity-50 blur-sm"
                initial={{ width: '0%' }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
            
            {isGenerating && !isComplete && (
              <div className="mt-3 text-right">
                <span className="text-slate-500 text-sm">预计剩余时间：{estimatedTime} 秒</span>
              </div>
            )}
          </div>
          
          <StepProgress steps={steps} currentStep={currentStep} />
        </div>

        {/* Logs Section */}
        <div className="space-y-4">
          <h3 className="text-slate-300">实时日志</h3>
          
          <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-4 h-[400px] overflow-y-auto">
            <div className="space-y-2 font-mono text-sm">
              <AnimatePresence>
                {logs.length === 0 ? (
                  <div className="text-slate-500 text-center py-8">
                    等待开始生成...
                  </div>
                ) : (
                  logs.map((log, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3 }}
                      className={`${
                        log.includes('✓')
                          ? 'text-emerald-400'
                          : log.includes('✗')
                          ? 'text-red-400'
                          : 'text-slate-400'
                      }`}
                    >
                      {log}
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Download Button */}
        <Button
          onClick={onDownload}
          disabled={!isComplete}
          className="w-full bg-gradient-to-r from-[#1F5EFF] to-[#8C4AFF] hover:opacity-90 transition-opacity shadow-lg shadow-[#1F5EFF]/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download className="w-4 h-4 mr-2" />
          下载数据
        </Button>

        {isComplete && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-r from-emerald-500/10 to-green-500/10 border border-emerald-500/30 rounded-xl p-4 text-center"
          >
            <div className="text-emerald-400">
              ✓ 生成完成！数据已准备就绪
            </div>
          </motion.div>
        )}
      </div>
    </Card>
  );
}
