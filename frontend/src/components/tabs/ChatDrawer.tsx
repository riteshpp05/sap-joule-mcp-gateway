import React, { useState } from 'react';
import { X, Send, Sparkles, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { ChatMessage } from '../../types/api';

interface ChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChatDrawer: React.FC<ChatDrawerProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Hello! I am your SAP Joule & ADT Copilot. Ask me how to resolve ST22 dumps, design S/4HANA CDS Views, configure CTS Transport Requests, or trigger ABAP Unit regression testing.',
    },
  ]);
  const [input, setInput] = useState<string>('');
  const [sending, setSending] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    const userMsg = input.trim();
    setInput('');
    const newHistory: ChatMessage[] = [...messages, { role: 'user', content: userMsg }];
    setMessages(newHistory);
    setSending(true);

    try {
      const res = await api.sendChat(newHistory);
      setMessages([...newHistory, { role: 'assistant', content: res.reply || 'No response.' }]);
    } catch (err: any) {
      setMessages([
        ...newHistory,
        { role: 'assistant', content: `Error: ${err.message}` },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      bottom: 0,
      width: 380,
      maxWidth: '100vw',
      background: '#ffffff',
      borderLeft: '1px solid var(--color-border)',
      boxShadow: '-8px 0 24px rgba(0,0,0,0.06)',
      zIndex: 100,
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* ── Header ── */}
      <div style={{
        padding: '12px 18px',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#ffffff',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sparkles size={15} color="#2563eb" />
          <span style={{ fontSize: 13.5, fontWeight: 600, color: '#0f172a' }}>Joule AI Copilot</span>
        </div>
        <button
          onClick={onClose}
          className="btn btn-ghost"
          style={{ padding: '4px 6px', border: 'none', background: 'transparent' }}
        >
          <X size={15} color="#64748b" />
        </button>
      </div>

      {/* ── Messages Feed ── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 14, background: '#f8fafc' }}>
        {messages.map((m, idx) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={idx}
              style={{
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                maxWidth: '88%',
                borderRadius: 8,
                padding: '10px 14px',
                fontSize: 12.5,
                lineHeight: 1.5,
                background: isUser ? '#2563eb' : '#ffffff',
                border: isUser ? '1px solid #1d4ed8' : '1px solid var(--color-border)',
                color: isUser ? '#ffffff' : '#0f172a',
                boxShadow: isUser ? '0 1px 2px rgba(37, 99, 235, 0.2)' : '0 1px 2px rgba(0, 0, 0, 0.04)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              <div style={{
                fontSize: 10,
                fontWeight: 600,
                color: isUser ? '#bfdbfe' : '#64748b',
                marginBottom: 4,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}>
                {isUser ? 'You' : 'Joule Assistant'}
              </div>
              {m.content}
            </div>
          );
        })}

        {sending && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11.5, color: '#64748b', padding: '6px 4px' }}>
            <RefreshCw size={12} className="spin" color="#2563eb" />
            <span>Joule is reasoning...</span>
          </div>
        )}
      </div>

      {/* ── Input Bar ── */}
      <div style={{
        padding: 14,
        borderTop: '1px solid var(--color-border)',
        background: '#ffffff',
        display: 'flex',
        gap: 8,
      }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask Joule Copilot..."
          className="input"
          style={{ flex: 1 }}
        />
        <button
          onClick={handleSend}
          disabled={sending || !input.trim()}
          className="btn btn-primary"
          style={{ padding: '7px 14px' }}
        >
          <Send size={13} />
        </button>
      </div>
    </div>
  );
};
