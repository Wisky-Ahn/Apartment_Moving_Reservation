/**
 * 간단한 Toast 알림 시스템
 */

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastOptions {
  duration?: number;
  type?: ToastType;
}

class ToastManager {
  private container: HTMLElement | null = null;

  private createContainer() {
    if (this.container) return this.container;

    this.container = document.createElement('div');
    this.container.className = 'fixed top-4 right-4 z-[9999] space-y-2';
    document.body.appendChild(this.container);
    return this.container;
  }

  private createToast(message: string, options: ToastOptions = {}) {
    const { duration = 3000, type = 'info' } = options;
    const container = this.createContainer();

    const toast = document.createElement('div');
    toast.className = `
      px-4 py-3 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 ease-in-out
      ${this.getToastStyles(type)}
    `;
    toast.textContent = message;

    // 애니메이션을 위해 초기 상태 설정
    toast.style.transform = 'translateX(100%)';
    toast.style.opacity = '0';

    container.appendChild(toast);

    // 애니메이션 시작
    requestAnimationFrame(() => {
      toast.style.transform = 'translateX(0)';
      toast.style.opacity = '1';
    });

    // 자동 제거
    setTimeout(() => {
      toast.style.transform = 'translateX(100%)';
      toast.style.opacity = '0';
      
      setTimeout(() => {
        if (container.contains(toast)) {
          container.removeChild(toast);
        }
        
        // 컨테이너가 비어있으면 제거
        if (container.children.length === 0) {
          document.body.removeChild(container);
          this.container = null;
        }
      }, 300);
    }, duration);
  }

  private getToastStyles(type: ToastType): string {
    switch (type) {
      case 'success':
        return 'bg-green-600 text-white';
      case 'error':
        return 'bg-red-600 text-white';
      case 'warning':
        return 'bg-yellow-600 text-white';
      case 'info':
      default:
        return 'bg-blue-600 text-white';
    }
  }

  success(message: string, duration?: number) {
    this.createToast(message, { type: 'success', duration });
  }

  error(message: string, duration?: number) {
    this.createToast(message, { type: 'error', duration });
  }

  info(message: string, duration?: number) {
    this.createToast(message, { type: 'info', duration });
  }

  warning(message: string, duration?: number) {
    this.createToast(message, { type: 'warning', duration });
  }
}

const toastManager = new ToastManager();

export const toast = {
  success: (message: string, duration?: number) => toastManager.success(message, duration),
  error: (message: string, duration?: number) => toastManager.error(message, duration),
  info: (message: string, duration?: number) => toastManager.info(message, duration),
  warning: (message: string, duration?: number) => toastManager.warning(message, duration),
}; 