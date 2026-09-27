import { motion } from 'motion/react';
import { Check } from 'lucide-react';

interface StepProgressProps {
  steps: string[];
  currentStep: number;
}

export function StepProgress({ steps, currentStep }: StepProgressProps) {
  return (
    <div className="relative">
      {/* Progress Line */}
      <div className="absolute top-6 left-0 right-0 h-0.5 bg-slate-800">
        <motion.div
          className="h-full bg-gradient-to-r from-[#1F5EFF] to-[#8C4AFF] shadow-[0_0_12px_rgba(31,94,255,0.6)]"
          initial={{ width: '0%' }}
          animate={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>

      {/* Steps */}
      <div className="relative flex justify-between">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isPending = index > currentStep;

          return (
            <div key={index} className="flex flex-col items-center">
              {/* Step Circle */}
              <motion.div
                initial={false}
                animate={{
                  scale: isCurrent ? 1.1 : 1,
                }}
                className={`relative w-12 h-12 rounded-full flex items-center justify-center border-2 mb-3 ${
                  isCompleted
                    ? 'bg-gradient-to-br from-[#1F5EFF] to-[#8C4AFF] border-transparent shadow-[0_0_16px_rgba(31,94,255,0.5)]'
                    : isCurrent
                    ? 'bg-slate-900 border-[#1F5EFF] shadow-[0_0_16px_rgba(31,94,255,0.5)]'
                    : 'bg-slate-900 border-slate-700'
                }`}
              >
                {isCompleted ? (
                  <Check className="w-6 h-6 text-white" />
                ) : (
                  <span
                    className={`${
                      isCurrent
                        ? 'text-[#1F5EFF]'
                        : 'text-slate-500'
                    }`}
                  >
                    {index + 1}
                  </span>
                )}

                {/* Glow Effect for Current Step */}
                {isCurrent && (
                  <motion.div
                    className="absolute inset-0 rounded-full bg-gradient-to-br from-[#1F5EFF] to-[#8C4AFF] opacity-20"
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [0.2, 0.4, 0.2],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: 'easeInOut',
                    }}
                  />
                )}
              </motion.div>

              {/* Step Label */}
              <span
                className={`text-sm text-center ${
                  isCompleted || isCurrent
                    ? 'text-slate-200'
                    : 'text-slate-500'
                }`}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
