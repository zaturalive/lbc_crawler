import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useEffect, useState } from 'react';
import { Zap, Search } from 'lucide-react';
import { getMyCredits } from '../api/client';

const ADMIN_USER_IDS = [1, 6];

export default function Header() {
  const { user, token, logout } = useAuth();
  const [credits, setCredits] = useState(null);

  useEffect(() => {
    if (!token) { setCredits(null); return; }
    getMyCredits(token)
      .then(setCredits)
      .catch(() => {});
  }, [token]);

  return (
    <header className="bg-fmc-surface border-b border-fmc-accent-deep/60 px-6 py-3 flex-shrink-0">
      <div className="flex items-center justify-between">
        <Link to="/" className="flex flex-col hover:opacity-80 transition-opacity">
          <h1 className="text-xl font-mono font-bold text-fmc-text tracking-tight">
            <span className="text-fmc-accent">▸</span> find_my_car
          </h1>
          <p className="text-xs text-fmc-text-dim font-mono mt-0.5">
            Powered by LeBonCoin
          </p>
        </Link>

        <nav className="flex items-center gap-3">
          <Link
            to="/history"
            className="text-xs font-mono text-fmc-text-dim hover:text-fmc-accent transition-colors"
          >
            Historique
          </Link>
          {ADMIN_USER_IDS.includes(user?.id) && (
            <Link
              to="/admin/ai"
              className="text-xs font-mono text-fmc-text-dim hover:text-purple-400 transition-colors"
              title="Administration IA"
            >
              ✨ Admin
            </Link>
          )}
          {user ? (
            <>
              {/* Solde crédits */}
              {credits && (
                <Link
                  to="/credits"
                  className="hidden sm:flex items-center gap-2 text-xs font-mono bg-fmc-bg border border-fmc-accent-deep/40 rounded px-2 py-1 hover:border-fmc-accent/60 transition-colors"
                  title="Mes crédits"
                >
                  <span className="flex items-center gap-1 text-fmc-accent">
                    <Zap size={11} />
                    {credits.analysis_credits}
                  </span>
                  <span className="text-fmc-accent-deep/60">|</span>
                  <span className="flex items-center gap-1 text-blue-400">
                    <Search size={11} />
                    {credits.daily_searches_free_remaining + credits.search_credits}
                  </span>
                </Link>
              )}
              <span className="text-xs font-mono text-fmc-text-dim hidden sm:block max-w-[140px] truncate">
                {user.email}
              </span>
              <Link
                to="/account"
                className="text-xs font-mono text-fmc-accent hover:text-fmc-glow underline underline-offset-2 transition-colors"
              >
                Mon compte
              </Link>
              <button
                onClick={logout}
                className="fmc-btn-ghost text-xs px-3 py-1.5"
              >
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="fmc-btn-ghost text-xs px-3 py-1.5">
                Connexion
              </Link>
              <Link to="/register" className="fmc-btn-primary text-xs px-3 py-1.5">
                Inscription
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
