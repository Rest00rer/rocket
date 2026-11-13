import { type FormEvent, useMemo, useState } from "react";

import { errorMessage } from "../../app/useCheckStock";
import { ApiError, command, mutate } from "../../shared/api/client";
import type { Product, Transfer, Warehouse } from "../../shared/api/types";

type ActionKind = "receipt" | "transfer" | "fbs" | "fbo";

const actions: Array<{ id: ActionKind; label: string }> = [
  { id: "receipt", label: "Приёмка" },
  { id: "transfer", label: "Перемещение" },
  { id: "fbs", label: "Резерв FBS" },
  { id: "fbo", label: "Отгрузка FBO" },
];

export function ActionPanel({
  products,
  warehouses,
  onComplete,
}: {
  products: Product[];
  warehouses: Warehouse[];
  onComplete: () => Promise<void>;
}) {
  const activeWarehouses = useMemo(
    () => warehouses.filter((warehouse) => !warehouse.archived),
    [warehouses],
  );
  const [kind, setKind] = useState<ActionKind>("receipt");
  const [productId, setProductId] = useState(products[0]?.id ?? "");
  const [warehouseId, setWarehouseId] = useState(activeWarehouses[0]?.id ?? "");
  const [destinationId, setDestinationId] = useState(
    activeWarehouses[1]?.id ?? "",
  );
  const [quantity, setQuantity] = useState(1);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "ok" | "error";
    text: string;
  } | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setFeedback(null);
    try {
      if (kind === "transfer") {
        if (warehouseId === destinationId) {
          throw new Error("Выберите разные склады отправления и назначения");
        }
        await mutate<Transfer>("/transfers", {
          product_id: productId,
          source_warehouse_id: warehouseId,
          destination_warehouse_id: destinationId,
          quantity,
        });
      } else {
        const endpoints: Record<Exclude<ActionKind, "transfer">, string> = {
          receipt: "/receipts",
          fbs: "/fbs/reservations",
          fbo: "/fbo/shipments",
        };
        await command(endpoints[kind], {
          product_id: productId,
          warehouse_id: warehouseId,
          quantity,
        });
      }
      setFeedback({
        type: "ok",
        text:
          kind === "transfer"
            ? "Перемещение создано как черновик"
            : "Операция выполнена",
      });
      setQuantity(1);
      await onComplete();
    } catch (requestError) {
      let text = errorMessage(requestError);
      if (
        requestError instanceof ApiError &&
        requestError.body.code === "insufficient_stock"
      ) {
        const details = requestError.body.details;
        text = `${text}. Здесь доступно: ${details?.available_here ?? 0}, на всех складах: ${details?.available_total ?? 0}.`;
      }
      setFeedback({ type: "error", text });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel action-panel" id="actions">
      <div className="panel-heading panel-heading--stacked">
        <div>
          <h2>Новая операция</h2>
        </div>
        <div className="action-tabs" aria-label="Тип операции">
          {actions.map((action) => (
            <button
              className={
                kind === action.id
                  ? "action-tab action-tab--active"
                  : "action-tab"
              }
              key={action.id}
              type="button"
              aria-pressed={kind === action.id}
              onClick={() => {
                setKind(action.id);
                setFeedback(null);
              }}
            >
              <strong>{action.label}</strong>
            </button>
          ))}
        </div>
      </div>

      <form className="operation-form" onSubmit={submit}>
        <label>
          <span>Товар</span>
          <select
            value={productId}
            onChange={(event) => setProductId(event.target.value)}
          >
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.sku} · {product.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>{kind === "transfer" ? "Со склада" : "Склад"}</span>
          <select
            value={warehouseId}
            onChange={(event) => setWarehouseId(event.target.value)}
          >
            {activeWarehouses.map((warehouse) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.name}
              </option>
            ))}
          </select>
        </label>
        {kind === "transfer" && (
          <label>
            <span>На склад</span>
            <select
              value={destinationId}
              onChange={(event) => setDestinationId(event.target.value)}
            >
              {activeWarehouses.map((warehouse) => (
                <option key={warehouse.id} value={warehouse.id}>
                  {warehouse.name}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="quantity-field">
          <span>Количество</span>
          <input
            min="1"
            type="number"
            value={quantity}
            onChange={(event) =>
              setQuantity(Math.max(1, Number(event.target.value)))
            }
          />
        </label>
        <button
          className="button button--primary form-submit"
          disabled={busy}
          type="submit"
        >
          {busy
            ? "Выполняем…"
            : actions.find((action) => action.id === kind)?.label}
        </button>
      </form>
      {feedback && (
        <p
          className={`inline-feedback inline-feedback--${feedback.type}`}
          role="status"
        >
          {feedback.text}
        </p>
      )}
    </section>
  );
}
