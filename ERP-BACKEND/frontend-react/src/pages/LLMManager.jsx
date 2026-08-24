import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Cpu, BarChart3, FileText, Plus, Trash2, ToggleLeft, ToggleRight,
  Download, CheckCircle, AlertTriangle, Clock, Zap, TrendingUp,
  Database, ArrowLeft, RefreshCw, Settings, MessageSquare, Layers
} from 'lucide-react';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function LLMManager() {
  const [activeTab, setActiveTab] = useState('models');
  const [models, setModels] = useState([]);
  const [availableModels, setAvailableModels] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [usage, setUsage] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [pulling, setPulling] = useState(false);
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [modelsRes, templatesRes, usageRes, convRes] = await Promise.all([
        axios.get(`${API_URL}/api/v1/llm/models`, axiosConfig),
        axios.get(`${API_URL}/api/v1/llm/templates`, axiosConfig),
        axios.get(`${API_URL}/api/v1/llm/analytics/usage?days=30`, axiosConfig),
        axios.get(`${API_URL}/api/v1/llm/analytics/conversations`, axiosConfig),
      ]);
      setModels(modelsRes.data.models || []);
      setAvailableModels(modelsRes.data.available_from_provider || []);
      setTemplates(templatesRes.data);
      setUsage(usageRes.data);
      setConversations(convRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load LLM data');
    } finally {
      setLoading(false);
    }
  };

  const pullModel = async (modelId) => {
    setPulling(true);
    try {
      await axios.post(`${API_URL}/api/v1/llm/models/${modelId}/pull`, {}, axiosConfig);
      setSuccess(`Model ${modelId} pulled successfully`);
      fetchAllData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to pull model');
    } finally {
      setPulling(false);
    }
  };

  const toggleModel = async (modelId) => {
    try {
      const model = models.find(m => m.model_id === modelId);
      await axios.put(`${API_URL}/api/v1/llm/models/${modelId}`, {
        is_active: !model.is_active
      }, axiosConfig);
      fetchAllData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to toggle model');
    }
  };

  const setDefault = async (modelId) => {
    try {
      await axios.put(`${API_URL}/api/v1/llm/models/${modelId}`, {
        is_default: true
      }, axiosConfig);
      fetchAllData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to set default');
    }
  };

  const deleteTemplate = async (id) => {
    if (!confirm('Delete this template?')) return;
    try {
      await axios.delete(`${API_URL}/api/v1/llm/templates/${id}`, axiosConfig);
      setSuccess('Template deleted');
      fetchAllData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete template');
    }
  };

  if (loading) return <div className="p-6 text-center">Loading LLM Manager...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/ai-chat')} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Cpu className="w-8 h-8 text-indigo-600" />
            LLM Manager
          </h1>
        </div>
      </div>

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <p className="text-sm text-green-700">{success}</p>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <MessageSquare className="w-5 h-5 text-indigo-600" />
            <p className="text-sm text-gray-500">Total Requests</p>
          </div>
          <p className="text-2xl font-bold">{usage?.total_requests?.toLocaleString() || 0}</p>
          <p className="text-xs text-gray-400 mt-1">Last 30 days</p>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <Database className="w-5 h-5 text-green-600" />
            <p className="text-sm text-gray-500">Total Tokens</p>
          </div>
          <p className="text-2xl font-bold">{usage?.total_tokens?.toLocaleString() || 0}</p>
          <p className="text-xs text-gray-400 mt-1">Prompt + Completion</p>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="w-5 h-5 text-amber-600" />
            <p className="text-sm text-gray-500">Avg Latency</p>
          </div>
          <p className="text-2xl font-bold">{usage?.avg_latency_ms?.toFixed(0) || 0}ms</p>
          <p className="text-xs text-gray-400 mt-1">Per request</p>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <Layers className="w-5 h-5 text-purple-600" />
            <p className="text-sm text-gray-500">Conversations</p>
          </div>
          <p className="text-2xl font-bold">{conversations?.total_conversations || 0}</p>
          <p className="text-xs text-gray-400 mt-1">{conversations?.total_messages || 0} messages</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'models', label: 'Models', icon: Cpu },
          { id: 'templates', label: 'Templates', icon: FileText },
          { id: 'usage', label: 'Usage Analytics', icon: BarChart3 },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); setError(null); setSuccess(null); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-all ${
              activeTab === tab.id ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Models Tab */}
      {activeTab === 'models' && (
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-600" />
              Configured Models
            </h2>
            <div className="space-y-3">
              {models.map(model => (
                <div key={model.id} className={`flex items-center justify-between p-4 rounded-lg border ${model.is_default ? 'border-indigo-200 bg-indigo-50/50' : 'border-gray-200'}`}>
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${model.is_available ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                      <Cpu className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{model.display_name}</h3>
                        {model.is_default && <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">Default</span>}
                        {model.is_available ? <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-medium">Available</span> : <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-medium">Not Pulled</span>}
                      </div>
                      <p className="text-sm text-gray-500">{model.model_id} • {model.provider} • {model.context_window?.toLocaleString()} context</p>
                      <p className="text-sm text-gray-400">{model.description}</p>
                      <div className="flex gap-2 mt-1">
                        {model.supports_streaming && <span className="text-xs text-gray-500 flex items-center gap-1"><Zap className="w-3 h-3" /> Streaming</span>}
                        {model.supports_tools && <span className="text-xs text-gray-500 flex items-center gap-1"><Settings className="w-3 h-3" /> Tools</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {!model.is_available && (
                      <button
                        onClick={() => pullModel(model.model_id)}
                        disabled={pulling}
                        className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1"
                      >
                        <Download className="w-4 h-4" />
                        {pulling ? 'Pulling...' : 'Pull'}
                      </button>
                    )}
                    {!model.is_default && model.is_active && (
                      <button onClick={() => setDefault(model.model_id)} className="px-3 py-1.5 text-sm text-indigo-600 hover:bg-indigo-50 rounded-lg">
                        Set Default
                      </button>
                    )}
                    <button onClick={() => toggleModel(model.model_id)} className="p-2 hover:bg-gray-100 rounded-lg">
                      {model.is_active ? <ToggleRight className="w-5 h-5 text-green-600" /> : <ToggleLeft className="w-5 h-5 text-gray-400" />}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-indigo-600" />
              Available from Ollama
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {availableModels.filter(am => !models.some(m => m.model_id === am.name)).map(am => (
                <div key={am.name} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{am.name}</p>
                    <p className="text-xs text-gray-500">{(am.size / 1024 / 1024 / 1024).toFixed(1)} GB</p>
                  </div>
                </div>
              ))}
              {availableModels.filter(am => !models.some(m => m.model_id === am.name)).length === 0 && (
                <p className="text-sm text-gray-500 col-span-full">All available models are configured</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600" />
              Prompt Templates
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map(t => (
                <div key={t.id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{t.display_name}</h3>
                      <p className="text-sm text-gray-500">{t.description}</p>
                      <span className="inline-block mt-2 px-2 py-0.5 bg-gray-200 text-gray-600 rounded text-xs capitalize">{t.category}</span>
                    </div>
                    <button onClick={() => deleteTemplate(t.id)} className="p-1.5 hover:bg-red-50 text-red-500 rounded">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="mt-3 p-2 bg-white rounded border border-gray-200 text-xs font-mono text-gray-600 line-clamp-3">
                    {t.system_prompt}
                  </div>
                </div>
              ))}
            </div>
            {templates.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No templates configured</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Usage Analytics Tab */}
      {activeTab === 'usage' && usage && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-600" />
                Usage by Model
              </h2>
              <div className="space-y-3">
                {usage.by_model?.map(m => (
                  <div key={m.model} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{m.model}</p>
                      <p className="text-sm text-gray-500">{m.requests} requests</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-gray-900">{m.tokens?.toLocaleString()} tokens</p>
                      <p className="text-sm text-gray-500">{m.avg_latency_ms?.toFixed(0)}ms avg</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
                Daily Usage
              </h2>
              <div className="space-y-2">
                {usage.by_day?.slice(-14).map(d => (
                  <div key={d.date} className="flex items-center gap-3">
                    <span className="text-sm text-gray-500 w-24">{d.date}</span>
                    <div className="flex-1 h-6 bg-gray-100 rounded overflow-hidden">
                      <div
                        className="h-full bg-indigo-500 rounded"
                        style={{ width: `${Math.min((d.tokens / (usage.total_tokens || 1)) * 100 * 7, 100)}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-700 w-20 text-right">{d.tokens?.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Endpoint Breakdown</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {usage.by_endpoint?.map(e => (
                <div key={e.endpoint} className="p-3 bg-gray-50 rounded-lg text-center">
                  <p className="text-sm text-gray-500 capitalize">{e.endpoint?.replace(/_/g, ' ')}</p>
                  <p className="text-xl font-bold text-gray-900">{e.requests}</p>
                  <p className="text-xs text-gray-400">{e.tokens?.toLocaleString()} tokens</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="card p-4">
              <p className="text-sm text-gray-500">Prompt Tokens</p>
              <p className="text-xl font-bold">{usage.prompt_tokens?.toLocaleString()}</p>
            </div>
            <div className="card p-4">
              <p className="text-sm text-gray-500">Completion Tokens</p>
              <p className="text-xl font-bold">{usage.completion_tokens?.toLocaleString()}</p>
            </div>
            <div className="card p-4">
              <p className="text-sm text-gray-500">Error Rate</p>
              <p className="text-xl font-bold">{usage.error_rate?.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

