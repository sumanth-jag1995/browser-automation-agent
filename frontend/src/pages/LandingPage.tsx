import { useState } from 'react';
import { Menu } from 'lucide-react';
import { HamburgerMenu } from '../components/HamburgerMenu';
import { RunForm } from '../components/RunForm';
import { LogPanel } from '../components/LogPanel';
import { useRunPoller } from '../hooks/useRunPoller';

export function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const { logs, done } = useRunPoller(activeRunId);

  return (
    <div className="min-h-screen bg-bg text-text flex flex-col">
      <header className="px-6 py-4 border-b border-border bg-surface flex items-center gap-4">
        <button
          onClick={() => setMenuOpen(true)}
          className="text-muted hover:text-text"
          aria-label="Open settings"
        >
          <Menu size={22} />
        </button>
        <h1 className="font-semibold text-base">Browser Automation AI Agent</h1>
      </header>

      <HamburgerMenu open={menuOpen} onClose={() => setMenuOpen(false)} />

      <main className="flex-1 flex flex-col items-center justify-start px-4 pt-16 pb-8">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-text mb-2">Browser Automation AI Agent</h2>
          <p className="text-muted">Describe a flow. We'll automate and test it.</p>
        </div>

        <RunForm onRunStarted={setActiveRunId} />

        {activeRunId && (
          <LogPanel runId={activeRunId} logs={logs} done={done} />
        )}
      </main>
    </div>
  );
}
