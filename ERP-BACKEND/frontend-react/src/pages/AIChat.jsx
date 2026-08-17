import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  MessageSquare, Send, Loader, Bot, User, Lightbulb, Sparkles,
  ChevronLeft, Plus, Clock, Zap, Settings, Trash2, Archive,
  Cpu, BarChart3, Wrench, FileText, ArrowRight, Copy, Check
} from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function AIChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [templates, setTemplates] = useState([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [copied, setCopied] = useState(false);
  const messagesEndRef = useRef(null);
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };
  const navigate = useNavigate();

  useEffect(() => {
    fetchConversations();
    fetchModels();
    fetchTemplates();
  }, []);

  const fetchConversations = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/v1/llm/conversations`, axiosConfig);
      setConversations(res.data);
    } catch (e) {}
  };

  const fetchModels = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/v1/llm/models`, axiosConfig);
      setModels(res.data.models || []);
      const defaultModel = res.data.models?.find(m => m.is_default);
      if (defaultModel) setSelectedModel(defaultModel.model_id);
    } catch (e) {}
  };

  const fetchTemplates = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/v1/llm/templates`, axiosConfig);
      setTemplates(res.data);
    } catch (e) {}
  };

  const loadConversation = async (id) => {
    try {
      const res = await axios.get(`${API_URL}/api/v1/llm/conversations/${id}`, axiosConfig);
      const conv = res.data;
      setConversationId(conv.id);
      setMessages(conv.messages.map(m => ({ role: m.role, content: m.content })));
      if (conv.model_id) setSelectedModel(conv.model_id);
    } catch (e) {}
  };

  const newConversation = () => {
    setConversationId(null);
    setMessages([]);
    setInput('');
  };

  const deleteConversation = async (id, e) => {
    e.stopPropagation();
    if (!confirm('Delete this conversation?')) return;
    try {
      await axios.delete(`${API_URL}/api/v1/llm/conversations/${id}`, axiosConfig);
      if (conversationId === id) newConversation();
      fetchConversations();
    } catch (e) {}
  };

  const archiveConversation = async (id, e) => {
    e.stopPropagation();
    try {
      await axios.put(`${API_URL}/api/v1/llm/conversations/${id}/archive`, {}, axiosConfig);
      if (conversationId === id) newConversation();
      fetchConversations();
    } catch (e) {}
  };

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  const sendMessage = async (useStream = false) => {
    if (!input.trim() || loading || streaming) return;
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setLoading(true);

    if (useStream) {
      await streamResponse(userMsg);
    } else {
      await regularResponse(userMsg);
    }
  };

  const regularResponse = async (userMsg) => {
    try {
      const res = await axios.post(`${API_URL}/api/v1/llm/chat`, {
        messages: [...messages, { role: 'user', content: userMsg }].map(m => ({ role: m.role, content: m.content })),
        model_id: selectedModel,
        conversation_id: conversationId,
        use_tools: true
      }, axiosConfig);

      const assistantContent = res.data.message?.content || 'No response';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: assistantContent,
        model: res.data.message?.model,
        tokens: res.data.message?.tokens_used,
        latency: res.data.message?.latency_ms
      }]);

      if (res.data.conversation_id && !conversationId) {
        setConversationId(res.data.conversation_id);
        fetchConversations();
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + (e.response?.data?.detail || e.message) }]);
    } finally {
      setLoading(false);
    }
  };

  const streamResponse = async (userMsg) => {
    setStreaming(true);
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }]);

    try {
      const response = await fetch(`${API_URL}/api/v1/llm/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          messages: [...messages, { role: 'user', content: userMsg }].map(m => ({ role: m.role, content: m.content })),
          model_id: selectedModel
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'content') {
                fullContent += data.content;
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMsg = newMessages[newMessages.length - 1];
                  if (lastMsg.role === 'assistant' && lastMsg.streaming) {
                    lastMsg.content = fullContent;
                  }
                  return newMessages;
                });
              } else if (data.type === 'done') {
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMsg = newMessages[newMessages.length - 1];
                  if (lastMsg.streaming) {
                    delete lastMsg.streaming;
                    lastContent.tokens = data.total_tokens;
                  }
                  return newMessages;
                });
              }
            } catch (e) {}
          }
        }
      }

      fetchConversations();
    } catch (e) {
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg.streaming) {
          lastMsg.content = 'Error: Streaming failed';
          delete lastMsg.streaming;
        }
        return newMessages;
      });
    } finally {
      setStreaming(false);
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const applyTemplate = (template) => {
    setInput(template.user_prompt_template || '');
  };

  const quickQuestions = [
    'What is my total pipeline value?',
    'Which products are low on stock?',
    'Show me revenue trends',
    'Who are my top customers?',
    'Create a summary of all active projects'
  ];

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-72 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <button onClick={newConversation} className="w-full btn-primary flex items-center justify-center gap-2 py-2.5">
              <Plus className="w-4 h-4" /> New Chat
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider px-2 mb-2">Recent Conversations</p>
            {conversations.map(conv => (
              <div
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer text-sm mb-1 transition-colors ${
                  conversationId === conv.id ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-gray-50 text-gray-700'
                }`}
              >
                <MessageSquare className="w-4 h-4 flex-shrink-0" />
                <span className="truncate flex-1">{conv.title || 'Untitled'}</span>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={(e) => archiveConversation(conv.id, e)} className="p-1 hover:bg-gray-200 rounded">
                    <Archive className="w-3 h-3 text-gray-400" />
                  </button>
                  <button onClick={(e) => deleteConversation(conv.id, e)} className="p-1 hover:bg-red-100 rounded">
                    <Trash2 className="w-3 h-3 text-red-400" />
                  </button>
                </div>
              </div>
            ))}
            {conversations.length === 0 && (
              <p className="text-sm text-gray-400 px-2 py-4 text-center">No conversations yet</p>
            )}
          </div>

          <div className="p-3 border-t border-gray-200">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Templates</p>
            <div className="space-y-1">
              {templates.slice(0, 5).map(t => (
                <button
                  key={t.id}
                  onClick={() => applyTemplate(t)}
                  className="w-full text-left px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50 rounded flex items-center gap-1.5"
                >
                  <FileText className="w-3 h-3" />
                  {t.display_name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Header */}
        <div className="h-14 border-b border-gray-200 flex items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <button onClick={() => setShowSidebar(!showSidebar)} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500">
              <ChevronLeft className={`w-5 h-5 transition-transform ${!showSidebar ? 'rotate-180' : ''}`} />
            </button>
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-indigo-600" />
              <h2 className="font-semibold text-gray-900">AI Assistant</h2>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Model Selector */}
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {models.map(m => (
                <option key={m.model_id} value={m.model_id}>
                  {m.display_name} {m.is_default ? '(Default)' : ''}
                </option>
              ))}
            </select>

            <button onClick={() => navigate('/llm-manager')} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500" title="LLM Manager">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-2xl flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">How can I help you today?</h3>
              <p className="text-gray-500 max-w-md mb-6">Ask about your business data, get insights, or use templates for specific tasks.</p>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {quickQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => { setInput(q); }}
                    className="px-4 py-2 bg-gray-100 text-gray-600 rounded-full text-sm hover:bg-gray-200 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                </div>
              )}
              <div className={`max-w-[80%] ${msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-800'} rounded-lg p-3`}>
                <div className="text-sm whitespace-pre-wrap">{msg.content || (msg.streaming ? <span className="animate-pulse">▋</span> : '')}</div>

                {msg.role === 'assistant' && !msg.streaming && (
                  <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-200/50">
                    {msg.model && <span className="text-xs text-gray-400">{msg.model}</span>}
                    {msg.tokens && <span className="text-xs text-gray-400">{msg.tokens} tokens</span>}
                    {msg.latency && <span className="text-xs text-gray-400">{msg.latency}ms</span>}
                    <button onClick={() => copyToClipboard(msg.content)} className="ml-auto p-1 hover:bg-gray-200 rounded">
                      {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3 text-gray-400" />}
                    </button>
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <User className="w-4 h-4 text-gray-600" />
                </div>
              )}
            </div>
          ))}

          {loading && !streaming && (
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

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2 mb-3">
            {templates.slice(0, 3).map(t => (
              <button
                key={t.id}
                onClick={() => applyTemplate(t)}
                className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-full text-xs hover:bg-gray-200 transition-colors flex items-center gap-1"
              >
                <Lightbulb className="w-3 h-3" />
                {t.display_name}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(e.metaKey || e.ctrlKey);
                }
              }}
              placeholder="Ask about your business... (Cmd+Enter to stream)"
              className="flex-1 input-field"
              disabled={loading || streaming}
            />
            <button
              onClick={() => sendMessage(true)}
              disabled={loading || streaming || !input.trim()}
              className="btn-primary px-4 flex items-center gap-2"
              title="Stream response"
            >
              <Zap className="w-4 h-4" />
            </button>
            <button
              onClick={() => sendMessage(false)}
              disabled={loading || streaming || !input.trim()}
              className="btn-primary px-4"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2">Press Enter to send, Cmd+Enter to stream • Model: {selectedModel}</p>
        </div>
      </div>
    </div>
  );
}

