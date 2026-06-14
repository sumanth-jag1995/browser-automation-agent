import { X, Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';
import { useSettings } from '../hooks/useSettings';

const MODELS = [
  { value: 'anthropic/claude-haiku-4-5', label: 'Claude Haiku 4.5' },
  { value: 'anthropic/claude-sonnet-4', label: 'Claude Sonnet 4' },
];

interface HamburgerMenuProps {
  open: boolean;
  onClose: () => void;
}

export function HamburgerMenu({ open, onClose }: HamburgerMenuProps) {
  const { settings, updateSettings } = useSettings();
  const [showKey, setShowKey] = useState(false);

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <aside className="fixed top-0 left-0 h-full w-72 bg-surface border-r border-border z-50 p-6 overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-text font-semibold text-lg">Settings</h2>
          <button onClick={onClose} className="text-muted hover:text-text" aria-label="Close settings">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-5">
          <div>
            <label className="block text-xs text-muted uppercase tracking-wide mb-1">
              OpenRouter API Key
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={settings.openrouterApiKey}
                onChange={e => updateSettings({ openrouterApiKey: e.target.value })}
                placeholder="sk-or-v1-…"
                className="w-full bg-bg border border-border rounded px-3 py-2 text-text text-sm pr-9 focus:outline-none focus:border-accent"
              />
              <button
                type="button"
                onClick={() => setShowKey(v => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted hover:text-text"
                aria-label={showKey ? 'Hide key' : 'Show key'}
              >
                {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs text-muted uppercase tracking-wide mb-1">
              Model
            </label>
            <select
              value={settings.openrouterModel}
              onChange={e => updateSettings({ openrouterModel: e.target.value })}
              className="w-full bg-bg border border-border rounded px-3 py-2 text-text text-sm focus:outline-none focus:border-accent"
            >
              {MODELS.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-between">
            <label className="text-xs text-muted uppercase tracking-wide">Use Mock LLM</label>
            <button
              type="button"
              role="switch"
              aria-checked={settings.useMockLlm}
              onClick={() => updateSettings({ useMockLlm: !settings.useMockLlm })}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                settings.useMockLlm ? 'bg-accent' : 'bg-border'
              }`}
            >
              <span
                className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  settings.useMockLlm ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div>
            <label className="block text-xs text-muted uppercase tracking-wide mb-1">
              Max Retries
            </label>
            <input
              type="number"
              min={0}
              max={10}
              value={settings.maxRetries}
              onChange={e => updateSettings({ maxRetries: Number(e.target.value) })}
              className="w-full bg-bg border border-border rounded px-3 py-2 text-text text-sm focus:outline-none focus:border-accent"
            />
          </div>

          <div>
            <label className="block text-xs text-muted uppercase tracking-wide mb-1">
              Max Repairs Before Regenerate
            </label>
            <input
              type="number"
              min={0}
              max={10}
              value={settings.maxRepairBeforeRegenerate}
              onChange={e => updateSettings({ maxRepairBeforeRegenerate: Number(e.target.value) })}
              className="w-full bg-bg border border-border rounded px-3 py-2 text-text text-sm focus:outline-none focus:border-accent"
            />
          </div>
        </div>
      </aside>
    </>
  );
}
