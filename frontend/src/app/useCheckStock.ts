import { useCallback, useEffect, useState } from "react";

import { ApiError, loadDashboard } from "../shared/api/client";
import type { DashboardData } from "../shared/api/types";

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof DOMException && error.name === "TimeoutError") {
    return "Сервер не ответил вовремя. Повторите попытку";
  }
  if (error instanceof Error) return error.message;
  return "Произошла неизвестная ошибка";
}

export function useCheckStock() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      setData(await loadDashboard());
      setError(null);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      if (!quiet) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
