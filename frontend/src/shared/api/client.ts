import { API_URL } from "../config";
import type {
  DashboardData,
  DomainErrorBody,
  FboShipment,
  FbsReservation,
  InventorySummary,
  OperationList,
  Product,
  Transfer,
  Warehouse,
} from "./types";

export class ApiError extends Error {
  status: number;
  body: DomainErrorBody;

  constructor(status: number, body: DomainErrorBody) {
    super(body.message ?? "Не удалось выполнить запрос");
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    signal: init?.signal ?? AbortSignal.timeout(15_000),
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  const body = (await response.json().catch(() => ({}))) as T & DomainErrorBody;
  if (!response.ok) {
    throw new ApiError(response.status, body);
  }
  return body as T;
}

export function command<T>(path: string, body?: unknown, method = "POST") {
  return request<T>(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
    headers: { "Idempotency-Key": crypto.randomUUID() },
  });
}

export function mutate<T>(path: string, body?: unknown, method = "POST") {
  return request<T>(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export async function loadDashboard(): Promise<DashboardData> {
  const [products, warehouses, inventory, transfers, fbs, fbo, operations] =
    await Promise.all([
      request<Product[]>("/products"),
      request<Warehouse[]>("/warehouses"),
      request<InventorySummary>("/inventory"),
      request<Transfer[]>("/transfers"),
      request<FbsReservation[]>("/fbs/reservations"),
      request<FboShipment[]>("/fbo/shipments"),
      request<OperationList>("/operations?limit=100"),
    ]);

  return {
    products,
    warehouses,
    inventory,
    transfers,
    fbs,
    fbo,
    operations: operations.items,
  };
}

export function loadOperations(params: URLSearchParams) {
  const query = params.toString();
  return request<OperationList>(`/operations${query ? `?${query}` : ""}`);
}
