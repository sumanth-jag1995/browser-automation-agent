import { useState, type FormEvent } from 'react';
import { Play } from 'lucide-react';
import { api } from '../api/client';
import { useSettings } from '../hooks/useSettings';

interface RunFormProps {
  onRunStarted: (runId: string) => void;
}

export function RunForm({ onRunStarted }: RunFormProps) {
  const { settings } = useSettings();
  const [intent, setIntent] = useState('');
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.startRun({
        url,
        intent,
        openrouter_api_key: settings.openrouterApiKey || undefined,
        openrouter_model: settings.openrouterModel,
        use_mock_llm: settings.useMockLlm,
        max_retries: settings.maxRetries,
        max_repair_before_regenerate: settings.maxRepairBeforeRegenerate,
      });
      onRunStarted(res.run_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start run');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="rounded-lg border border-border overflow-hidden">
        <textarea
          value={intent}
          onChange={e => setIntent(e.target.value)}
          placeholder="Describe what you want to test…"
          rows={4}
          required
          className="w-full bg-surface px-4 py-3 text-text placeholder:text-muted text-sm resize-none focus:outline-none border-b border-border"
        />
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="https://example.com"
          required
          className="w-full bg-surface px-4 py-3 text-text placeholder:text-muted text-sm focus:outline-none"
        />
      </div>
      {error && <p className="mt-2 text-fail text-sm">{error}</p>}
      <div className="mt-4 flex justify-center">
        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
        >
          <Play size={16} />
          {loading ? 'Starting…' : 'Run Automation'}
        </button>
      </div>
    </form>
  );
}
