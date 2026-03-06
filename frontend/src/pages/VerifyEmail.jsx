import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { verifyEmail } from '../api/client';

export default function VerifyEmail() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState(searchParams.get('token') || '');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await verifyEmail(token);
      if (data.access_token) {
        login(data.access_token, data.user || {});
        navigate('/');
      } else {
        setError('Vérification échouée, token invalide ou expiré.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-fmc-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-mono font-bold text-fmc-text tracking-tight">
            <span className="text-fmc-accent">▸</span> find_my_car
          </h1>
        </div>

        <div className="fmc-panel p-6 border-fmc-accent-deep">
          <h2 className="fmc-title text-sm mb-6 flex items-center gap-2">
            <span className="text-fmc-accent text-xs">◈</span>
            VERIFICATION EMAIL
          </h2>

          {error && (
            <div className="mb-4 px-3 py-2 bg-red-900/20 border border-red-700/40 rounded text-xs font-mono text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-fmc-text-dim mb-1">Token de vérification</label>
              <input
                type="text"
                value={token}
                onChange={e => setToken(e.target.value)}
                required
                className="fmc-input w-full font-mono"
                placeholder="Collez votre token ici"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="fmc-btn-primary w-full mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Vérification…' : 'Activer mon compte'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
