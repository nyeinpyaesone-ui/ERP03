import React, { useState, useEffect } from 'react';
import {
  Shield, Users, Key, Lock, Eye, EyeOff, FileText, ChevronDown, ChevronUp,
  Plus, Trash2, Save, CheckCircle, AlertTriangle, Search, Filter,
  ToggleLeft, ToggleRight, Settings, UserCheck, Database, ArrowRight
} from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const resources = [
  'contacts', 'companies', 'deals', 'products', 'employees', 'departments',
  'invoices', 'projects', 'tasks', 'reports', 'workflows', 'settings', 'users', 'bulk', 'migrations'
];

const actions = ['read', 'create', 'update', 'delete'];
const accessLevels = [
  { value: 'read', label: 'Read Only', color: 'text-blue-600', bg: 'bg-blue-50' },
  { value: 'write', label: 'Read & Write', color: 'text-green-600', bg: 'bg-green-50' },
  { value: 'hidden', label: 'Hidden', color: 'text-red-600', bg: 'bg-red-50' },
];

export default function PermissionsManager() {
  const [activeTab, setActiveTab] = useState('roles');
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [fieldPermissions, setFieldPermissions] = useState([]);
  const [dataPolicies, setDataPolicies] = useState([]);
  const [users, setUsers] = useState([]);
  const [myPerms, setMyPerms] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form states
  const [newRole, setNewRole] = useState({ name: '', display_name: '', description: '' });
  const [selectedRole, setSelectedRole] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [rolePermissions, setRolePermissions] = useState([]);
  const [userRoles, setUserRoles] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [rolesRes, permsRes, fpRes, dpRes, myRes] = await Promise.all([
        axios.get(`${API_URL}/api/v1/permissions/roles`, axiosConfig),
        axios.get(`${API_URL}/api/v1/permissions/permissions`, axiosConfig),
        axios.get(`${API_URL}/api/v1/permissions/field-permissions`, axiosConfig),
        axios.get(`${API_URL}/api/v1/permissions/data-policies`, axiosConfig),
        axios.get(`${API_URL}/api/v1/permissions/me`, axiosConfig),
      ]);
      setRoles(rolesRes.data);
      setPermissions(permsRes.data);
      setFieldPermissions(fpRes.data);
      setDataPolicies(dpRes.data);
      setMyPerms(myRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load permissions data');
    } finally {
      setLoading(false);
    }
  };

  const createRole = async () => {
    if (!newRole.name || !newRole.display_name) return;
    try {
      await axios.post(`${API_URL}/api/v1/permissions/roles`, newRole, axiosConfig);
      setNewRole({ name: '', display_name: '', description: '' });
      setSuccess('Role created successfully');
      fetchAllData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create role');
    }
  };

  const deleteRole = async (id) => {
    if (!confirm('Delete this role?')) return;
    try {
      await axios.delete(`${API_URL}/api/v1/permissions/roles/${id}`, axiosConfig);
      setSuccess('Role deleted');
      fetchAllData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete role');
    }
  };

  const togglePolicy = async (id) => {
    try {
      await axios.put(`${API_URL}/api/v1/permissions/data-policies/${id}/toggle`, {}, axiosConfig);
      fetchAllData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to toggle policy');
    }
  };

  const deletePolicy = async (id) => {
    if (!confirm('Delete this policy?')) return;
    try {
      await axios.delete(`${API_URL}/api/v1/permissions/data-policies/${id}`, axiosConfig);
      setSuccess('Policy deleted');
      fetchAllData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete policy');
    }
  };

  const assignPermissionsToRole = async (roleId, permIds) => {
    try {
      await axios.post(`${API_URL}/api/v1/permissions/roles/${roleId}/permissions`, { permission_ids: permIds }, axiosConfig);
      setSuccess('Permissions updated');
      fetchAllData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to assign permissions');
    }
  };

  if (loading) return <div className="p-6 text-center">Loading permissions...</div>;
  if (error) return <div className="p-6 text-center text-red-600">{error}</div>;
  if (!myPerms?.is_admin) return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="card p-8 text-center">
        <Shield className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900">Access Denied</h2>
        <p className="text-gray-500 mt-2">You need admin privileges to manage permissions.</p>
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Shield className="w-8 h-8 text-indigo-600" />
          Permissions & RBAC
        </h1>
        <p className="text-gray-600 mt-2">Manage roles, permissions, field-level access, and data policies</p>
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

      {/* My Permissions Card */}
      <div className="card p-5 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <UserCheck className="w-5 h-5 text-indigo-600" />
          Your Access Level
        </h2>
        <div className="flex flex-wrap gap-2">
          {myPerms?.roles?.map(role => (
            <span key={role} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium capitalize">
              {role}
            </span>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-2">{myPerms?.permissions?.length || 0} permissions granted</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'roles', label: 'Roles', icon: Users },
          { id: 'permissions', label: 'Permissions', icon: Key },
          { id: 'fields', label: 'Field Access', icon: Eye },
          { id: 'policies', label: 'Data Policies', icon: Database },
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

      {/* Roles Tab */}
      {activeTab === 'roles' && (
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Plus className="w-5 h-5 text-indigo-600" />
              Create New Role
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <input
                type="text"
                value={newRole.name}
                onChange={e => setNewRole({...newRole, name: e.target.value})}
                placeholder="Role key (e.g., sales_manager)"
                className="input-field"
              />
              <input
                type="text"
                value={newRole.display_name}
                onChange={e => setNewRole({...newRole, display_name: e.target.value})}
                placeholder="Display name"
                className="input-field"
              />
              <input
                type="text"
                value={newRole.description}
                onChange={e => setNewRole({...newRole, description: e.target.value})}
                placeholder="Description"
                className="input-field"
              />
            </div>
            <button onClick={createRole} className="mt-3 btn-primary flex items-center gap-2">
              <Save className="w-4 h-4" /> Create Role
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {roles.map(role => (
              <div key={role.id} className={`card p-5 ${role.is_system ? 'border-indigo-200' : ''}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{role.display_name}</h3>
                    <p className="text-sm text-gray-500 font-mono">{role.name}</p>
                  </div>
                  {role.is_system && (
                    <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">System</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-2">{role.description}</p>
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-1">{role.permissions?.length || 0} permissions</p>
                  <div className="flex flex-wrap gap-1">
                    {(role.permissions || []).slice(0, 5).map(p => (
                      <span key={p.id} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                        {p.resource}.{p.action}
                      </span>
                    ))}
                    {(role.permissions || []).length > 5 && (
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">+{(role.permissions || []).length - 5} more</span>
                    )}
                  </div>
                </div>
                {!role.is_system && (
                  <button
                    onClick={() => deleteRole(role.id)}
                    className="mt-3 flex items-center gap-1 text-sm text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" /> Delete
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Permissions Matrix Tab */}
      {activeTab === 'permissions' && (
        <div className="card overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Key className="w-5 h-5 text-indigo-600" />
              Permission Matrix
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Resource</th>
                  <th className="px-4 py-3 text-left font-medium">Action</th>
                  <th className="px-4 py-3 text-left font-medium">Permission Name</th>
                  <th className="px-4 py-3 text-left font-medium">Roles</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {permissions.map(p => {
                  const rolesWithPerm = roles.filter(r => r.permissions?.some(rp => rp.id === p.id));
                  return (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 capitalize text-gray-900">{p.resource}</td>
                      <td className="px-4 py-3 capitalize text-gray-600">{p.action}</td>
                      <td className="px-4 py-3 font-mono text-indigo-600">{p.name}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {rolesWithPerm.map(r => (
                            <span key={r.id} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">{r.display_name}</span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Field Permissions Tab */}
      {activeTab === 'fields' && (
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Eye className="w-5 h-5 text-indigo-600" />
              Field-Level Access Control
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Control which fields are visible or editable for each role. Hidden fields are completely masked from the user.
            </p>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Role</th>
                    <th className="px-4 py-3 text-left font-medium">Resource</th>
                    <th className="px-4 py-3 text-left font-medium">Field</th>
                    <th className="px-4 py-3 text-left font-medium">Access</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {fieldPermissions.map(fp => {
                    const level = accessLevels.find(l => l.value === fp.access_level) || accessLevels[0];
                    return (
                      <tr key={fp.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium">{roles.find(r => r.id === fp.role_id)?.display_name || fp.role_id}</td>
                        <td className="px-4 py-3 capitalize text-gray-600">{fp.resource}</td>
                        <td className="px-4 py-3 font-mono text-gray-900">{fp.field_name}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${level.bg} ${level.color}`}>
                            {level.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {fieldPermissions.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <EyeOff className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No field permissions configured yet</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Data Policies Tab */}
      {activeTab === 'policies' && (
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-600" />
              Data Policies (Row-Level Access)
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Define row-level access rules. Policies determine which records a role can see based on conditions.
            </p>
            <div className="space-y-3">
              {dataPolicies.map(policy => (
                <div key={policy.id} className={`p-4 rounded-lg border ${policy.is_active ? 'bg-white border-gray-200' : 'bg-gray-50 border-gray-100'}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold text-gray-900">{policy.name}</h3>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${policy.effect === 'allow' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {policy.effect}
                        </span>
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs capitalize">{policy.resource}</span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        Role: {roles.find(r => r.id === policy.role_id)?.display_name || policy.role_id} • Priority: {policy.priority}
                      </p>
                      {policy.condition && (
                        <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono text-gray-600">
                          {JSON.stringify(policy.condition, null, 2)}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={() => togglePolicy(policy.id)} className="p-2 hover:bg-gray-100 rounded-lg">
                        {policy.is_active ? <ToggleRight className="w-5 h-5 text-green-600" /> : <ToggleLeft className="w-5 h-5 text-gray-400" />}
                      </button>
                      <button onClick={() => deletePolicy(policy.id)} className="p-2 hover:bg-red-50 text-red-500 rounded-lg">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              {dataPolicies.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Database className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No data policies configured yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

