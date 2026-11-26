import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function VerificationPending({ retry }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-3 bg-gray-50">
      <p role="alert">Unable to verify your session. Protected content remains hidden.</p>
      <button type="button" onClick={retry} className="rounded bg-blue-600 px-4 py-2 text-white">
        Retry verification
      </button>
    </div>
  );
}

function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
    </div>
  );
}

export function ProtectedRoute() {
  const { isAuthenticated, loading, probeError, refreshUser } = useAuth();
  const location = useLocation();

  if (loading) return <Loading />;
  if (probeError) return <VerificationPending retry={refreshUser} />;
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <Outlet />;
}

export function GuestRoute() {
  const { isAuthenticated, loading, probeError, refreshUser } = useAuth();
  if (loading) return <Loading />;
  if (probeError) return <VerificationPending retry={refreshUser} />;
  if (isAuthenticated) return <Navigate to="/" replace />;
  return <Outlet />;
}
