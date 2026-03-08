import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getMyCredits } from '../api/client';
import Header from '../components/Header';

export default function PaymentSuccess() {
  const { token } = useAuth();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const [credits, setCredits] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) { setLoading(false); return; }
    // Attendre quelques secondes que le webhook Stripe soit traité
    const timer = setTimeout(async () => {
      try {
        const data = await getMyCredits(token);
        setCredits(data);
      } catch (_) {}
      setLoading(false);
    }, 2500);
    return () => clearTimeout(timer);
  }, [token]);

  return (
    <div className="min-h-screen bg-fmc-bg flex flex-col">
      <Header />
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="bg-fmc-surface border border-green-500/40 rounded-xl p-8 max-w-md w-full text-center">
          <CheckCircle size={48} className="text-green-400 mx-auto mb-4" />
          <h2 className="text-xl font-mono font-bold text-fmc-text mb-2">Paiement confirmé !</h2>
          <p className="text-sm text-fmc-text-dim font-mono mb-6">
            Vos crédits ont été ajoutés à votre compte.
          </p>

          {loading ? (
            <div className="flex items-center justify-center gap-2 text-fmc-text-dim text-sm font-mono">
              <Loader2 size={14} className="animate-spin" /> Mise à jour du solde…
            </div>
          ) : credits ? (
            <div className="bg-fmc-bg rounded-lg p-4 mb-6 text-left font-mono text-sm">
              <div className="flex justify-between text-fmc-text">
                <span>Analyses IA</span>
                <span className="text-fmc-accent font-bold">{credits.analysis_credits} crédits</span>
              </div>
              <div className="flex justify-between text-fmc-text mt-2">
                <span>Recherches</span>
                <span className="text-blue-400 font-bold">{credits.search_credits} crédits</span>
              </div>
            </div>
          ) : null}

          <div className="flex gap-3 justify-center">
            <Link to="/" className="fmc-btn-primary text-sm px-4 py-2">
              Lancer une recherche
            </Link>
            <Link to="/credits" className="fmc-btn-ghost text-sm px-4 py-2">
              Mes crédits
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
