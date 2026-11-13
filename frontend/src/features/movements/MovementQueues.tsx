import { useEffect, useState } from "react";

import { errorMessage } from "../../app/useCheckStock";
import { command } from "../../shared/api/client";
import { historyHref, warehouseHref } from "../../shared/navigation";
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
      {product ? (
        <a
          className="entity-link entity-link--stacked"
          href={historyHref({ sku: product.sku })}
          title={`Открыть историю ${product.sku}`}
        >
          <strong>{product.name}</strong>
          <span>
            {product.sku} · {quantity} шт.
          </span>
        </a>
      ) : (
        <>
          <strong>Неизвестный товар</strong>
          <span>— · {quantity} шт.</span>
        </>
      )}
    </div>
  );
}

type MovementTab =
  "pending" | "all" | "transfers" | "fbs" | "fbo" | "fbs-to-customer";

const movementTabs: Array<{ id: MovementTab; label: string }> = [
  { id: "pending", label: "Требуют действия" },
  { id: "all", label: "Все" },
  { id: "transfers", label: "Перемещения" },
  { id: "fbs", label: "Резерв FBS" },
  { id: "fbo", label: "FBO" },
  { id: "fbs-to-customer", label: "Клиенту FBS" },
];

function isMovementTab(value: string): value is MovementTab {
  return movementTabs.some((tab) => tab.id === value);
}

export function MovementQueues({
  products,
  warehouses,
  transfers,
  fbs,
  fbo,
  focusSection,
  onComplete,
}: {
  products: Product[];
  warehouses: Warehouse[];
  transfers: Transfer[];
  fbs: FbsReservation[];
  fbo: FboShipment[];
  focusSection: string;
  onComplete: () => Promise<void>;
}) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<MovementTab>(
    isMovementTab(focusSection) ? focusSection : "pending",
  );
  const activeTransfers = transfers.filter(
    (item) => item.status !== "received",
  );
  const activeFbs = fbs.filter((item) => item.status === "reserved");
  const shippedFbs = fbs.filter((item) => item.status === "shipped");
  const activeFbo = fbo.filter((item) => item.status === "in_transit");
  const warehouseName = (id: string) =>
    warehouses.find((item) => item.id === id)?.name ?? "—";

  async function run(id: string, path: string, method = "POST") {
    setBusyId(id);
    setError(null);
    try {
      await command(path, undefined, method);
      await onComplete();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusyId(null);
    }
  }

  const activeCount =
    activeTransfers.length + activeFbs.length + activeFbo.length;
  const tabCounts: Record<MovementTab, number> = {
    pending: activeCount,
    all: activeCount + shippedFbs.length,
    transfers: activeTransfers.length,
    fbs: activeFbs.length,
    fbo: activeFbo.length,
    "fbs-to-customer": shippedFbs.length,
  };
  const showTransfers =
    activeTab === "all" || activeTab === "pending" || activeTab === "transfers";
  const showActiveFbs =
    activeTab === "all" || activeTab === "pending" || activeTab === "fbs";
  const showActiveFbo =
    activeTab === "all" || activeTab === "pending" || activeTab === "fbo";
  const showShippedFbs = activeTab === "all" || activeTab === "fbs-to-customer";

  useEffect(() => {
    if (!isMovementTab(focusSection)) return;
    setActiveTab(focusSection);
    document.getElementById("movements")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, [focusSection]);

  return (
    <section className="panel panel--wide" id="movements">
      <div className="panel-heading">
        <div>
          <h2>Незавершённые движения</h2>
        </div>
        {activeCount > 0 && <span className="count-badge">{activeCount}</span>}
      </div>

      <div className="movement-tabs" aria-label="Фильтр операций">
        {movementTabs.map((tab) => (
          <button
            aria-pressed={activeTab === tab.id}
            className={
              activeTab === tab.id
                ? "movement-tab movement-tab--active"
                : "movement-tab"
            }
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
            <span className="movement-tab__count">{tabCounts[tab.id]}</span>
          </button>
        ))}
      </div>

      {error && (
        <p className="inline-feedback inline-feedback--error">{error}</p>
      )}
      {tabCounts[activeTab] === 0 ? (
        <EmptyState>
          {activeTab === "pending"
            ? "Незавершённых операций нет."
            : "Операций в этой категории нет."}
        </EmptyState>
      ) : (
        <div className="queue-grid">
          {showTransfers &&
            activeTransfers.map((transfer) => (
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
                  <a
                    className="entity-link"
                    href={warehouseHref(transfer.source_warehouse_id)}
                  >
                    {warehouseName(transfer.source_warehouse_id)}
                  </a>
                  <span aria-hidden="true">→</span>
                  <a
                    className="entity-link"
                    href={warehouseHref(transfer.destination_warehouse_id)}
                  >
                    {warehouseName(transfer.destination_warehouse_id)}
                  </a>
                </p>
                <div className="button-row">
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
                  {transfer.status === "draft" && (
                    <button
                      className="button button--quiet button--small button--danger"
                      disabled={busyId === transfer.id}
                      type="button"
                      onClick={() => {
                        if (
                          window.confirm(
                            "Удалить черновик перемещения? Остатки не изменятся.",
                          )
                        ) {
                          void run(
                            transfer.id,
                            `/transfers/${transfer.id}`,
                            "DELETE",
                          );
                        }
                      }}
                    >
                      Удалить
                    </button>
                  )}
                </div>
              </article>
            ))}

          {showActiveFbs &&
            activeFbs.map((reservation) => (
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
                  Склад:
                  <a
                    className="entity-link"
                    href={warehouseHref(reservation.warehouse_id)}
                  >
                    {warehouseName(reservation.warehouse_id)}
                  </a>
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

          {showActiveFbo &&
            activeFbo.map((shipment) => (
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
                  Со склада:
                  <a
                    className="entity-link"
                    href={warehouseHref(shipment.warehouse_id)}
                  >
                    {warehouseName(shipment.warehouse_id)}
                  </a>
                </p>
                <button
                  className="button button--secondary button--small"
                  disabled={busyId === shipment.id}
                  type="button"
                  onClick={() =>
                    void run(
                      shipment.id,
                      `/fbo/shipments/${shipment.id}/receive`,
                    )
                  }
                >
                  {busyId === shipment.id
                    ? "Обновляем…"
                    : "Подтвердить приёмку"}
                </button>
              </article>
            ))}
          {showShippedFbs &&
            shippedFbs.map((reservation) => (
              <article className="queue-item" key={reservation.id}>
                <div className="queue-item__top">
                  <span className="tag">FBS</span>
                  <span className="status status--dispatched">
                    В пути к клиенту
                  </span>
                </div>
                <RecordTitle
                  productId={reservation.product_id}
                  products={products}
                  quantity={reservation.quantity}
                />
                <p className="route">
                  Со склада:
                  <a
                    className="entity-link"
                    href={warehouseHref(reservation.warehouse_id)}
                  >
                    {warehouseName(reservation.warehouse_id)}
                  </a>
                </p>
              </article>
            ))}
        </div>
      )}
    </section>
  );
}
