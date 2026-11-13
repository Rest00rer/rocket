import { type FormEvent, useState } from "react";

import { errorMessage } from "../../app/useCheckStock";
import { mutate } from "../../shared/api/client";
import type { Warehouse } from "../../shared/api/types";

export function WarehousePanel({
  selectedWarehouseId,
  warehouses,
  onComplete,
}: {
  selectedWarehouseId?: string;
  warehouses: Warehouse[];
  onComplete: () => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setBusyId("create");
    setError(null);
    try {
      await mutate("/warehouses", { name: name.trim() });
      setName("");
      await onComplete();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusyId(null);
    }
  }

  async function rename(id: string) {
    if (!editingName.trim()) return;
    setBusyId(id);
    setError(null);
    try {
      await mutate(`/warehouses/${id}`, { name: editingName.trim() }, "PATCH");
      setEditingId(null);
      await onComplete();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusyId(null);
    }
  }

  async function archive(warehouse: Warehouse) {
    if (
      !window.confirm(
        `Перенести склад «${warehouse.name}» в архив? Остатки сохранятся.`,
      )
    )
      return;
    setBusyId(warehouse.id);
    setError(null);
    try {
      await mutate(`/warehouses/${warehouse.id}`, undefined, "DELETE");
      await onComplete();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="panel" id="warehouses">
      <div className="panel-heading">
        <div>
          <h2>Управление складами</h2>
        </div>
      </div>
      <form className="add-warehouse" onSubmit={create}>
        <label>
          <span className="sr-only">Название нового склада</span>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Новый склад"
            maxLength={255}
          />
        </label>
        <button
          className="button button--secondary"
          disabled={busyId === "create"}
          type="submit"
        >
          Добавить
        </button>
      </form>
      {error && (
        <p className="inline-feedback inline-feedback--error">{error}</p>
      )}
      <ul className="warehouse-list">
        {warehouses.map((warehouse) => (
          <li
            className={
              warehouse.id === selectedWarehouseId
                ? "warehouse-row--selected"
                : undefined
            }
            key={warehouse.id}
          >
            {editingId === warehouse.id ? (
              <>
                <input
                  autoFocus
                  value={editingName}
                  onChange={(event) => setEditingName(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void rename(warehouse.id);
                    if (event.key === "Escape") setEditingId(null);
                  }}
                />
                <button
                  className="text-button"
                  disabled={busyId === warehouse.id}
                  type="button"
                  onClick={() => void rename(warehouse.id)}
                >
                  Сохранить
                </button>
              </>
            ) : (
              <>
                <div>
                  <strong>{warehouse.name}</strong>
                  {warehouse.archived && <span>Архив</span>}
                </div>
                <div className="row-actions">
                  {!warehouse.archived && (
                    <>
                      <button
                        className="text-button"
                        type="button"
                        onClick={() => {
                          setEditingId(warehouse.id);
                          setEditingName(warehouse.name);
                        }}
                      >
                        Переименовать
                      </button>
                      <button
                        className="text-button text-button--danger"
                        disabled={busyId === warehouse.id}
                        type="button"
                        onClick={() => void archive(warehouse)}
                      >
                        В архив
                      </button>
                    </>
                  )}
                </div>
              </>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
