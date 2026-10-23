import React, { useState, useEffect } from 'react';
import { ShieldCheck, Lock, User as UserIcon, Mail, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';

interface LoginProps {
  initialUser?: User | null;
  onLoginSuccess: (user: User) => void;
}

type AuthMode = 'login' | 'setup' | 'change_password';

export const Login: React.FC<LoginProps> = ({ initialUser, onLoginSuccess }) => {
  const [mode, setMode] = useState<AuthMode>(initialUser?.must_change_password ? 'change_password' : 'login');
  const [loading, setLoading] = useState(false);
  const [checkingSetup, setCheckingSetup] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form Fields
  const [username, setUsername] = useState('admin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('admin');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Check setup status on load
  useEffect(() => {
    if (initialUser?.must_change_password) {
      setMode('change_password');
      setCheckingSetup(false);
      return;
    }

    const checkSetup = async () => {
      try {
        const status = await api.getSetupStatus();
        if (status.setup_required) {
          setMode('setup');
        } else {
          setMode('login');
        }
      } catch (err) {
        // Fallback to login if check fails
        setMode('login');
      } finally {
        setCheckingSetup(false);
      }
    };

    checkSetup();
  }, [initialUser]);

  const validatePasswordRules = (pwd: string) => {
    return {
      length: pwd.length >= 12,
      upper: /[A-Z]/.test(pwd),
      lower: /[a-z]/.test(pwd),
      digit: /[0-9]/.test(pwd),
      symbol: /[^A-Za-z0-9]/.test(pwd),
    };
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      setSuccessMsg('');
      const data = await api.login(username, password);
      if (data.user.must_change_password) {
        setCurrentPassword(password);
        setPassword('');
        setMode('change_password');
        setSuccessMsg('Authentication successful. A mandatory password change is required before proceeding.');
      } else {
        onLoginSuccess(data.user);
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    const rules = validatePasswordRules(password);
    if (!rules.length || !rules.upper || !rules.lower || !rules.digit || !rules.symbol) {
      setError('Password does not satisfy enterprise complexity requirements (>= 12 chars, upper, lower, number, symbol).');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setSuccessMsg('');
      const res = await api.initialSetup({
        username,
        email,
        password,
        confirm_password: confirmPassword,
      });
      setSuccessMsg('Admin credentials created successfully. Initializing workspace...');
      setTimeout(() => {
        onLoginSuccess(res.user);
      }, 700);
    } catch (err: any) {
      setError(err.message || 'Setup failed. Please check input parameters.');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }

    const rules = validatePasswordRules(newPassword);
    if (!rules.length || !rules.upper || !rules.lower || !rules.digit || !rules.symbol) {
      setError('New password does not satisfy enterprise complexity requirements (>= 12 chars, upper, lower, number, symbol).');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setSuccessMsg('');
      const res = await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setSuccessMsg('Password updated successfully. System unlocked.');
      setTimeout(() => {
        onLoginSuccess(res.user);
      }, 700);
    } catch (err: any) {
      setError(err.message || 'Password update failed.');
    } finally {
      setLoading(false);
    }
  };

  if (checkingSetup) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-primary)',
        color: '#94A3B8'
      }}>
        <div style={{ textAlign: 'center' }}>
          <ShieldCheck size={36} color="var(--cyber-cyan)" style={{ animation: 'pulse 1.5s infinite' }} />
          <p style={{ marginTop: 12, fontSize: '0.9rem' }}>Verifying platform security posture...</p>
        </div>
      </div>
    );
  }

  const pwdToInspect = mode === 'setup' ? password : newPassword;
  const rulesState = validatePasswordRules(pwdToInspect);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--bg-primary)',
      backgroundImage: 'radial-gradient(circle at center, rgba(0, 240, 255, 0.05) 0%, transparent 65%)',
      padding: 20
    }}>
      <div style={{
        width: '100%',
        maxWidth: mode === 'setup' ? 460 : 430,
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-active)',
        borderRadius: 14,
        padding: 32,
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 240, 255, 0.1)'
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{
            width: 52,
            height: 52,
            borderRadius: 12,
            background: 'linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(139, 92, 246, 0.2))',
            border: '1px solid var(--cyber-cyan)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--cyber-cyan)',
            boxShadow: 'var(--glow-cyan)',
            marginBottom: 12
          }}>
            {mode === 'change_password' ? <ShieldAlert size={28} /> : <ShieldCheck size={28} />}
          </div>
          <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#FFFFFF', letterSpacing: 0.5 }}>
            Vuln<span style={{ color: 'var(--cyber-cyan)' }}>AI</span> X
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#94A3B8', marginTop: 4 }}>
            {mode === 'setup' && 'First-Time Setup: Create Platform Administrator'}
            {mode === 'login' && 'Autonomous Security Research Platform'}
            {mode === 'change_password' && 'Security Policy: Mandatory Password Rotation'}
          </p>
        </div>

        {error && (
          <div style={{
            padding: '10px 14px',
            borderRadius: 6,
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid var(--cyber-crimson)',
            color: '#FCA5A5',
            fontSize: '0.85rem',
            marginBottom: 18,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div style={{
            padding: '10px 14px',
            borderRadius: 6,
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid var(--cyber-emerald)',
            color: '#6EE7B7',
            fontSize: '0.85rem',
            marginBottom: 18,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <CheckCircle2 size={16} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* MODE 1: LOGIN */}
        {mode === 'login' && (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  className="form-control"
                  style={{ paddingLeft: 38 }}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter administrator or researcher username"
                  required
                />
                <UserIcon size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: 12 }} />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="password"
                  className="form-control"
                  style={{ paddingLeft: 38 }}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  required
                />
                <Lock size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: 12 }} />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', marginTop: 12, padding: 12 }}
            >
              {loading ? 'Authenticating...' : 'Sign In to VulnAI X'}
            </button>
          </form>
        )}

        {/* MODE 2: FIRST-TIME SETUP */}
        {mode === 'setup' && (
          <form onSubmit={handleSetup}>
            <div style={{
              padding: '10px 14px',
              borderRadius: 6,
              backgroundColor: 'rgba(0, 240, 255, 0.08)',
              border: '1px solid rgba(0, 240, 255, 0.25)',
              color: '#A5F3FC',
              fontSize: '0.8rem',
              marginBottom: 16
            }}>
              No administrator account exists yet. Establish initial credentials to initialize the secure enclave.
            </div>

            <div className="form-group">
              <label className="form-label">Admin Username</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  className="form-control"
                  style={{ paddingLeft: 38 }}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. security-lead"
                  required
                />
                <UserIcon size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: 12 }} />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Admin Email</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="email"
                  className="form-control"
                  style={{ paddingLeft: 38 }}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@vulnai-x.corp"
                  required
                />
                <Mail size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: 12 }} />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Admin Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="password"
                  className="form-control"
                  style={{ paddingLeft: 38 }}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 12 chars (Upper, Lower, Number, Symbol)"
                  required
                />
                <Lock size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: 12 }} />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="password"
                  className="form-control"
                  style={{ paddingLeft: 38 }}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  required
                />
                <Lock size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: 12 }} />
              </div>
            </div>

            {/* Complexity Indicator */}
            {password.length > 0 && (
              <div style={{
                fontSize: '0.72rem',
                backgroundColor: 'rgba(0,0,0,0.3)',
                padding: '8px 12px',
                borderRadius: 6,
                marginBottom: 16,
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 4
              }}>
                <span style={{ color: rulesState.length ? 'var(--cyber-emerald)' : '#94A3B8' }}>
                  {rulesState.length ? '✓' : '○'} ≥ 12 Characters
                </span>
                <span style={{ color: rulesState.upper ? 'var(--cyber-emerald)' : '#94A3B8' }}>
                  {rulesState.upper ? '✓' : '○'} Uppercase Letter
                </span>
                <span style={{ color: rulesState.lower ? 'var(--cyber-emerald)' : '#94A3B8' }}>
                  {rulesState.lower ? '✓' : '○'} Lowercase Letter
                </span>
                <span style={{ color: (rulesState.digit && rulesState.symbol) ? 'var(--cyber-emerald)' : '#94A3B8' }}>
                  {(rulesState.digit && rulesState.symbol) ? '✓' : '○'} Number & Symbol
                </span>
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', marginTop: 10, padding: 12 }}
            >
              {loading ? 'Configuring Security Enclave...' : 'Initialize Enclave & Sign In'}
            </button>
          </form>
        )}

        {/* MODE 3: FORCE PASSWORD CHANGE */}
        {mode === 'change_password' && (
          <form onSubmit={handleChangePassword}>
            <div style={{
              padding: '10px 14px',
              borderRadius: 6,
              backgroundColor: 'rgba(234, 179, 8, 0.12)',
              border: '1px solid rgba(234, 179, 8, 0.35)',
              color: '#FDE047',
              fontSize: '0.8rem',
              marginBottom: 16
            }}>
              Your account has a temporary or default credential flag. You must establish a new high-entropy password before platform features can be unlocked.
            </div>

            <div className="form-group">
              <label className="form-label">Current / Temporary Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="password"
                  className="form-control"
                  style={{ paddingLeft: 38 }}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
                <Lock size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: 12 }} />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">New Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="password"
                  className="form-control"
                  style={{ paddingLeft: 38 }}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Min 12 chars (Upper, Lower, Number, Symbol)"
                  required
                />
                <Lock size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: 12 }} />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Confirm New Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="password"
                  className="form-control"
                  style={{ paddingLeft: 38 }}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new password"
                  required
                />
                <Lock size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: 12 }} />
              </div>
            </div>

            {/* Complexity Indicator */}
            {newPassword.length > 0 && (
              <div style={{
                fontSize: '0.72rem',
                backgroundColor: 'rgba(0,0,0,0.3)',
                padding: '8px 12px',
                borderRadius: 6,
                marginBottom: 16,
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 4
              }}>
                <span style={{ color: rulesState.length ? 'var(--cyber-emerald)' : '#94A3B8' }}>
                  {rulesState.length ? '✓' : '○'} ≥ 12 Characters
                </span>
                <span style={{ color: rulesState.upper ? 'var(--cyber-emerald)' : '#94A3B8' }}>
                  {rulesState.upper ? '✓' : '○'} Uppercase Letter
                </span>
                <span style={{ color: rulesState.lower ? 'var(--cyber-emerald)' : '#94A3B8' }}>
                  {rulesState.lower ? '✓' : '○'} Lowercase Letter
                </span>
                <span style={{ color: (rulesState.digit && rulesState.symbol) ? 'var(--cyber-emerald)' : '#94A3B8' }}>
                  {(rulesState.digit && rulesState.symbol) ? '✓' : '○'} Number & Symbol
                </span>
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', marginTop: 10, padding: 12 }}
            >
              {loading ? 'Rotating Security Keys...' : 'Set New Password & Unlock System'}
            </button>
          </form>
        )}

        {/* Quick Credentials Pill */}
        <div style={{
          marginTop: 20,
          padding: 10,
          borderRadius: 6,
          backgroundColor: 'rgba(0, 240, 255, 0.05)',
          border: '1px solid rgba(0, 240, 255, 0.2)',
          textAlign: 'center',
          fontSize: '0.8rem',
          color: '#94A3B8'
        }}>
          <div><b>Default Credentials:</b></div>
          <div style={{ color: 'var(--cyber-cyan)', fontFamily: 'monospace', marginTop: 2, fontWeight: 600 }}>
            admin / admin
          </div>
        </div>

        {/* Security Notice Footer */}
        <div style={{
          marginTop: 14,
          padding: 10,
          borderRadius: 6,
          backgroundColor: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-subtle)',
          textAlign: 'center',
          fontSize: '0.75rem',
          color: '#94A3B8'
        }}>
          <div><b>Security Enclave Active</b></div>
          <div style={{ color: '#64748B', marginTop: 2 }}>
            JWT Authorization • Anti-Rebinding SSRF Shield • Strict Bug Bounty Scope
          </div>
        </div>
      </div>
    </div>
  );
};
