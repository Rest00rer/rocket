import type { InventoryItem } from "../../shared/api/types";
import { EmptyState } from "../../shared/ui/Feedback";

export function InventoryTable({ items }: { items: InventoryItem[] }) {
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
                <th>Товар</th>
                <th>Склад</th>
                <th className="number-cell">На руках</th>
                <th className="number-cell">Резерв FBS</th>
                <th className="number-cell">Доступно</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={`${item.product.id}-${item.warehouse.id}`}>
                  <td>
                    <strong>{item.product.name}</strong>
                    <span className="secondary-text">{item.product.sku}</span>
                  </td>
                  <td>
                    {item.warehouse.name}
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
