import { useState } from "react";

import type { ToastMessage } from "./Toast";

let nextToastId = 0;

export function useToasts() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const push = (message: string, type: "info" | "error" = "info") => {
    setToasts((prev) => [...prev, { id: ++nextToastId, message, type }]);
  };
  const dismiss = (id: number) => setToasts((prev) => prev.filter((t) => t.id !== id));
  return { toasts, push, dismiss };
}
