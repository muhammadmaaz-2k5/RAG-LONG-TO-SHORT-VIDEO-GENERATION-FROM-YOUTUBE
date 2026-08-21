import React, { useEffect } from 'react';
import { Sparkles, CheckCircle2, AlertCircle, X } from 'lucide-react';

export default function Toast({ message, type = 'success', onClose }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 4500);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`toast-notification glass-panel-elevated toast-${type}`}>
      <div className="toast-icon-wrapper">
        {type === 'error' ? (
          <AlertCircle size={18} className="text-red" />
        ) : (
          <CheckCircle2 size={18} className="text-emerald" />
        )}
      </div>
      <div className="toast-content">
        <p className="toast-message">{message}</p>
      </div>
      <button className="toast-close" onClick={onClose}>
        <X size={15} />
      </button>
    </div>
  );
}
