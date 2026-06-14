function screenshotUrl(path: string): string {
  const normalized = path.replace(/^\/+/, '');
  return '/' + normalized.split('/').map(encodeURIComponent).join('/');
}

interface ScreenshotGridProps {
  screenshots: string[];
}

export function ScreenshotGrid({ screenshots }: ScreenshotGridProps) {
  if (!screenshots.length) {
    return (
      <p className="text-muted text-sm text-center py-4 border border-dashed border-border rounded-lg">
        No screenshots captured.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {screenshots.map((s, i) => (
        <figure key={i} className="border border-border rounded-lg overflow-hidden bg-bg">
          <a href={screenshotUrl(s)} target="_blank" rel="noopener noreferrer">
            <img src={screenshotUrl(s)} alt={s} loading="lazy" className="w-full block bg-black" />
          </a>
          <figcaption className="px-3 py-2 text-xs text-muted truncate">{s}</figcaption>
        </figure>
      ))}
    </div>
  );
}
