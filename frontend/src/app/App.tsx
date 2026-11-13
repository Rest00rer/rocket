import { useEffect, useRef, useState } from "react";

import { ActionPanel } from "../features/actions/ActionPanel";
import { InventoryTable } from "../features/dashboard/InventoryTable";
import { SummaryCards } from "../features/dashboard/SummaryCards";
import { OperationHistory } from "../features/history/OperationHistory";
import { MovementQueues } from "../features/movements/MovementQueues";
import { WarehousePanel } from "../features/warehouses/WarehousePanel";
import { parseViewHash, type ViewId } from "../shared/navigation";
import { ErrorState, LoadingState } from "../shared/ui/Feedback";
import { useCheckStock } from "./useCheckStock";

const views = [
  { id: "inventory", label: "Остатки" },
  { id: "operations", label: "Операции" },
  { id: "history", label: "История" },
  { id: "warehouses", label: "Склады" },
] as const;

export function App() {
  const { data, loading, error, refresh } = useCheckStock();
  const [locationHash, setLocationHash] = useState(window.location.hash);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const location = parseViewHash(locationHash);
  const activeView: ViewId = location.view;

  useEffect(() => {
    const updateView = () => setLocationHash(window.location.hash);
    window.addEventListener("hashchange", updateView);
    return () => window.removeEventListener("hashchange", updateView);
  }, []);

  useEffect(() => {
    const label = views.find((view) => view.id === activeView)?.label;
    document.title = `${label ?? "Остатки"} · CheckStock`;
    headingRef.current?.focus();
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [activeView]);

  if (loading && !data) {
    return (
      <main className="initial-state">
        <LoadingState />
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="initial-state">
        <ErrorState message={error} onRetry={() => void refresh()} />
      </main>
    );
  }

  if (!data) return null;

  const update = () => refresh(true);
  const unfinishedCount =
    data.transfers.filter((item) => item.status !== "received").length +
    data.fbs.filter((item) => item.status === "reserved").length +
    data.fbo.filter((item) => item.status === "in_transit").length;
  const activeViewLabel =
    views.find((view) => view.id === activeView)?.label ?? "Остатки";

  return (
    <div className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href="#inventory"
          aria-label="CheckStock — остатки"
        >
          <span className="brand-mark" aria-hidden="true">
            CS
          </span>
          <strong>CheckStock</strong>
        </a>
        <nav aria-label="Основная навигация">
          {views.map((view) => (
            <a
              className={activeView === view.id ? "nav-link--active" : ""}
              href={`#${view.id}`}
              key={view.id}
              aria-current={activeView === view.id ? "page" : undefined}
            >
              {view.label}
              {view.id === "operations" && unfinishedCount > 0 && (
                <span className="nav-count" aria-label="Незавершённые операции">
                  {unfinishedCount}
                </span>
              )}
            </a>
          ))}
        </nav>
      </header>

      <main className="workspace">
        <section className="page-intro">
          <h1 ref={headingRef} tabIndex={-1}>
            {activeViewLabel}
          </h1>
        </section>

        {error && (
          <div className="page-warning" role="alert">
            Не удалось обновить часть данных: {error}
          </div>
        )}

        {activeView === "inventory" && (
          <div className="view-stack">
            <SummaryCards inventory={data.inventory} />
            <InventoryTable
              items={data.inventory.items}
              selectedSku={location.params.get("sku") ?? undefined}
            />
          </div>
        )}

        {activeView === "operations" && (
          <div className="operations-layout">
            <ActionPanel
              products={data.products}
              warehouses={data.warehouses}
              inventory={data.inventory.items}
              onComplete={update}
            />
            <MovementQueues
              products={data.products}
              warehouses={data.warehouses}
              transfers={data.transfers}
              fbs={data.fbs}
              fbo={data.fbo}
              focusSection={location.params.get("section") ?? ""}
              onComplete={update}
            />
          </div>
        )}

        {activeView === "history" && (
          <OperationHistory
            key={locationHash}
            initialOperations={data.operations}
            initialOperationGroup={location.params.get("group") ?? "all"}
            initialSku={location.params.get("sku") ?? ""}
            initialWarehouseId={location.params.get("warehouse_id") ?? ""}
            warehouses={data.warehouses}
          />
        )}

        {activeView === "warehouses" && (
          <div className="settings-column">
            <WarehousePanel
              selectedWarehouseId={
                location.params.get("warehouse_id") ?? undefined
              }
              warehouses={data.warehouses}
              onComplete={update}
            />
          </div>
        )}
      </main>
    </div>
  );
}
