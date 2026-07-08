import toast from 'react-hot-toast';

export const useToast = () => {
  const showToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    const styles = {
      success: { icon: '✅', style: { background: '#22c55e', color: 'white' } },
      error: { icon: '❌', style: { background: '#ef4444', color: 'white' } },
      info: { icon: 'ℹ️', style: { background: '#3b82f6', color: 'white' } },
      warning: { icon: '⚠️', style: { background: '#f59e0b', color: 'white' } },
    };

    const config = styles[type];
    toast(message, {
      icon: config.icon,
      style: config.style,
    });
  };

  return { showToast };
};