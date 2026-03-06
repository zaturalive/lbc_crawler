import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register } from '../api/client';

export default function Register() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [devToken, setDevToken] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError('Les mots de passe ne correspondent pas.');
      return;
    }
    setLoading(true);
    try {
      const data = await register(email, password);
      setDevToken(data.verification_token || data.token || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (devToken) {
    return (
      <div className="min-h-screen bg-fmc-bg flex items-center justify-center px-4">
        <div className="w-full max-w-sm">
          <div className="fmc-panel p-6 border-fmc-accent-deep">
            <h2 className="fmc-title text-sm mb-4 flex items-center gap-2">
              <span className="text-fmc-accent text-xs">◈</span>
              COMPTE CREE
            </h2>
            <p className="text-xs font-mono text-fmc-text-dim mb-3">
              Vérifiez votre email pour activer votre compte.
            </p>
            <div className="px-3 py-2 bg-fmc-accent/10 border border-fmc-accent-deep rounded font-mono text-xs text-fmc-accent break-all mb-4">
              Token de développement : {devToken}
            </div>
            <button
              onClick={() => navigate(`/verify-email?token=${devToken}`)}
              className="fmc-btn-primary w-full"
            >
              Vérifier maintenant
            </button>
          </div>
        </div>
      </div>
    );
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
            INSCRIPTION
          </h2>

          {error && (
            <div className="mb-4 px-3 py-2 bg-red-900/20 border border-red-700/40 rounded text-xs font-mono text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-fmc-text-dim mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="fmc-input w-full"
                placeholder="vous@exemple.fr"
                autoComplete="email"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-fmc-text-dim mb-1">Mot de passe</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="fmc-input w-full"
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-fmc-text-dim mb-1">Confirmer le mot de passe</label>
              <input
                type="password"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                required
                className="fmc-input w-full"
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="fmc-btn-primary w-full mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Création…' : 'Créer mon compte'}
            </button>
          </form>

          <p className="mt-4 text-center text-xs font-mono text-fmc-text-dim">
            Déjà un compte ?{' '}
            <Link to="/login" className="text-fmc-accent hover:text-fmc-glow underline underline-offset-2 transition-colors">
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
