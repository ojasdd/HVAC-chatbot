import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, Loader2 } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    
    setError('');
    setIsLoading(true);
    
    const endpoint = isRegistering ? '/api/register' : '/api/login';
    
    try {
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }
      
      // Store user info and redirect
      localStorage.setItem('user_id', data.user_id.toString());
      localStorage.setItem('username', data.username);
      navigate('/chat');
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100vw', height: '100vh', backgroundColor: 'var(--bg-primary)' }}>
      <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '3rem 2rem', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-lg)', width: '100%', maxWidth: '400px', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', textAlign: 'center' }}>
          <div style={{ backgroundColor: 'var(--accent-light)', padding: '1rem', borderRadius: 'var(--radius-full)', color: 'var(--accent-primary)' }}>
            <Bot size={40} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {isRegistering ? 'Create an Account' : 'Welcome Back'}
            </h1>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem', fontSize: '0.9rem' }}>
              Sign in to access your HVAC Manual Assistant
            </p>
          </div>
        </div>

        {error && (
          <div style={{ backgroundColor: '#fee2e2', color: '#b91c1c', padding: '0.75rem', borderRadius: 'var(--radius-md)', fontSize: '0.875rem', textAlign: 'center' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>Username</label>
            <input 
              type="text" 
              value={username} 
              onChange={e => setUsername(e.target.value)} 
              required
              style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', outline: 'none' }} 
              placeholder="Enter your username"
            />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              required
              style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', outline: 'none' }} 
              placeholder="••••••••"
            />
          </div>

          <button 
            type="submit" 
            disabled={isLoading || !username || !password}
            style={{ 
              backgroundColor: 'var(--accent-primary)', color: 'white', padding: '0.75rem', 
              borderRadius: 'var(--radius-md)', border: 'none', fontWeight: 500, cursor: 'pointer', 
              display: 'flex', justifyContent: 'center', marginTop: '0.5rem' 
            }}
          >
            {isLoading ? <Loader2 className="animate-spin" size={20} /> : (isRegistering ? 'Sign Up' : 'Sign In')}
          </button>
        </form>

        <div style={{ textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          {isRegistering ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button 
            onClick={() => setIsRegistering(!isRegistering)} 
            style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', fontWeight: 500, cursor: 'pointer', padding: 0 }}
          >
            {isRegistering ? 'Sign In' : 'Sign Up'}
          </button>
        </div>
        
      </div>
    </div>
  );
}
