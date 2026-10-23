import React from 'react';
import { LogOut, User as UserIcon } from 'lucide-react';
import { User } from '../types';

interface HeaderProps {
  title: string;
  workerOnline: boolean;
  user: User | null;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, workerOnline, user, onLogout }) => {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <h1 className="page-title">{title}</h1>
      </div>

      <div className="topbar-right">
        <div className="worker-pill">
          <div className={`pulse-dot ${workerOnline ? 'online' : 'offline'}`} />
          <span>Worker: {workerOnline ? 'Active' : 'Offline'}</span>
        </div>

        {user && (
          <div className="user-badge">
            <UserIcon size={14} color="#94A3B8" />
            <span>{user.username}</span>
            <span className="user-role-tag">{user.role}</span>
          </div>
        )}

        <button className="logout-btn" onClick={onLogout} title="Sign Out">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
};
