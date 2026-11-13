import type { InventorySummary } from "../../shared/api/types";
import { operationsHref } from "../../shared/navigation";

type MetricItem = {
  label: string;
  value: number;
  href?: string;
  title?: string;
};

export function SummaryCards({ inventory }: { inventory: InventorySummary }) {
  const totals = inventory.items.reduce(
    (result, item) => ({
      onHand: result.onHand + item.on_hand,
      reserved: result.reserved + item.reserved_fbs,
      available: result.available + item.available,
    }),
    { onHand: 0, reserved: 0, available: 0 },
  );
  const groups: Array<{ label: string; items: MetricItem[] }> = [
    {
      label: "На складах",
      items: [
        { label: "Физически", value: totals.onHand },
        { label: "Доступно", value: totals.available },
        {
          label: "Резерв FBS",
          value: totals.reserved,
          href: operationsHref(),
          title: "Открыть операции с резервом FBS",
        },
      ],
    },
    {
      label: "В пути",
      items: [
        {
          label: "Между складами",
          value: inventory.in_transit.between_warehouses,
          href: operationsHref(),
          title: "Открыть операции между складами",
        },
        {
          label: "На FBO",
          value: inventory.in_transit.fbo,
          href: operationsHref(),
          title: "Открыть отправки на FBO",
        },
        {
          label: "Клиенту FBS",
          value: inventory.in_transit.fbs_to_customer,
          href: operationsHref("fbs-to-customer"),
          title: "Открыть отправки клиентам FBS",
        },
      ],
    },
  ];

  return (
    <section className="summary-groups" aria-label="Сводка по остаткам">
      {groups.map((group) => (
        <article className="summary-group" key={group.label}>
          <h2>{group.label}</h2>
          <div className="summary-grid">
            {group.items.map((item) => {
              const content = (
                <>
                  <p>{item.label}</p>
                  <strong>{item.value}</strong>
                </>
              );

              return item.href ? (
                <a
                  className="metric metric--link"
                  href={item.href}
                  key={item.label}
                  title={item.title}
                >
                  {content}
                </a>
              ) : (
                <div className="metric" key={item.label}>
                  {content}
                </div>
              );
            })}
          </div>
        </article>
      ))}
    </section>
  );
}
