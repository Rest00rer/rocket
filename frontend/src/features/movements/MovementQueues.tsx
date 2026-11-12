import { useState } from "react";

import { errorMessage } from "../../app/useCheckStock";
import { command } from "../../shared/api/client";
import type {
  FboShipment,
  FbsReservation,
  Product,
  Transfer,
  Warehouse,
} from "../../shared/api/types";
import { EmptyState } from "../../shared/ui/Feedback";

function RecordTitle({
  productId,
  products,
  quantity,
}: {
  productId: string;
  products: Product[];
  quantity: number;
}) {
  const product = products.find((item) => item.id === productId);
  return (
    <div className="queue-title">
      <strong>{product?.name ?? "Неизвестный товар"}</strong>
      <span>
        {product?.sku ?? "—"} · {quantity} шт.
      </span>
    </div>
  );
}

export function MovementQueues({
  products,
  warehouses,
  transfers,
  fbs,
  fbo,
  onComplete,
}: {
  products: Product[];
  warehouses: Warehouse[];
  transfers: Transfer[];
  fbs: FbsReservation[];
  fbo: FboShipment[];
  onComplete: () => Promise<void>;
}) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const activeTransfers = transfers.filter(
    (item) => item.status !== "received",
  );
  const activeFbs = fbs.filter((item) => item.status === "reserved");
  const activeFbo = fbo.filter((item) => item.status === "in_transit");
  const warehouseName = (id: string) =>
    warehouses.find((item) => item.id === id)?.name ?? "—";

  async function run(id: string, path: string) {
    setBusyId(id);
    setError(null);
    try {
      await command(path);
      await onComplete();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusyId(null);
    }
  }

  const activeCount =
    activeTransfers.length + activeFbs.length + activeFbo.length;
  const isEmpty = activeCount === 0;

  return (
    <section className="panel panel--wide" id="movements">
      <div className="panel-heading">
        <div>
          <h2>Незавершённые движения</h2>
        </div>
        {activeCount > 0 && <span className="count-badge">{activeCount}</span>}
      </div>

      {error && (
        <p className="inline-feedback inline-feedback--error">{error}</p>
      )}
      {isEmpty ? (
        <EmptyState>Незавершённых операций нет.</EmptyState>
      ) : (
        <div className="queue-grid">
          {activeTransfers.map((transfer) => (
            <article className="queue-item" key={transfer.id}>
              <div className="queue-item__top">
                <span className="tag">Между складами</span>
                <span className={`status status--${transfer.status}`}>
                  {transfer.status === "draft" ? "Черновик" : "В пути"}
                </span>
              </div>
              <RecordTitle
                productId={transfer.product_id}
                products={products}
                quantity={transfer.quantity}
              />
              <p className="route">
                {warehouseName(transfer.source_warehouse_id)}
                <span aria-hidden="true">→</span>
                {warehouseName(transfer.destination_warehouse_id)}
              </p>
              <button
                className="button button--secondary button--small"
                disabled={busyId === transfer.id}
                type="button"
                onClick={() =>
                  void run(
                    transfer.id,
                    `/transfers/${transfer.id}/${transfer.status === "draft" ? "dispatch" : "receive"}`,
                  )
                }
              >
                {busyId === transfer.id
                  ? "Обновляем…"
                  : transfer.status === "draft"
                    ? "Отправить"
                    : "Принять"}
              </button>
            </article>
          ))}

          {activeFbs.map((reservation) => (
            <article className="queue-item" key={reservation.id}>
              <div className="queue-item__top">
                <span className="tag">FBS</span>
                <span className="status status--reserved">В резерве</span>
              </div>
              <RecordTitle
                productId={reservation.product_id}
                products={products}
                quantity={reservation.quantity}
              />
              <p className="route">
                Склад: {warehouseName(reservation.warehouse_id)}
              </p>
              <div className="button-row">
                <button
                  className="button button--secondary button--small"
                  disabled={busyId === reservation.id}
                  type="button"
                  onClick={() =>
                    void run(
                      reservation.id,
                      `/fbs/reservations/${reservation.id}/ship`,
                    )
                  }
                >
                  Отгрузить
                </button>
                <button
                  className="button button--quiet button--small"
                  disabled={busyId === reservation.id}
                  type="button"
                  onClick={() =>
                    void run(
                      reservation.id,
                      `/fbs/reservations/${reservation.id}/cancel`,
                    )
                  }
                >
                  Отменить
                </button>
              </div>
            </article>
          ))}

          {activeFbo.map((shipment) => (
            <article className="queue-item" key={shipment.id}>
              <div className="queue-item__top">
                <span className="tag">FBO</span>
                <span className="status status--dispatched">В пути</span>
              </div>
              <RecordTitle
                productId={shipment.product_id}
                products={products}
                quantity={shipment.quantity}
              />
              <p className="route">
                Со склада: {warehouseName(shipment.warehouse_id)}
              </p>
              <button
                className="button button--secondary button--small"
                disabled={busyId === shipment.id}
                type="button"
                onClick={() =>
                  void run(shipment.id, `/fbo/shipments/${shipment.id}/receive`)
                }
              >
                {busyId === shipment.id ? "Обновляем…" : "Подтвердить приёмку"}
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
