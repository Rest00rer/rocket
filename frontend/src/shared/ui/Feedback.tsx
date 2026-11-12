export function LoadingState() {
  return (
    <div className="state-panel" role="status">
      <span className="spinner" aria-hidden="true" />
      <div>
        <strong>Загружаем остатки</strong>
        <p>Проверяем склады и незавершённые операции.</p>
      </div>
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="state-panel state-panel--error" role="alert">
      <div>
        <strong>Не удалось получить данные</strong>
        <p>{message}</p>
      </div>
      <button
        className="button button--secondary"
        type="button"
        onClick={onRetry}
      >
        Повторить
      </button>
    </div>
  );
}

export function EmptyState({ children }: { children: string }) {
  return <p className="empty-state">{children}</p>;
}
