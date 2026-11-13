import { useMemo, useState } from "react";

import type { InventoryItem } from "../../shared/api/types";
import { historyHref, warehouseHref } from "../../shared/navigation";
import { EmptyState } from "../../shared/ui/Feedback";
import {
  compareNumbers,
  compareText,
  nextSortState,
  type SortState,
} from "../../shared/ui/sorting";

type InventoryColumn =
  "product" | "warehouse" | "on_hand" | "reserved_fbs" | "available";

function SortIndicator({
  active,
  direction,
}: {
  active: boolean;
  direction?: "asc" | "desc";
}) {
  return (
    <span
      aria-hidden="true"
      className={
        active
          ? "table-sort-indicator table-sort-indicator--active"
          : "table-sort-indicator"
      }
    >
      {active ? (direction === "asc" ? "↑" : "↓") : "↕"}
    </span>
  );
}

export function InventoryTable({
  items,
  selectedSku,
}: {
  items: InventoryItem[];
  selectedSku?: string;
}) {
  const [sort, setSort] = useState<SortState<InventoryColumn> | null>(null);
  const sortedItems = useMemo(() => {
    if (!sort) return items;

    const multiplier = sort.direction === "asc" ? 1 : -1;
    return [...items].sort((left, right) => {
      const comparison =
        sort.column === "product"
          ? compareText(left.product.name, right.product.name)
          : sort.column === "warehouse"
            ? compareText(left.warehouse.name, right.warehouse.name)
            : sort.column === "on_hand"
              ? compareNumbers(left.on_hand, right.on_hand)
              : sort.column === "reserved_fbs"
                ? compareNumbers(left.reserved_fbs, right.reserved_fbs)
                : compareNumbers(left.available, right.available);

      return comparison * multiplier;
    });
  }, [items, sort]);

  function selectSort(column: InventoryColumn) {
    setSort((current) => nextSortState(current, column));
  }

  function ariaSort(column: InventoryColumn) {
    if (sort?.column !== column) return "none" as const;
    return sort.direction === "asc" ? "ascending" : "descending";
  }

  function sortHeader(label: string, column: InventoryColumn, numeric = false) {
    const active = sort?.column === column;
    return (
      <button
        aria-label={`Сортировать по полю «${label}»`}
        className={numeric ? "table-sort table-sort--numeric" : "table-sort"}
        type="button"
        onClick={() => selectSort(column)}
      >
        <span>{label}</span>
        <SortIndicator active={active} direction={sort?.direction} />
      </button>
    );
  }

  return (
    <section className="panel panel--wide" id="inventory">
      <div className="panel-heading">
        <h2>Товары по складам</h2>
      </div>

      {items.length === 0 ? (
        <EmptyState>Товаров пока нет.</EmptyState>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th aria-sort={ariaSort("product")}>
                  {sortHeader("Товар", "product")}
                </th>
                <th aria-sort={ariaSort("warehouse")}>
                  {sortHeader("Склад", "warehouse")}
                </th>
                <th aria-sort={ariaSort("on_hand")} className="number-cell">
                  {sortHeader("На руках", "on_hand", true)}
                </th>
                <th
                  aria-sort={ariaSort("reserved_fbs")}
                  className="number-cell"
                >
                  {sortHeader("Резерв FBS", "reserved_fbs", true)}
                </th>
                <th aria-sort={ariaSort("available")} className="number-cell">
                  {sortHeader("Доступно", "available", true)}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedItems.map((item) => (
                <tr
                  className={
                    item.product.sku === selectedSku
                      ? "table-row--selected"
                      : undefined
                  }
                  key={`${item.product.id}-${item.warehouse.id}`}
                >
                  <td>
                    <a
                      className="entity-link entity-link--stacked"
                      href={historyHref({ sku: item.product.sku })}
                      title={`Открыть историю ${item.product.sku}`}
                    >
                      <strong>{item.product.name}</strong>
                      <span className="secondary-text">{item.product.sku}</span>
                    </a>
                  </td>
                  <td>
                    <a
                      className="entity-link"
                      href={warehouseHref(item.warehouse.id)}
                      title={`Открыть склад «${item.warehouse.name}»`}
                    >
                      {item.warehouse.name}
                    </a>
                    {item.warehouse.archived && (
                      <span className="tag tag--muted">Архив</span>
                    )}
                  </td>
                  <td className="number-cell">{item.on_hand}</td>
                  <td className="number-cell">{item.reserved_fbs}</td>
                  <td className="number-cell">
                    <span
                      className={
                        item.available === 0 ? "stock-zero" : "stock-positive"
                      }
                    >
                      {item.available}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
