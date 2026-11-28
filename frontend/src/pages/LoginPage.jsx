import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import { isSupabaseConfigured, signInWithSupabase } from '../services/supabaseAuth';

export default function LoginPage() {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login, loginWithSupabase } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const form = new FormData(e.currentTarget);
      await login({
        business_code: form.get('business_code'),
        email: form.get('email'),
        password: form.get('password'),
      });
      navigate('/');
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSupabaseSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const form = new FormData(e.currentTarget);
      const session = await signInWithSupabase(form.get('email'), form.get('password'));
      await loginWithSupabase(session);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Supabase sign-in failed. Link your identity using ERP03 credentials first.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-10">
      <div className="w-full max-w-md px-6">
        <div className="mb-8 text-center">
          <h2 className="mt-4 text-2xl font-bold tracking-tight text-gray-900">Sign in to ERP03</h2>
          <p className="mt-2 text-sm text-gray-600">Use your existing ERP03 account or a linked Supabase identity.</p>
        </div>
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 space-y-8">
          {error && <div role="alert" className="p-4 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <h3 className="font-semibold text-gray-900">Existing ERP03 account</h3>
            <label className="block text-sm font-medium text-gray-700">Business Code
              <input name="business_code" type="text" required autoComplete="organization" className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md" />
            </label>
            <label className="block text-sm font-medium text-gray-700">Email
              <input name="email" type="email" required autoComplete="username" className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md" />
            </label>
            <label className="block text-sm font-medium text-gray-700">Password
              <input name="password" type="password" required autoComplete="current-password" className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md" />
            </label>
            <button type="submit" disabled={loading} className="w-full py-3 px-4 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50">
              {loading ? 'Signing in…' : 'Sign in with ERP03'}
            </button>
          </form>
          {isSupabaseConfigured && (
            <>
              <div className="border-t border-gray-200" />
              <form onSubmit={handleSupabaseSubmit} className="space-y-4">
                <h3 className="font-semibold text-gray-900">Linked Supabase identity</h3>
                <label className="block text-sm font-medium text-gray-700">Email
                  <input name="email" type="email" required autoComplete="username" className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md" />
                </label>
                <label className="block text-sm font-medium text-gray-700">Password
                  <input name="password" type="password" required autoComplete="current-password" className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md" />
                </label>
                <button type="submit" disabled={loading} className="w-full py-3 px-4 rounded-md text-sm font-medium text-gray-800 border border-gray-300 hover:bg-gray-50 disabled:opacity-50">
                  {loading ? 'Signing in…' : 'Sign in with Supabase'}
                </button>
              </form>
            </>
          )}
        </div>
        <p className="mt-6 text-center text-sm text-gray-600">New business? <Link to="/register" className="font-medium text-blue-600">Create an account</Link></p>
      </div>
    </div>
  );
}
