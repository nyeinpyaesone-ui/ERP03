import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Loader, Bot, User, Lightbulb, Sparkles } from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function AIChat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AI business assistant. Ask me about your contacts, deals, inventory, revenue, or any business insights.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/api/v1/ai/chat`, { message: userMsg }, axiosConfig);
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const quickQuestions = [
    'What is my total pipeline value?',
    'Which products are low on stock?',
    'Show me revenue trends',
    'Who are my top customers?',
    'What is my outstanding revenue?'
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      <h1 className="text-3xl font-bold text-gray-900 mb-4 flex items-center gap-3">
        <Bot className="w-8 h-8 text-indigo-600" /> AI Business Assistant
      </h1>
      <div className="flex-1 card overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                </div>
              )}
              <div className={`max-w-[80%] p-3 rounded-lg ${msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-gray-600" />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                <Loader className="w-4 h-4 text-indigo-600 animate-spin" />
              </div>
              <div className="bg-gray-100 p-3 rounded-lg">
                <p className="text-sm text-gray-500">Thinking...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
            {quickQuestions.map((q, i) => (
              <button key={i} onClick={() => { setInput(q); }}
                className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-full text-xs whitespace-nowrap hover:bg-gray-200 transition-colors flex items-center gap-1">
                <Lightbulb className="w-3 h-3" />{q}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask about your business..."
              className="flex-1 input-field"
            />
            <button onClick={sendMessage} disabled={loading} className="btn-primary px-4">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

