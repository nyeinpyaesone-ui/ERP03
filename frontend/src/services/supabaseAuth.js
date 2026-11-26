const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || '';
const SESSION_KEY = 'erp03_supabase_session';
let refreshInFlight = null;

export const isSupabaseConfigured = Boolean(SUPABASE_URL && SUPABASE_KEY);

async function authRequest(path, body) {
  if (!isSupabaseConfigured) {
    throw new Error('Supabase Auth is not configured for this environment.');
  }
  const response = await fetch(`${SUPABASE_URL.replace(/\/$/, '')}/auth/v1/${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: SUPABASE_KEY,
    },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.msg || data.message || data.error_description || 'Supabase authentication failed.');
  }
  return data;
}

export async function signInWithSupabase(email, password) {
  const session = await authRequest('token?grant_type=password', { email, password });
  if (!session.access_token || !session.refresh_token) {
    throw new Error('Supabase did not return a complete session.');
  }
  return {
    ...session,
    expires_at: session.expires_at || Math.floor(Date.now() / 1000) + session.expires_in,
  };
}

export function saveSupabaseSession(session) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch {
    throw new Error('This browser cannot store the Supabase session for this tab.');
  }
}

export function clearSupabaseSession() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    // Storage may be unavailable in privacy-restricted browser contexts.
  }
}

export async function getSupabaseAccessToken() {
  let session;
  try {
    session = JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null');
  } catch {
    clearSupabaseSession();
    return null;
  }
  if (!session?.access_token || !session?.refresh_token) return null;
  if (Number(session.expires_at || 0) > Math.floor(Date.now() / 1000) + 60) {
    return session.access_token;
  }
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const refreshed = await authRequest('token?grant_type=refresh_token', {
          refresh_token: session.refresh_token,
        });
        saveSupabaseSession({
          ...refreshed,
          expires_at: refreshed.expires_at || Math.floor(Date.now() / 1000) + refreshed.expires_in,
        });
        return refreshed.access_token;
      } catch {
        clearSupabaseSession();
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

export async function signOutSupabase() {
  const token = await getSupabaseAccessToken();
  if (token && isSupabaseConfigured) {
    try {
      await fetch(`${SUPABASE_URL.replace(/\/$/, '')}/auth/v1/logout`, {
        method: 'POST',
        headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${token}` },
      });
    } catch {
      // Local sign-out must still complete when the Auth service is unavailable.
    }
  }
  clearSupabaseSession();
}
