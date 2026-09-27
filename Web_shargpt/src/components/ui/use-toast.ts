/**
 * Toast hook - 使用 sonner 库提供 toast 通知
 */
import { toast as sonnerToast } from 'sonner';

type ToastProps = {
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
};

export function useToast() {
  const toast = ({ title, description, variant }: ToastProps) => {
    if (variant === 'destructive') {
      sonnerToast.error(title || '错误', {
        description,
      });
    } else {
      sonnerToast(title || '通知', {
        description,
      });
    }
  };

  return { toast };
}

