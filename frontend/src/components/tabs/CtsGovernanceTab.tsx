import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, FolderPlus, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { TransportValidationResult } from '../../types/api';

export const CtsGovernanceTab: React.FC = () => {
  // Transport Validation State
  const [packageName, setPackageName] = useState<string>('ZDEV_CORE');
  const [transportRequest, setTransportRequest] = useState<string>('DEVK900123');
  const [validationResult, setValidationResult] = useState<TransportValidationResult | null>(null);
  const [validating, setValidating] = useState<boolean>(false);

  // Package Creation State
  const [newPkgName, setNewPkgName] = useState<string>('ZDEV_LOGISTICS');
  const [newPkgDesc, setNewPkgDesc] = useState<string>('Core supply chain logistics package');
  const [creatingPkg, setCreatingPkg] = useState<boolean>(false);
  const [pkgResult, setPkgResult] = useState<any | null>(null);

  const handleValidate = async () => {
    setValidating(true);
    setValidationResult(null);
    try {
      const res = await api.validateTransportRequest({
        package: packageName.trim().toUpperCase(),
        transport_request: transportRequest.trim().toUpperCase() || undefined,
      });
      setValidationResult(res);
    } catch (err: any) {
      alert(`Validation error: ${err.message}`);
    } finally {
      setValidating(false);
    }
  };

  const handleCreatePackage = async () => {
    if (!newPkgName.trim()) return;
    setCreatingPkg(true);
    setPkgResult(null);
    try {
      const res = await api.createPackage({
        package_name: newPkgName.trim().toUpperCase(),
        description: newPkgDesc.trim(),
        push_to_sap: false,
      });
      setPkgResult(res);
    } catch (err: any) {
      alert(`Package creation failed: ${err.message}`);
    } finally {
      setCreatingPkg(false);
    }
  };

  return (
    <div style={{ maxWidth: 880, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* ── Section 1: CTS Transport Request Governance ── */}
      <div className="surface" style={{ padding: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <ShieldCheck size={17} color="#2563eb" />
            <span style={{ fontSize: 14.5, fontWeight: 600, color: '#0f172a' }}>
              CTS Transport Request Governance
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            Enforces SAP Change &amp; Transport System standards. Non-local transportable packages mandate an active Transport Request in <span className="mono" style={{ color: '#0f172a', fontWeight: 600 }}>&lt;SID&gt;K9XXXXX</span> format.
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label className="label">Target SAP Package</label>
            <input
              type="text"
              value={packageName}
              onChange={(e) => setPackageName(e.target.value)}
              placeholder="e.g. $TMP or ZDEV_CORE"
              className="input mono"
              style={{ textTransform: 'uppercase' }}
            />
            <span style={{ fontSize: 11, color: '#64748b', marginTop: 4, display: 'block' }}>
              Use <strong style={{ color: '#334155' }}>$TMP</strong> for local objects, or custom package name.
            </span>
          </div>

          <div>
            <label className="label">CTS Transport Request</label>
            <input
              type="text"
              value={transportRequest}
              onChange={(e) => setTransportRequest(e.target.value)}
              placeholder="e.g. DEVK900123"
              className="input mono"
              style={{ textTransform: 'uppercase' }}
            />
            <span style={{ fontSize: 11, color: '#64748b', marginTop: 4, display: 'block' }}>
              Standard SAP format: 3-character SID + 'K' + 6 digits.
            </span>
          </div>
        </div>

        <div>
          <button
            onClick={handleValidate}
            disabled={validating}
            className="btn btn-primary"
          >
            {validating ? (
              <>
                <RefreshCw size={13} className="spin" />
                <span>Verifying CTS Compliance...</span>
              </>
            ) : (
              <span>Validate Transport Request</span>
            )}
          </button>
        </div>

        {validationResult && (
          <div
            style={{
              padding: '12px 16px',
              borderRadius: 6,
              fontSize: 12.5,
              background: validationResult.valid ? '#ecfdf5' : '#fef2f2',
              border: validationResult.valid ? '1px solid #a7f3d0' : '1px solid #fecaca',
              color: validationResult.valid ? '#065f46' : '#991b1b',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, marginBottom: 4 }}>
              {validationResult.valid ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
              <span>{validationResult.valid ? 'CTS Validation Succeeded' : 'CTS Validation Rejected'}</span>
            </div>
            <div style={{ color: '#334155', marginBottom: 6, lineHeight: 1.5 }}>
              {validationResult.message}
            </div>
            <div className="mono" style={{ fontSize: 11, color: '#64748b' }}>
              Package: <strong>{validationResult.package}</strong> | Local Object: <strong>{validationResult.is_local ? 'YES' : 'NO'}</strong>
            </div>
          </div>
        )}
      </div>

      {/* ── Section 2: SAP DevClass / Package Provisioning ── */}
      <div className="surface" style={{ padding: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <FolderPlus size={17} color="#2563eb" />
            <span style={{ fontSize: 14.5, fontWeight: 600, color: '#0f172a' }}>
              Development Package Definition (DevClass)
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            Synthesizes ADT-compliant <span className="mono" style={{ color: '#0f172a', fontWeight: 600 }}>adtcore:package</span> XML definition for structured enterprise ABAP object management.
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label className="label">Package Name</label>
            <input
              type="text"
              value={newPkgName}
              onChange={(e) => setNewPkgName(e.target.value)}
              placeholder="e.g. ZDEV_LOGISTICS"
              className="input mono"
              style={{ textTransform: 'uppercase' }}
            />
          </div>

          <div>
            <label className="label">Package Description</label>
            <input
              type="text"
              value={newPkgDesc}
              onChange={(e) => setNewPkgDesc(e.target.value)}
              placeholder="e.g. Supply chain logistics logic"
              className="input"
            />
          </div>
        </div>

        <div>
          <button
            onClick={handleCreatePackage}
            disabled={creatingPkg}
            className="btn btn-ghost"
          >
            {creatingPkg ? (
              <>
                <RefreshCw size={13} className="spin" />
                <span>Synthesizing Package...</span>
              </>
            ) : (
              <span>Synthesize Package Metadata</span>
            )}
          </button>
        </div>

        {pkgResult && (
          <div className="surface-subtle" style={{ padding: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 12.5, fontWeight: 600, color: '#16a34a' }}>
                Package Definition Ready: {pkgResult.package_name || newPkgName}
              </span>
              <span className="badge-neutral mono">{pkgResult.status || 'COMPILED'}</span>
            </div>
            {pkgResult.package_xml && (
              <pre className="code-display" style={{
                maxHeight: 180,
                overflow: 'auto',
                padding: 12,
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: 4,
                color: '#1e40af',
                fontSize: 11,
              }}>
                {pkgResult.package_xml}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
