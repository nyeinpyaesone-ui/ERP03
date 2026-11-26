import { useState } from 'react';
import { api } from '../services/api';
import { isSupabaseConfigured, saveSupabaseSession, signInWithSupabase } from '../services/supabaseAuth';

export default function SupabaseIdentityPage() {
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLink = async (event) => {
    event.preventDefault();
    const formNode = event.currentTarget;
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const form = new FormData(formNode);
      const session = await signInWithSupabase(form.get('email'), form.get('password'));
      await api.linkSupabase(session.access_token);
      saveSupabaseSession(session);
      setMessage('Supabase identity linked. New API requests can now use this verified identity.');
      formNode.reset();
    } catch (err) {
      setError(err.message || 'Unable to link Supabase identity.');
    } finally {
      setLoading(false);
    }
  };

  if (!isSupabaseConfigured) {
    return <section className="max-w-xl rounded-lg border bg-white p-6"><h1 className="text-xl font-semibold">Supabase identity</h1><p className="mt-2 text-sm text-gray-600">Supabase Auth is not configured for this frontend environment.</p></section>;
  }

  return (
    <section className="max-w-xl rounded-lg border bg-white p-6">
      <h1 className="text-xl font-semibold">Connect Supabase identity</h1>
      <p className="mt-2 text-sm text-gray-600">First sign in with your existing ERP03 account. Then authenticate with a Supabase user whose email is verified and matches your ERP03 account email. This does not create or change ERP roles, business membership, or branch permissions.</p>
      {error && <p role="alert" className="mt-4 rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {message && <p role="status" className="mt-4 rounded bg-green-50 p-3 text-sm text-green-700">{message}</p>}
      <form onSubmit={handleLink} className="mt-6 space-y-4">
        <label className="block text-sm font-medium">Supabase email
          <input name="email" type="email" autoComplete="username" required className="mt-1 w-full rounded border px-3 py-2" />
        </label>
        <label className="block text-sm font-medium">Supabase password
          <input name="password" type="password" autoComplete="current-password" required className="mt-1 w-full rounded border px-3 py-2" />
        </label>
        <button type="submit" disabled={loading} className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50">{loading ? 'Connecting…' : 'Verify and link identity'}</button>
      </form>
    </section>
  );
}
