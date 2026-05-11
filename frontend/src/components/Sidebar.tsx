import React from 'react';
import { MessageSquare, Plus, LogOut } from 'lucide-react';

interface ChatSession {
  id: string;
  title: string;
  created_at: number;
}

interface SidebarProps {
  chats: ChatSession[];
  activeChatId: string | null;
  onSelectChat: (id: string | null) => void;
  onLogout: () => void;
}

export default function Sidebar({ chats, activeChatId, onSelectChat, onLogout }: SidebarProps) {
  const username = localStorage.getItem('username');

  return (
    <div style={{ 
      width: '260px', 
      backgroundColor: 'var(--bg-secondary)', 
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
    }}>
      <div style={{ padding: '1rem' }}>
        <button 
          onClick={() => onSelectChat(null)}
          style={{ 
            width: '100%', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.5rem', 
            padding: '0.75rem', 
            backgroundColor: 'var(--accent-primary)', 
            color: 'white', 
            border: 'none', 
            borderRadius: 'var(--radius-md)', 
            cursor: 'pointer',
            fontWeight: 500
          }}
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '0 0.5rem' }}>
        {chats.map(chat => (
          <button
            key={chat.id}
            onClick={() => onSelectChat(chat.id)}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.75rem',
              backgroundColor: chat.id === activeChatId ? 'var(--bg-tertiary)' : 'transparent',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              color: 'var(--text-primary)',
              textAlign: 'left',
              marginBottom: '0.25rem'
            }}
          >
            <MessageSquare size={18} color="var(--text-secondary)" />
            <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '0.875rem' }}>
              {chat.title}
            </span>
          </button>
        ))}
      </div>

      <div style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>
          {username}
        </div>
        <button 
          onClick={onLogout}
          style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex' }}
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>
    </div>
  );
}
