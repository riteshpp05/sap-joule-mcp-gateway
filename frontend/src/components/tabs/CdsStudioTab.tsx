import React, { useState } from 'react';
import { Database, Sparkles, Copy, UploadCloud, Layers, CheckCircle2, Code2 } from 'lucide-react';
import { api } from '../../services/api';
import { CdsCreateResponse } from '../../types/api';

export const CdsStudioTab: React.FC = () => {
  const [prompt, setPrompt] = useState<string>(
    'Create an executive CDS View for Sales Orders from VBAK with Customer and Total Net Amount, exposed to Fiori'
  );
  const [viewName, setViewName] = useState<string>('Z_I_SalesOrder_View');
  const [tableName, setTableName] = useState<string>('vbak');
  const [fields, setFields] = useState<string>('key vbeln as SalesOrder\nerdat as CreationDate\nkunnr as CustomerNumber\nnetwr as NetAmount');
  const [viewType, setViewType] = useState<'entity' | 'classic'>('entity');
  const [exposeFiori, setExposeFiori] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [createdView, setCreatedView] = useState<CdsCreateResponse | null>(null);
  const [pushing, setPushing] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);

  const handleAiGenerate = async () => {
    if (!prompt.trim()) return;
    setGenerating(true);
    setStatusMsg('');
    try {
      const res = await api.generateCdsFromEnglish(prompt);
      if (res.view_name) setViewName(res.view_name);
      if (res.table_name) setTableName(res.table_name);
      if (res.fields && Array.isArray(res.fields)) {
        setFields(res.fields.join('\n'));
      }
      if (res.view_type) setViewType(res.view_type);
      setStatusMsg('AI schema generated successfully. Review parameters and compile DDL.');
    } catch (err: any) {
      alert(`AI Generation failed: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleCompileDdl = async (pushLive = false) => {
    const fieldList = fields
      .split('\n')
      .map((f) => f.trim())
      .filter(Boolean);

    if (!viewName || !tableName || fieldList.length === 0) {
      alert('Please specify view name, primary table, and at least one field projection.');
      return;
    }

    if (pushLive) setPushing(true);
    setStatusMsg('');
    try {
      const res = await api.createCdsView({
        view_name: viewName,
        table_name: tableName,
        fields: fieldList,
        view_type: viewType,
        expose_to_fiori: exposeFiori,
        push_to_sap: pushLive,
      });
      setCreatedView(res);
      setStatusMsg(pushLive ? 'CDS View pushed and activated live in SAP ADT!' : 'DDL syntax compiled successfully.');
    } catch (err: any) {
      alert(`Compilation failed: ${err.message}`);
    } finally {
      if (pushLive) setPushing(false);
    }
  };

  const copyToClipboard = () => {
    if (!createdView) return;
    navigator.clipboard.writeText(createdView.ddl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '420px 1fr', gap: 16, height: '100%', minHeight: 650 }}>
      {/* ── Left Pane: CDS Generation Form ── */}
      <div className="surface" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: '#ffffff',
        }}>
          <Database size={15} color="#2563eb" />
          <span style={{ fontSize: 13, fontWeight: 600, color: '#0f172a' }}>CDS Model Studio</span>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Natural Language Prompt */}
          <div className="surface-subtle" style={{ padding: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, color: '#2563eb', fontSize: 11, fontWeight: 600 }}>
              <Sparkles size={13} />
              <span>NATURAL LANGUAGE TO CDS</span>
            </div>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={2}
              className="input"
              style={{ resize: 'none', marginBottom: 10 }}
              placeholder="e.g. Create a CDS view for Billing Documents from VBRK with Item Net Value..."
            />
            <button
              onClick={handleAiGenerate}
              disabled={generating}
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
            >
              <Sparkles size={13} className={generating ? 'spin' : ''} />
              <span>{generating ? 'Synthesizing CDS Model...' : 'Generate CDS Model'}</span>
            </button>
          </div>

          {/* Architecture Toggle */}
          <div>
            <label className="label">S/4HANA Architecture</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <button
                type="button"
                onClick={() => setViewType('entity')}
                style={{
                  padding: '9px 12px',
                  borderRadius: 6,
                  border: viewType === 'entity' ? '1px solid #2563eb' : '1px solid var(--color-border)',
                  background: viewType === 'entity' ? '#eff6ff' : '#ffffff',
                  color: viewType === 'entity' ? '#1e40af' : '#64748b',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ fontSize: 12, fontWeight: 600 }}>CDS View Entity</div>
                <div style={{ fontSize: 10.5, color: '#64748b', marginTop: 2 }}>ABAP 7.55+ (No SQL view)</div>
              </button>

              <button
                type="button"
                onClick={() => setViewType('classic')}
                style={{
                  padding: '9px 12px',
                  borderRadius: 6,
                  border: viewType === 'classic' ? '1px solid #2563eb' : '1px solid var(--color-border)',
                  background: viewType === 'classic' ? '#eff6ff' : '#ffffff',
                  color: viewType === 'classic' ? '#1e40af' : '#64748b',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ fontSize: 12, fontWeight: 600 }}>Classic CDS View</div>
                <div style={{ fontSize: 10.5, color: '#64748b', marginTop: 2 }}>NetWeaver Catalog SQL</div>
              </button>
            </div>
          </div>

          {/* View Name & Table */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label className="label">View Name</label>
              <input
                type="text"
                value={viewName}
                onChange={(e) => setViewName(e.target.value)}
                className="input mono"
              />
            </div>
            <div>
              <label className="label">Primary Table</label>
              <input
                type="text"
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                className="input mono"
                style={{ textTransform: 'uppercase' }}
              />
            </div>
          </div>

          {/* Field Projections */}
          <div>
            <label className="label">Field Projections (One per line)</label>
            <textarea
              value={fields}
              onChange={(e) => setFields(e.target.value)}
              rows={4}
              className="code-editor"
              style={{ width: '100%', minHeight: 100, color: '#0f172a', background: '#ffffff' }}
            />
          </div>

          {/* Fiori Checkbox */}
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#334155', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={exposeFiori}
              onChange={(e) => setExposeFiori(e.target.checked)}
              style={{ accentColor: '#2563eb' }}
            />
            <span>Auto-Expose to Fiori (@OData.publish: true)</span>
          </label>
        </div>

        {/* Action Buttons */}
        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--color-border)',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 10,
          background: '#f8fafc',
        }}>
          <button
            onClick={() => handleCompileDdl(false)}
            className="btn btn-ghost"
            style={{ justifyContent: 'center' }}
          >
            Compile DDL
          </button>
          <button
            onClick={() => handleCompileDdl(true)}
            disabled={pushing}
            className="btn btn-primary"
            style={{ justifyContent: 'center' }}
          >
            <UploadCloud size={13} className={pushing ? 'spin' : ''} />
            <span>{pushing ? 'Deploying...' : 'Deploy to SAP'}</span>
          </button>
        </div>
      </div>

      {/* ── Right Pane: DDL Output ── */}
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
            <Code2 size={15} color="#64748b" />
            <span style={{ fontSize: 13, fontWeight: 600, color: '#0f172a' }}>Compiled SAP DDL Definition</span>
            {createdView && (
              <span className="badge-blue mono">{createdView.view_type}</span>
            )}
          </div>
          {createdView && (
            <button
              onClick={copyToClipboard}
              className="btn btn-ghost"
              style={{ padding: '3px 8px', fontSize: 11 }}
            >
              <Copy size={12} />
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          )}
        </div>

        {statusMsg && (
          <div style={{
            padding: '8px 16px',
            background: '#ecfdf5',
            borderBottom: '1px solid #a7f3d0',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 12,
            color: '#065f46',
          }}>
            <CheckCircle2 size={14} />
            <span>{statusMsg}</span>
          </div>
        )}

        <div style={{ flex: 1, padding: 16, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
          {createdView ? (
            <pre className="code-display" style={{
              flex: 1,
              margin: 0,
              padding: 16,
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: 6,
              color: '#0f172a',
              overflow: 'auto',
              lineHeight: 1.6,
            }}>
              {createdView.ddl}
            </pre>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-dim)', textAlign: 'center' }}>
              <Layers size={32} color="#cbd5e1" style={{ marginBottom: 12 }} />
              <div style={{ fontSize: 13, fontWeight: 600, color: '#64748b', marginBottom: 4 }}>No DDL Generated</div>
              <div style={{ fontSize: 11.5, maxWidth: 320, color: '#94a3b8', lineHeight: 1.5 }}>
                Use natural language generation or click "Compile DDL" to inspect synthesized ABAP Core Data Services code.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
