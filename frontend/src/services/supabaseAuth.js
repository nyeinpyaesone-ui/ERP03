const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || '';
const SESSION_KEY = 'erp03_supabase_session';

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
    const error = new Error(
      data.msg || data.message || data.error_description || 'Supabase authentication failed.'
    );
    error.status = response.status;
    error.code = data.error || data.code || data.error_code;
    throw error;
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
    throw new Error('This browser cannot store the Supabase session securely for this tab.');
  }
}

export function clearSupabaseSession() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    // Storage may be unavailable in privacy-restricted browser contexts.
  }
}

function readStoredSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return { raw, session: raw ? JSON.parse(raw) : null };
  } catch {
    clearSupabaseSession();
    return { raw: null, session: null };
  }
}

export function hasSupabaseSession() {
  const { session } = readStoredSession();
  return Boolean(session?.access_token || session?.refresh_token);
}

export async function getSupabaseAccessToken() {
  const { raw: sessionMarker, session } = readStoredSession();
  if (!session?.access_token || !session?.refresh_token) return null;
  if (Number(session.expires_at || 0) > Math.floor(Date.now() / 1000) + 60) {
    return session.access_token;
  }

  let refreshed;
  try {
    refreshed = await authRequest('token?grant_type=refresh_token', {
      refresh_token: session.refresh_token,
    });
  } catch (error) {
    const explicitlyRejected = [401, 403].includes(error.status)
      || (error.status === 400 && (
        error.code === 'invalid_grant'
        || /invalid.*refresh|refresh.*(expired|revoked|not found)/i.test(error.message)
      ));
    if (explicitlyRejected) {
      const current = readStoredSession().raw;
      if (current === sessionMarker) clearSupabaseSession();
      return null;
    }
    // Network, rate-limit, and provider failures are retryable; preserve state
    // and let the caller stop the request instead of selecting another identity.
    throw error;
  }

  const currentMarker = readStoredSession().raw;
  if (currentMarker !== sessionMarker) return null;
  saveSupabaseSession({
    ...refreshed,
    expires_at: refreshed.expires_at || Math.floor(Date.now() / 1000) + refreshed.expires_in,
  });
  return refreshed.access_token || null;
}

export async function signOutSupabase() {
  const token = await getSupabaseAccessToken();
  if (token && isSupabaseConfigured) {
    try {
      await fetch(`${SUPABASE_URL.replace(/\/$/, '')}/auth/v1/logout`, {
        method: 'POST',
        headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${token}` },
        signal: AbortSignal.timeout(2500),
      });
    } catch {
      // Local sign-out is authoritative; remote revocation is best effort.
    }
  }
  clearSupabaseSession();
}
