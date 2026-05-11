import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Sidebar from '../components/Sidebar';
import { useNavigate } from 'react-router-dom';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
};

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [chats, setChats] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const userId = localStorage.getItem('user_id');

  useEffect(() => {
    if (!userId) {
      navigate('/');
      return;
    }
    fetchChats();
  }, [userId]);

  useEffect(() => {
    if (activeChatId) {
      fetchMessages(activeChatId);
    } else {
      setMessages([{
        id: '1',
        role: 'assistant',
        content: 'Hello! I am the HVAC Manual Assistant. Start typing to create a new chat.'
      }]);
    }
  }, [activeChatId]);

  const fetchChats = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/chats?user_id=${userId}`);
      if (res.ok) {
        const data = await res.json();
        setChats(data.chats);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchMessages = async (chatId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/chats/${chatId}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages.map((m: any) => ({
          id: m.id.toString(),
          role: m.role,
          content: m.content
        })));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !userId) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    const assistantMessageId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: assistantMessageId, role: 'assistant', content: '' }]);

    let currentChatId = activeChatId;

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: input, 
          user_id: parseInt(userId), 
          chat_id: currentChatId,
          top_k: 5 
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch response');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let done = false;
        let buffer = '';

        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) {
            buffer += decoder.decode(value, { stream: true });
            
            const parts = buffer.split(/\r?\n\r?\n/);
            buffer = parts.pop() || '';

            for (const part of parts) {
              const lines = part.split(/\r?\n/);
              let eventName = 'message';
              let eventData = '';
              
              for (const line of lines) {
                if (line.startsWith('event: ')) {
                  eventName = line.substring(7).trim();
                } else if (line.startsWith('data: ')) {
                  eventData = line.substring(6).trim();
                }
              }

              if (eventName === 'meta' && eventData) {
                const data = JSON.parse(eventData);
                if (!currentChatId) {
                  currentChatId = data.chat_id;
                  setActiveChatId(currentChatId);
                  fetchChats(); // Refresh sidebar
                }
              } else if (eventName === 'token' && eventData) {
                try {
                  const data = JSON.parse(eventData);
                  setMessages(prev => prev.map(m => 
                    m.id === assistantMessageId ? { ...m, content: m.content + data.text } : m
                  ));
                } catch (e) {
                  console.error('Error parsing token', e);
                }
              } else if (eventName === 'error' && eventData) {
                try {
                  const data = JSON.parse(eventData);
                  setMessages(prev => prev.map(m => 
                    m.id === assistantMessageId ? { ...m, content: m.content + `\n\n**Error:** ${data.detail}` } : m
                  ));
                } catch (e) {}
              } else if (eventName === 'sources' && eventData) {
                try {
                  const data = JSON.parse(eventData);
                  if (data.chunks && data.chunks.length > 0) {
                    const sourcesMD = data.chunks.map((c: any, i: number) => {
                      const label = c.subsection || c.section || '-';
                      const page = c.page || '?';
                      return `[${i + 1}] ${label} | p.${page} | ${c.chunk_type || ''}`;
                    }).join('\n');
                    
                    const images = Array.from(new Set(data.chunks.flatMap((c: any) => c.linked_images || [])));
                    const imagesMD = images.length > 0 
                      ? '\n\n**Images:**\n\n' + images.map((img: any) => `![${img}](http://localhost:8000/api/images/${img})`).join('\n\n') 
                      : '';
                    
                    setMessages(prev => prev.map(m => 
                      m.id === assistantMessageId ? { ...m, content: m.content + '\n\n---\n**Sources:**\n\n' + sourcesMD + imagesMD } : m
                    ));
                  }
                } catch (e) {}
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: 'Sorry, I encountered an error.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    navigate('/');
  };

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', backgroundColor: 'var(--bg-primary)' }}>
      <Sidebar 
        chats={chats} 
        activeChatId={activeChatId} 
        onSelectChat={setActiveChatId} 
        onLogout={handleLogout}
      />
      
      <main className="chat-main" style={{ boxShadow: 'none', borderLeft: '1px solid var(--border-color)', maxWidth: 'none' }}>
        <header className="chat-header" style={{ justifyContent: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%', maxWidth: '48rem', margin: '0 auto' }}>
            <div style={{ backgroundColor: 'var(--accent-light)', padding: '0.5rem', borderRadius: 'var(--radius-md)', color: 'var(--accent-primary)' }}>
              <Bot size={24} />
            </div>
            <div>
              <h1>HVAC Manual Assistant</h1>
              <p>Ask technical questions based on the HVAC manuals</p>
            </div>
          </div>
        </header>

        <div className="message-list" style={{ maxWidth: '48rem', margin: '0 auto', width: '100%' }}>
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className={`avatar ${message.role}`}>
                {message.role === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              <div className="message-content">
                {message.role === 'assistant' ? (
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                ) : (
                  message.content
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="avatar assistant">
                <Bot size={20} />
              </div>
              <div className="typing-indicator">
                <div className="dot"></div><div className="dot"></div><div className="dot"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area" style={{ maxWidth: '48rem', margin: '0 auto', width: '100%', borderTop: 'none', paddingBottom: '2rem' }}>
          <form onSubmit={handleSubmit} className="input-form">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your HVAC query here..."
              className="chat-input"
              disabled={isLoading}
            />
            <button type="submit" className="send-button" disabled={!input.trim() || isLoading}>
              {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
