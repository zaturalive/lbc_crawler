import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Header() {
  const { user, logout } = useAuth();

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
          {user ? (
            <>
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
