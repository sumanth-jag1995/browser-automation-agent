import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SettingsProvider } from './hooks/useSettings';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';

export function App() {
  return (
    <SettingsProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/:runId" element={<DashboardPage />} />
        </Routes>
      </BrowserRouter>
    </SettingsProvider>
  );
}
