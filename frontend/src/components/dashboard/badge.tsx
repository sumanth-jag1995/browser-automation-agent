const STATUS_CLASSES: Record<string, string> = {
  success: 'bg-success/20 text-success',
  failed: 'bg-fail/20 text-fail',
  fail: 'bg-fail/20 text-fail',
  escalated: 'bg-warn/20 text-warn',
  regression: 'bg-warn/20 text-warn',
  running: 'bg-accent/20 text-accent',
};

export function Badge({ status }: { status: string }) {
  const cls = STATUS_CLASSES[status?.toLowerCase()] ?? 'bg-border/40 text-muted';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${cls}`}>
      {status ?? 'unknown'}
    </span>
  );
}
