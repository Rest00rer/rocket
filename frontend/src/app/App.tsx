import { ActionPanel } from "../features/actions/ActionPanel";
import { InventoryTable } from "../features/dashboard/InventoryTable";
import { SummaryCards } from "../features/dashboard/SummaryCards";
import { OperationHistory } from "../features/history/OperationHistory";
import { MovementQueues } from "../features/movements/MovementQueues";
import { WarehousePanel } from "../features/warehouses/WarehousePanel";
import { ErrorState, LoadingState } from "../shared/ui/Feedback";
import { useCheckStock } from "./useCheckStock";

export function App() {
  const { data, loading, error, refresh } = useCheckStock();

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

  return (
    <div className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href="#top"
          aria-label="CheckStock — к началу страницы"
        >
          <span className="brand-mark" aria-hidden="true">
            CS
          </span>
          <strong>CheckStock</strong>
        </a>
        <nav aria-label="Основная навигация">
          <a href="#inventory">Остатки</a>
          <a href="#movements">Движения</a>
          <a href="#history">История</a>
          <a href="#warehouses">Склады</a>
        </nav>
      </header>

      <main className="workspace" id="top">
        <section className="page-intro">
          <h1>Где сейчас товар?</h1>
        </section>

        {error && (
          <div className="page-warning" role="alert">
            Не удалось обновить часть данных: {error}
          </div>
        )}

        <SummaryCards inventory={data.inventory} />
        <div className="primary-grid">
          <InventoryTable items={data.inventory.items} />
          <ActionPanel
            products={data.products}
            warehouses={data.warehouses}
            onComplete={update}
          />
        </div>
        <MovementQueues
          products={data.products}
          warehouses={data.warehouses}
          transfers={data.transfers}
          fbs={data.fbs}
          fbo={data.fbo}
          onComplete={update}
        />
        <div className="secondary-grid">
          <OperationHistory
            initialOperations={data.operations}
            warehouses={data.warehouses}
          />
          <WarehousePanel warehouses={data.warehouses} onComplete={update} />
        </div>
      </main>
    </div>
  );
}
