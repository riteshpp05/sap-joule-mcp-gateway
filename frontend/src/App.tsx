import React, { useState, useEffect } from 'react';
import { St22Tab } from './components/tabs/St22Tab';
import { CdsStudioTab } from './components/tabs/CdsStudioTab';
import { AbapUnitTab } from './components/tabs/AbapUnitTab';
import { CtsGovernanceTab } from './components/tabs/CtsGovernanceTab';
import { ObservabilityTab } from './components/tabs/ObservabilityTab';
import { ChatDrawer } from './components/tabs/ChatDrawer';
import { api } from './services/api';

type TabId = 'st22' | 'cds' | 'unit' | 'cts' | 'metrics';

const TABS: { id: TabId; label: string }[] = [
  { id: 'st22', label: 'ST22 Triage' },
  { id: 'cds', label: 'CDS Studio' },
  { id: 'unit', label: 'Unit Tests' },
  { id: 'cts', label: 'CTS Governance' },
  { id: 'metrics', label: 'Observability' },
];

export const App: React.FC = () => {
  const [tab, setTab] = useState<TabId>('st22');
  const [chatOpen, setChatOpen] = useState(false);
  const [mockMode, setMockMode] = useState<boolean | null>(null);

  useEffect(() => {
    api.getReadiness()
      .then(r => setMockMode(r.mock_mode))
      .catch(() => setMockMode(null));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#f8fafc' }}>
      {/* ── Top Bar ── */}
      <header style={{
        height: 48,
        borderBottom: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        flexShrink: 0,
        background: '#ffffff',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.02)',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 26, height: 26, borderRadius: 6,
            background: '#2563eb',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 9.5, fontWeight: 700, color: '#ffffff', letterSpacing: 0.5,
          }}>SAP</div>
          <span style={{ fontWeight: 600, fontSize: 13.5, color: '#0f172a', letterSpacing: '-0.01em' }}>
            Joule AI Studio
          </span>
          <span style={{ color: '#cbd5e1', fontSize: 13 }}>/</span>
          <span style={{ fontSize: 12, color: '#64748b' }}>
            ABAP &amp; CDS Gateway
          </span>
          {mockMode !== null && (
            <span className={mockMode ? 'badge-success' : 'badge-warn'} style={{ marginLeft: 6 }}>
              {mockMode ? '● Mock Mode' : '● Live SAP'}
            </span>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            className="btn btn-ghost"
            onClick={() => window.open('/docs', '_blank')}
          >
            API Docs
          </button>
          <button
            className="btn btn-ghost"
            style={chatOpen ? { borderColor: '#2563eb', color: '#2563eb', background: '#eff6ff' } : {}}
            onClick={() => setChatOpen(v => !v)}
          >
            ✦ Joule Assistant
          </button>
        </div>
      </header>

      {/* ── Tab Bar ── */}
      <nav style={{
        borderBottom: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        gap: 4,
        flexShrink: 0,
        background: '#ffffff',
        position: 'sticky',
        top: 48,
        zIndex: 40,
      }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: '11px 16px',
              fontSize: 12.5,
              fontWeight: tab === t.id ? 600 : 500,
              background: 'none',
              border: 'none',
              borderBottom: tab === t.id ? '2px solid #2563eb' : '2px solid transparent',
              color: tab === t.id ? '#0f172a' : '#64748b',
              cursor: 'pointer',
              transition: 'all 0.15s',
              letterSpacing: '-0.01em',
              marginBottom: -1,
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* ── Content ── */}
      <main style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
        {tab === 'st22' && <St22Tab />}
        {tab === 'cds' && <CdsStudioTab />}
        {tab === 'unit' && <AbapUnitTab />}
        {tab === 'cts' && <CtsGovernanceTab />}
        {tab === 'metrics' && <ObservabilityTab />}
      </main>

      <ChatDrawer isOpen={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
};
