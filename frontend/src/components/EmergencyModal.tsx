import React, { useState } from 'react';
import { AlertOctagon, X } from 'lucide-react';
import { api } from '../services/api';

interface EmergencyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const EmergencyModal: React.FC<EmergencyModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [reason, setReason] = useState('Manual Emergency Stop initiated by researcher');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleStop = async () => {
    try {
      setLoading(true);
      setError('');
      await api.triggerEmergencyStop(reason);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to trigger emergency stop');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ borderColor: 'var(--cyber-crimson)' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#FCA5A5' }}>
            <AlertOctagon size={22} color="var(--cyber-crimson)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>EMERGENCY STOP PROTOCOL</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <p style={{ fontSize: '0.9rem', color: '#CBD5E1', marginBottom: 16 }}>
            Activating Emergency Stop will <b>immediately halt and cancel all active and queued research jobs</b>, terminate active agent processes, and reject any new research tasks.
          </p>

          {error && <div style={{ color: 'var(--cyber-crimson)', marginBottom: 12, fontSize: '0.85rem' }}>{error}</div>}

          <div className="form-group">
            <label className="form-label">Audit Reason for Emergency Stop</label>
            <textarea
              className="form-control"
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Provide reason for immediate halt..."
            />
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
            Dismiss
          </button>
          <button className="btn btn-danger" onClick={handleStop} disabled={loading}>
            {loading ? 'Halting...' : 'ACTIVATE EMERGENCY STOP'}
          </button>
        </div>
      </div>
    </div>
  );
};
