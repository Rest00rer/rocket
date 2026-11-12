import type { InventorySummary } from "../../shared/api/types";

export function SummaryCards({ inventory }: { inventory: InventorySummary }) {
  const totals = inventory.items.reduce(
    (result, item) => ({
      onHand: result.onHand + item.on_hand,
      reserved: result.reserved + item.reserved_fbs,
      available: result.available + item.available,
    }),
    { onHand: 0, reserved: 0, available: 0 },
  );
  const items = [
    { label: "На складах", value: totals.onHand },
    { label: "Доступно", value: totals.available },
    { label: "Резерв FBS", value: totals.reserved },
    {
      label: "Между складами",
      value: inventory.in_transit.between_warehouses,
    },
    { label: "FBO в пути", value: inventory.in_transit.fbo },
    { label: "FBS клиенту", value: inventory.in_transit.fbs_to_customer },
  ];

  return (
    <section className="summary-grid" aria-label="Сводка по остаткам">
      {items.map((item) => (
        <article className="metric" key={item.label}>
          <p>{item.label}</p>
          <strong>{item.value}</strong>
        </article>
      ))}
    </section>
  );
}
