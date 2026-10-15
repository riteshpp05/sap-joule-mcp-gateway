import React, { useState } from 'react';
import { ShieldCheck, Play, RefreshCw, CheckCircle2, XCircle } from 'lucide-react';
import { api } from '../../services/api';
import { AbapUnitTestResult } from '../../types/api';

export const AbapUnitTab: React.FC = () => {
  const [programName, setProgramName] = useState<string>('ZTEST_CALCULATOR');
  const [running, setRunning] = useState<boolean>(false);
  const [result, setResult] = useState<AbapUnitTestResult | null>(null);

  const handleRunTests = async () => {
    if (!programName.trim()) return;
    setRunning(true);
    setResult(null);
    try {
      const res = await api.runAbapUnitTests(programName.trim().toUpperCase());
      setResult(res);
    } catch (err: any) {
      alert(`Test run failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* ── Top Bar / Action ── */}
      <div className="surface" style={{ padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
              <ShieldCheck size={17} color="#2563eb" />
              <span style={{ fontSize: 14, fontWeight: 600, color: '#0f172a' }}>
                ABAP Unit Automated Regression Testing Gate
              </span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              Executes isolated unit suites via <span className="mono" style={{ color: '#334155', fontWeight: 600 }}>/sap/bc/adt/abapunit/testruns</span> prior to code activation.
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="text"
              value={programName}
              onChange={(e) => setProgramName(e.target.value)}
              placeholder="e.g. ZTEST_CALCULATOR"
              className="input mono"
              style={{ width: 220, textTransform: 'uppercase' }}
            />
            <button
              onClick={handleRunTests}
              disabled={running}
              className="btn btn-primary"
            >
              {running ? (
                <>
                  <RefreshCw size={13} className="spin" />
                  <span>Executing...</span>
                </>
              ) : (
                <>
                  <Play size={13} />
                  <span>Run Suite</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {result ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* ── Summary Counters ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            <div className="surface" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 4, fontWeight: 600 }}>
                Total Tests
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#0f172a' }}>{result.tests_run}</div>
            </div>

            <div className="surface" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 11, color: '#16a34a', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 4, fontWeight: 600 }}>
                Passed
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#16a34a' }}>{result.passed}</div>
            </div>

            <div className="surface" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 11, color: '#dc2626', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 4, fontWeight: 600 }}>
                Failed
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#dc2626' }}>{result.failed}</div>
            </div>

            <div className="surface" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 11, color: '#d97706', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 4, fontWeight: 600 }}>
                Errors
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#d97706' }}>{result.errors}</div>
            </div>
          </div>

          {/* ── Status Banner ── */}
          <div
            style={{
              padding: '12px 16px',
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: 12.5,
              background: result.status === 'SUCCESS' ? '#ecfdf5' : '#fef2f2',
              border: result.status === 'SUCCESS' ? '1px solid #a7f3d0' : '1px solid #fecaca',
              color: result.status === 'SUCCESS' ? '#065f46' : '#991b1b',
            }}
          >
            {result.status === 'SUCCESS' ? <CheckCircle2 size={17} /> : <XCircle size={17} />}
            <span style={{ fontWeight: 600 }}>{result.message}</span>
          </div>

          {/* ── Test Details Table ── */}
          <div className="surface" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)', fontSize: 12.5, fontWeight: 600, color: '#0f172a', background: '#ffffff' }}>
              Test Method Execution Breakdown
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)', background: '#f8fafc', color: '#64748b', fontSize: 11 }}>
                  <th style={{ padding: '10px 16px', fontWeight: 600 }}>Class</th>
                  <th style={{ padding: '10px 16px', fontWeight: 600 }}>Method</th>
                  <th style={{ padding: '10px 16px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '10px 16px', fontWeight: 600 }}>Diagnostic Details</th>
                </tr>
              </thead>
              <tbody>
                {result.details.map((d, idx) => (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: idx === result.details.length - 1 ? 'none' : '1px solid #f1f5f9',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <td className="mono" style={{ padding: '10px 16px', color: '#0f172a', fontWeight: 500 }}>{d.test_class}</td>
                    <td className="mono" style={{ padding: '10px 16px', color: '#475569' }}>{d.method}</td>
                    <td style={{ padding: '10px 16px' }}>
                      <span className={d.status === 'PASSED' ? 'badge-success' : 'badge-error'}>
                        {d.status}
                      </span>
                    </td>
                    <td className="mono" style={{ padding: '10px 16px', color: '#64748b', fontSize: 11 }}>
                      {d.failure_detail || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="surface" style={{ padding: '52px 20px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <ShieldCheck size={38} color="#cbd5e1" style={{ marginBottom: 12 }} />
          <div style={{ fontSize: 14, fontWeight: 600, color: '#0f172a', marginBottom: 4 }}>
            Ready to Execute ABAP Unit Suite
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', maxWidth: 380, lineHeight: 1.5 }}>
            Specify a target ABAP test class or report above and click <strong style={{ color: '#0f172a' }}>Run Suite</strong> to evaluate regression test assertions.
          </div>
        </div>
      )}
    </div>
  );
};
