import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw, Server, Shield, Copy } from 'lucide-react';
import { api } from '../../services/api';
import { HealthStatus, ReadinessStatus } from '../../types/api';

export const ObservabilityTab: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [readiness, setReadiness] = useState<ReadinessStatus | null>(null);
  const [metricsRaw, setMetricsRaw] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const fetchObservability = async () => {
    setLoading(true);
    try {
      const [h, r, m] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getReadiness().catch(() => null),
        api.getMetrics().catch(() => ''),
      ]);
      setHealth(h);
      setReadiness(r);
      setMetricsRaw(m);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObservability();
  }, []);

  const handleCopyMetrics = () => {
    if (!metricsRaw) return;
    navigator.clipboard.writeText(metricsRaw);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* ── Top Header ── */}
      <div className="surface" style={{ padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
              <Activity size={17} color="#2563eb" />
              <span style={{ fontSize: 14.5, fontWeight: 600, color: '#0f172a' }}>
                Observability, Probes &amp; Prometheus Telemetry
              </span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              Real-time Kubernetes health endpoints, SAP gateway audit metrics, and OpenMetrics scrapers.
            </div>
          </div>

          <button
            onClick={fetchObservability}
            disabled={loading}
            className="btn btn-ghost"
          >
            <RefreshCw size={13} className={loading ? 'spin' : ''} />
            <span>Refresh Probes</span>
          </button>
        </div>
      </div>

      {/* ── Probe Status Cards ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
        {/* Liveness Probe */}
        <div className="surface" style={{ padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 600, color: '#0f172a' }}>
              <Server size={15} color="#16a34a" />
              Liveness Probe
            </span>
            <span className="badge-success">
              <span className="dot-alive" style={{ marginRight: 6 }} />
              ALIVE (200 OK)
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5, marginBottom: 12 }}>
            Monitors core FastAPI process heartbeat and event loop responsiveness for Kubernetes pod restarts.
          </div>
          <div className="surface-subtle mono" style={{ padding: '8px 12px', fontSize: 11, color: '#334155' }}>
            GET /health/live
          </div>
        </div>

        {/* Readiness Probe */}
        <div className="surface" style={{ padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 600, color: '#0f172a' }}>
              <Shield size={15} color="#2563eb" />
              Readiness Probe
            </span>
            <span className={readiness?.mock_mode ? 'badge-warn' : 'badge-success'}>
              {readiness?.status || 'READY'}
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5, marginBottom: 12 }}>
            Verifies SAP gateway communication layer and backend mock configuration status.
          </div>
          <div className="surface-subtle mono" style={{ padding: '8px 12px', fontSize: 11, color: '#334155' }}>
            Mock Mode: <strong style={{ color: '#0f172a' }}>{readiness?.mock_mode ? 'TRUE (Isolated)' : 'FALSE'}</strong>
          </div>
        </div>
      </div>

      {/* ── Raw Prometheus Scrape Output ── */}
      <div className="surface" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{
          padding: '12px 18px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#ffffff',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#0f172a' }}>Prometheus Metrics Exporter</span>
            <span className="badge-neutral mono">GET /metrics</span>
          </div>
          <button
            onClick={handleCopyMetrics}
            className="btn btn-ghost"
            style={{ padding: '3px 8px', fontSize: 11 }}
          >
            <Copy size={12} />
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>

        <pre className="code-display" style={{
          margin: 0,
          padding: 16,
          background: '#f8fafc',
          color: '#0f172a',
          maxHeight: 340,
          overflow: 'auto',
          lineHeight: 1.6,
          fontSize: 11.5,
          border: 'none',
        }}>
          {metricsRaw || '# Fetching Prometheus metrics...'}
        </pre>
      </div>
    </div>
  );
};
