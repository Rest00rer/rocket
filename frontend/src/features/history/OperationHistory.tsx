import { useEffect, useState } from "react";

import { errorMessage } from "../../app/useCheckStock";
import { loadOperations } from "../../shared/api/client";
import type { Operation, Warehouse } from "../../shared/api/types";
import {
  historyHref,
  inventoryHref,
  warehouseHref,
} from "../../shared/navigation";
import { EmptyState } from "../../shared/ui/Feedback";

const operationLabels: Record<string, string> = {
  receipt: "Приёмка",
  transfer_created: "Перемещение создано",
  transfer_dispatched: "Перемещение отправлено",
  transfer_received: "Перемещение принято",
  fbs_reserved: "Резерв FBS",
  fbs_cancelled: "Резерв отменён",
  fbs_shipped: "Заказ FBS отгружен",
  fbo_dispatched: "Отгрузка FBO",
  fbo_received: "FBO принят",
  warehouse_created: "Склад создан",
  warehouse_renamed: "Склад переименован",
  warehouse_archived: "Склад архивирован",
};

const filters = [
  { id: "all", label: "Все операции", types: [] },
  { id: "receipt", label: "Приёмка", types: ["receipt"] },
  {
    id: "transfers",
    label: "Перемещения",
    types: ["transfer_created", "transfer_dispatched", "transfer_received"],
  },
  {
    id: "fbs",
    label: "FBS",
    types: ["fbs_reserved", "fbs_cancelled", "fbs_shipped"],
  },
  {
    id: "fbo",
    label: "FBO",
    types: ["fbo_dispatched", "fbo_received"],
  },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function OperationHistory({
  initialOperations,
  initialOperationGroup,
  initialSku,
  initialWarehouseId,
  warehouses,
}: {
  initialOperations: Operation[];
  initialOperationGroup: string;
  initialSku: string;
  initialWarehouseId: string;
  warehouses: Warehouse[];
}) {
  const normalizedInitialGroup = filters.some(
    (filter) => filter.id === initialOperationGroup,
  )
    ? initialOperationGroup
    : "all";
  const [items, setItems] = useState(initialOperations);
  const [sku, setSku] = useState(initialSku);
  const [warehouseId, setWarehouseId] = useState(initialWarehouseId);
  const [operationGroup, setOperationGroup] = useState(normalizedInitialGroup);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sku && !warehouseId && operationGroup === "all") {
      setItems(initialOperations);
    }
  }, [initialOperations, operationGroup, sku, warehouseId]);

  useEffect(() => {
    if (initialSku || initialWarehouseId || normalizedInitialGroup !== "all") {
      void applyFilters(normalizedInitialGroup, false);
    }
  }, []);

  async function applyFilters(nextGroup = operationGroup, updateUrl = true) {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: "100" });
      if (sku.trim()) params.set("sku", sku.trim());
      if (warehouseId) params.set("warehouse_id", warehouseId);
      const selectedFilter = filters.find((filter) => filter.id === nextGroup);
      selectedFilter?.types.forEach((type) =>
        params.append("operation_type", type),
      );
      setItems((await loadOperations(params)).items);
      if (updateUrl) {
        window.history.replaceState(
          null,
          "",
          historyHref({
            sku: sku.trim() || undefined,
            warehouseId: warehouseId || undefined,
            group: nextGroup === "all" ? undefined : nextGroup,
          }),
        );
      }
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel panel--wide" id="history">
      <div className="panel-heading panel-heading--history">
        <div>
          <h2>Журнал операций</h2>
        </div>
        <div className="filters filters--history">
          <input
            aria-label="SKU товара"
            value={sku}
            onChange={(event) => setSku(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && void applyFilters()}
            placeholder="Фильтр по SKU"
          />
          <select
            aria-label="Склад"
            value={warehouseId}
            onChange={(event) => setWarehouseId(event.target.value)}
          >
            <option value="">Все склады</option>
            {warehouses.map((warehouse) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.name}
              </option>
            ))}
          </select>
          <button
            className="button button--secondary button--small"
            disabled={loading}
            type="button"
            onClick={() => void applyFilters()}
          >
            Применить
          </button>
        </div>
      </div>
      <div className="history-tabs" aria-label="Фильтр истории">
        {filters.map((filter) => (
          <button
            className={
              operationGroup === filter.id
                ? "history-tab history-tab--active"
                : "history-tab"
            }
            key={filter.id}
            type="button"
            aria-pressed={operationGroup === filter.id}
            onClick={() => {
              setOperationGroup(filter.id);
              void applyFilters(filter.id);
            }}
          >
            {filter.label}
          </button>
        ))}
      </div>
      {error && (
        <p className="inline-feedback inline-feedback--error">{error}</p>
      )}
      {items.length === 0 ? (
        <EmptyState>Операции не найдены.</EmptyState>
      ) : (
        <div
          className={
            loading ? "history-list history-list--loading" : "history-list"
          }
        >
          {items.map((operation) => (
            <article className="history-item" key={operation.id}>
              <time dateTime={operation.created_at}>
                {formatDate(operation.created_at)}
              </time>
              <div>
                <strong>
                  {operationLabels[operation.operation_type] ??
                    operation.operation_type}
                </strong>
                <p>
                  {operation.product_name ? (
                    <a
                      className="entity-link"
                      href={inventoryHref(operation.sku ?? undefined)}
                      title={`Показать ${operation.sku} в остатках`}
                    >
                      {operation.product_name} · {operation.sku}
                    </a>
                  ) : (
                    "Складская операция"
                  )}
                </p>
              </div>
              <div className="history-route">
                {operation.source_warehouse_name && (
                  <a
                    className="entity-link"
                    href={warehouseHref(
                      operation.source_warehouse_id ?? undefined,
                    )}
                  >
                    {operation.source_warehouse_name}
                  </a>
                )}
                {operation.source_warehouse_name &&
                  operation.destination_warehouse_name && (
                    <span aria-hidden="true">→</span>
                  )}
                {operation.destination_warehouse_name && (
                  <a
                    className="entity-link"
                    href={warehouseHref(
                      operation.destination_warehouse_id ?? undefined,
                    )}
                  >
                    {operation.destination_warehouse_name}
                  </a>
                )}
              </div>
              <strong className="history-quantity">
                {operation.quantity == null ? "—" : `${operation.quantity} шт.`}
              </strong>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
