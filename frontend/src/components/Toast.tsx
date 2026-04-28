import { useEffect } from "react";

export interface ToastMessage {
  id: number;
  message: string;
  type?: "info" | "error";
}

interface Props {
  toasts: ToastMessage[];
  dismiss: (id: number) => void;
}

export function ToastStack({ toasts, dismiss }: Props) {
  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} dismiss={dismiss} />
      ))}
    </div>
  );
}

function ToastItem({ toast, dismiss }: { toast: ToastMessage; dismiss: (id: number) => void }) {
  useEffect(() => {
    const handle = window.setTimeout(() => dismiss(toast.id), 4000);
    return () => window.clearTimeout(handle);
  }, [toast.id, dismiss]);

  return <div className={`toast${toast.type === "error" ? " error" : ""}`}>{toast.message}</div>;
}
