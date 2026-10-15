import React, { useState, useEffect } from 'react';
import { AlertCircle, RefreshCw, CheckCircle2, Play, RotateCcw, Lock, Terminal } from 'lucide-react';
import { api } from '../../services/api';
import { DumpItem, AutoFixProposal, PushFixResult } from '../../types/api';

export const St22Tab: React.FC = () => {
  const [dumps, setDumps] = useState<DumpItem[]>([]);
  const [selectedDump, setSelectedDump] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [proposing, setProposing] = useState<boolean>(false);
  const [proposal, setProposal] = useState<AutoFixProposal | null>(null);
  const [pushResult, setPushResult] = useState<PushFixResult | null>(null);
  const [pushing, setPushing] = useState<boolean>(false);
  const [autoRollback, setAutoRollback] = useState<boolean>(true);
  const [runUnitTests, setRunUnitTests] = useState<boolean>(true);

  const fetchDumps = async () => {
    setLoading(true);
    try {
      const data = await api.listRecentDumps(15);
      const safeList = Array.isArray(data) ? data : [];
      setDumps(safeList);
      if (safeList.length > 0 && !selectedDump) {
        setSelectedDump(safeList[0].dump_id);
      }
    } catch (err: any) {
      console.error('Error fetching ST22 dumps:', err);
      setDumps([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDumps();
  }, []);

  const handleProposeFix = async () => {
    if (!selectedDump) return;
    setProposing(true);
    setProposal(null);
    setPushResult(null);
    try {
      const res = await api.proposeAutoFix(selectedDump);
      setProposal(res);
    } catch (err: any) {
      alert(`Error proposing fix: ${err.message}`);
    } finally {
      setProposing(false);
    }
  };

  const handleConfirmPush = async () => {
    if (!proposal) return;
    setPushing(true);
    setPushResult(null);
    try {
      const res = await api.pushAbapFix({
        program_name: proposal.target_program,
        fixed_code: proposal.proposed_code,
        dump_id: proposal.dump_id,
        confirm_push: true,
        run_unit_tests: runUnitTests,
        auto_rollback_on_test_failure: autoRollback,
      });
      setPushResult(res);
    } catch (err: any) {
      alert(`Push error: ${err.message}`);
    } finally {
      setPushing(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 16, height: '100%', minHeight: 650 }}>
      {/* ── Left Pane: ST22 Dump Logs ── */}
      <div className="surface" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#ffffff',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>ST22 Dumps</span>
            <span className="badge-neutral">{dumps.length}</span>
          </div>
          <button
            onClick={fetchDumps}
            disabled={loading}
            className="btn btn-ghost"
            style={{ padding: '4px 8px' }}
            title="Refresh logs"
          >
            <RefreshCw size={12} className={loading ? 'spin' : ''} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
          {dumps.length === 0 ? (
            <div style={{ padding: '36px 16px', textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>
              {loading ? 'Querying SAP ST22...' : 'No runtime short dumps found.'}
            </div>
          ) : (
            dumps.map((d) => {
              const isSelected = selectedDump === d.dump_id;
              return (
                <div
                  key={d.dump_id}
                  onClick={() => setSelectedDump(d.dump_id)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 6,
                    cursor: 'pointer',
                    marginBottom: 4,
                    transition: 'all 0.15s ease',
                    background: isSelected ? '#eff6ff' : 'transparent',
                    border: isSelected ? '1px solid #bfdbfe' : '1px solid transparent',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) (e.currentTarget.style.background = '#f8fafc');
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) (e.currentTarget.style.background = 'transparent');
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span className="mono" style={{ fontSize: 11, fontWeight: 600, color: isSelected ? '#2563eb' : '#334155' }}>
                      {d.dump_id}
                    </span>
                    <span style={{ fontSize: 11, color: '#94a3b8' }}>
                      {d.timestamp}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 500, color: '#0f172a', marginBottom: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {d.title}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#64748b' }}>
                    <span className="mono">{d.program}</span>
                    <span>{d.user}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div style={{ padding: 12, borderTop: '1px solid var(--color-border)', background: '#f8fafc' }}>
          <button
            onClick={handleProposeFix}
            disabled={!selectedDump || proposing}
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            {proposing ? (
              <>
                <RefreshCw size={13} className="spin" />
                <span>Synthesizing Fix...</span>
              </>
            ) : (
              <>
                <Play size={13} />
                <span>AI Analyze &amp; Auto-Fix</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Right Pane: AI Resolution & Push Studio ── */}
      <div className="surface" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {proposal ? (
          <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Header / Overview */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span className="badge-error mono">{proposal.exception_type}</span>
                  <span style={{ fontSize: 15, fontWeight: 600, color: '#0f172a' }}>
                    {proposal.target_program}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                  {proposal.user_controller_message}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="badge-warn">Review Required</span>
                <span className="badge-blue mono">{proposal.dump_id}</span>
              </div>
            </div>

            {/* AI Root-Cause Diagnostic */}
            <div className="surface-subtle" style={{ padding: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, color: '#2563eb', fontSize: 11, fontWeight: 600, letterSpacing: '0.03em' }}>
                <Terminal size={13} />
                <span>AI ROOT CAUSE DIAGNOSIS</span>
              </div>
              <div className="mono" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, color: '#334155', fontSize: 11.5 }}>
                {proposal.ai_analysis}
              </div>
            </div>

            {/* Code Diff / Review Panels */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, flex: 1, minHeight: 280 }}>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label className="label" style={{ color: '#dc2626' }}>Faulty Original Source</label>
                <textarea
                  readOnly
                  value={proposal.original_code || ''}
                  className="code-display"
                  style={{
                    flex: 1,
                    minHeight: 260,
                    color: '#991b1b',
                    background: '#fff5f5',
                    border: '1px solid #fecaca',
                    borderRadius: 6,
                    padding: 12,
                    resize: 'none',
                    outline: 'none',
                  }}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label className="label" style={{ color: '#16a34a' }}>AI Remediated Clean ABAP</label>
                <textarea
                  value={proposal.proposed_code || ''}
                  onChange={(e) => setProposal({ ...proposal, proposed_code: e.target.value })}
                  className="code-editor"
                  style={{
                    flex: 1,
                    minHeight: 260,
                    color: '#166534',
                    background: '#f0fdf4',
                    border: '1px solid #bbf7d0',
                    borderRadius: 6,
                    padding: 12,
                    resize: 'none',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            {/* Governance & Push Actions Bar */}
            <div className="surface-subtle" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#334155', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={autoRollback}
                    onChange={(e) => setAutoRollback(e.target.checked)}
                    style={{ accentColor: '#2563eb' }}
                  />
                  <span>Atomic Rollback on Failure</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#334155', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={runUnitTests}
                    onChange={(e) => setRunUnitTests(e.target.checked)}
                    style={{ accentColor: '#2563eb' }}
                  />
                  <span>Run ABAP Unit Test Gate</span>
                </label>
              </div>

              <button
                onClick={handleConfirmPush}
                disabled={pushing}
                className="btn btn-primary"
                style={{ background: '#16a34a', borderColor: '#16a34a' }}
              >
                {pushing ? (
                  <>
                    <RefreshCw size={13} className="spin" />
                    <span>Pushing &amp; Activating in SAP...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={13} />
                    <span>Approve &amp; Push to SAP</span>
                  </>
                )}
              </button>
            </div>

            {/* Push / Execution Feedback Banner */}
            {pushResult && (
              <div
                style={{
                  padding: '12px 14px',
                  borderRadius: 6,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 10,
                  fontSize: 12,
                  background:
                    pushResult.status === 'ACTIVATED' || pushResult.pushed
                      ? '#ecfdf5'
                      : pushResult.lock_conflict
                      ? '#fffbeb'
                      : '#fef2f2',
                  border:
                    pushResult.status === 'ACTIVATED' || pushResult.pushed
                      ? '1px solid #a7f3d0'
                      : pushResult.lock_conflict
                      ? '1px solid #fde68a'
                      : '1px solid #fecaca',
                }}
              >
                {pushResult.status === 'ACTIVATED' || pushResult.pushed ? (
                  <CheckCircle2 size={16} color="#16a34a" style={{ marginTop: 2, flexShrink: 0 }} />
                ) : pushResult.lock_conflict ? (
                  <Lock size={16} color="#d97706" style={{ marginTop: 2, flexShrink: 0 }} />
                ) : (
                  <RotateCcw size={16} color="#dc2626" style={{ marginTop: 2, flexShrink: 0 }} />
                )}
                <div>
                  <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: 2 }}>
                    Status: {pushResult.status}
                    {pushResult.rollback_performed && ' — Automated Rollback Completed'}
                  </div>
                  <div style={{ color: '#475569', lineHeight: 1.5 }}>
                    {pushResult.message}
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 40, textAlign: 'center' }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#f1f5f9', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}>
              <AlertCircle size={22} color="#94a3b8" />
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#0f172a', marginBottom: 6 }}>
              No Short Dump Selected
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', maxWidth: 360, lineHeight: 1.6 }}>
              Select an ST22 runtime dump from the left panel and click <strong style={{ color: '#0f172a' }}>AI Analyze &amp; Auto-Fix</strong> to trigger autonomous root-cause diagnosis and code synthesis.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
