import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const form = new FormData(e.currentTarget);
      await login({
        business_code: form.get('business_code').trim(),
        email: form.get('email').trim(),
        password: form.get('password'),
      });
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'ဝင်ရောက်မှု မအောင်မြင်ပါ။ အချက်အလက်များကို ပြန်စစ်ဆေးပါ။');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-erp-background px-4 py-10 text-erp-foreground">
      <div className="w-full max-w-md">
        <header className="mb-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-erp-secondary text-erp-secondaryForeground">
            <svg aria-hidden="true" className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <p className="eyebrow mt-4">MYANMAR BUSINESS OPERATIONS</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-erp-foreground">ERP03 သို့ ဝင်ရောက်ရန်</h1>
          <p className="mt-2 text-sm text-erp-foregroundMuted">လုပ်ငန်းကုဒ်၊ အီးမေးလ်နှင့် စကားဝှက်ကို ဖြည့်သွင်းပါ။</p>
        </header>

        <section className="rounded-xl border border-erp-border bg-erp-surface p-6 shadow-sm sm:p-8" aria-label="Sign in">
          {error && (
            <div role="alert" aria-live="polite" className="mb-6 rounded-md border border-red-700 bg-red-50 p-4 text-sm text-red-900">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="business_code" className="mb-1 block text-sm font-medium text-erp-foreground">လုပ်ငန်းကုဒ် (Business Code)</label>
              <input
                id="business_code"
                name="business_code"
                type="text"
                autoComplete="organization"
                required
                placeholder="လုပ်ငန်းကုဒ်"
                className="w-full rounded-md border border-erp-border bg-erp-surface px-3 py-2.5 text-erp-foreground placeholder:text-erp-foregroundMuted focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-erp-primary"
              />
            </div>
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-medium text-erp-foreground">အီးမေးလ် (Email)</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="username"
                required
                placeholder="name@company.com"
                className="w-full rounded-md border border-erp-border bg-erp-surface px-3 py-2.5 text-erp-foreground placeholder:text-erp-foregroundMuted focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-erp-primary"
              />
            </div>
            <div>
              <label htmlFor="password" className="mb-1 block text-sm font-medium text-erp-foreground">စကားဝှက် (Password)</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="w-full rounded-md border border-erp-border bg-erp-surface px-3 py-2.5 text-erp-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-erp-primary"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center rounded-md bg-erp-primary px-4 py-3 text-sm font-semibold text-erp-primaryForeground transition-colors hover:bg-erp-secondary hover:text-erp-secondaryForeground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-erp-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'ဝင်ရောက်နေသည်…' : 'ဝင်ရောက်ရန်'}
            </button>
          </form>
        </section>

        <p className="mt-6 text-center text-sm text-erp-foregroundMuted">
          အကောင့်မရှိသေးပါသလား?{' '}
          <Link to="/register" className="font-semibold text-erp-primary underline-offset-4 hover:underline">
            အကောင့်ဖွင့်ရန်
          </Link>
        </p>
      </div>
    </main>
  );
}
