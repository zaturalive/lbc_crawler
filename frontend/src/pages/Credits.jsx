import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CreditCard, Zap, Search, CheckCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getMyCredits, getCreditPacks, createCheckout } from '../api/client';
import Header from '../components/Header';

const PACK_TYPE_LABELS = {
  analysis: { label: 'Analyses IA', icon: <Zap size={16} className="text-fmc-accent" />, color: 'fmc-accent' },
  search:   { label: 'Recherches',  icon: <Search size={16} className="text-blue-400" />,     color: 'blue-400' },
};

export default function Credits() {
  const { user, token } = useAuth();
  const navigate = useNavigate();

  const [credits, setCredits]     = useState(null);
  const [packs, setPacks]         = useState([]);
  const [loading, setLoading]     = useState(true);
  const [buying, setBuying]       = useState(null); // pack_id en cours d'achat
  const [error, setError]         = useState(null);

  useEffect(() => {
    if (!token) { navigate('/login'); return; }
    fetchData();
  }, [token]);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const [creditsData, packsData] = await Promise.all([
        getMyCredits(token),
        getCreditPacks(),
      ]);
      setCredits(creditsData);
      setPacks(Array.isArray(packsData) ? packsData : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleBuy(packId) {
    if (!token) { navigate('/login'); return; }
    setBuying(packId);
    setError(null);
    try {
      const { checkout_url } = await createCheckout(packId, token);
      window.location.href = checkout_url;
    } catch (err) {
      setError(err.message || 'Erreur lors de la création du paiement');
      setBuying(null);
    }
  }

  const analysisPacks = packs.filter(p => p.pack_type === 'analysis');
  const searchPacks   = packs.filter(p => p.pack_type === 'search');

  return (
    <div className="min-h-screen bg-fmc-bg flex flex-col">
      <Header />
      <main className="flex-1 p-6 max-w-4xl mx-auto w-full">
        <h2 className="text-2xl font-mono font-bold text-fmc-text mb-1">
          Mes crédits
        </h2>
        <p className="text-sm text-fmc-text-dim font-mono mb-6">
          Gérez votre solde de crédits et achetez des packs.
        </p>

        {loading && (
          <div className="flex items-center gap-2 text-fmc-text-dim font-mono text-sm">
            <Loader2 size={16} className="animate-spin" /> Chargement…
          </div>
        )}

        {error && (
          <div className="bg-red-900/30 border border-red-500/40 rounded p-3 text-red-400 text-sm font-mono mb-4">
            {error}
          </div>
        )}

        {/* Solde actuel */}
        {credits && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
            {/* Analyses IA */}
            <div className="bg-fmc-surface border border-fmc-accent-deep/40 rounded-lg p-5">
              <div className="flex items-center gap-2 mb-2">
                <Zap size={18} className="text-fmc-accent" />
                <span className="font-mono font-semibold text-fmc-text">Analyses IA</span>
              </div>
              <div className="text-3xl font-mono font-bold text-fmc-accent">
                {credits.analysis_credits}
              </div>
              <div className="text-xs text-fmc-text-dim font-mono mt-1">crédits disponibles</div>
            </div>

            {/* Recherches */}
            <div className="bg-fmc-surface border border-fmc-accent-deep/40 rounded-lg p-5">
              <div className="flex items-center gap-2 mb-2">
                <Search size={18} className="text-blue-400" />
                <span className="font-mono font-semibold text-fmc-text">Recherches</span>
              </div>
              <div className="text-3xl font-mono font-bold text-blue-400">
                {credits.daily_searches_free_remaining}
                <span className="text-lg text-fmc-text-dim">/{credits.daily_searches_free} gratuites</span>
              </div>
              <div className="text-xs text-fmc-text-dim font-mono mt-1">
                + {credits.search_credits} crédit{credits.search_credits !== 1 ? 's' : ''} payant{credits.search_credits !== 1 ? 's' : ''}
              </div>
              <div className="mt-2 text-xs text-fmc-text-dim font-mono">
                Résultats : {credits.daily_results_used}/{credits.daily_results_limit} aujourd'hui
              </div>
            </div>
          </div>
        )}

        {/* Packs Analyses IA */}
        {!loading && analysisPacks.length > 0 && (
          <section className="mb-8">
            <h3 className="text-lg font-mono font-semibold text-fmc-text mb-3 flex items-center gap-2">
              <Zap size={16} className="text-fmc-accent" /> Packs Analyses IA
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {analysisPacks.map(pack => (
                <PackCard key={pack.id} pack={pack} buying={buying} onBuy={handleBuy} />
              ))}
            </div>
          </section>
        )}

        {/* Packs Recherches */}
        {!loading && searchPacks.length > 0 && (
          <section className="mb-8">
            <h3 className="text-lg font-mono font-semibold text-fmc-text mb-3 flex items-center gap-2">
              <Search size={16} className="text-blue-400" /> Packs Recherches
            </h3>
            <p className="text-xs text-fmc-text-dim font-mono mb-3">
              3 recherches gratuites par jour incluses. Les crédits payants n'expirent jamais.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {searchPacks.map(pack => (
                <PackCard key={pack.id} pack={pack} buying={buying} onBuy={handleBuy} accentColor="blue" />
              ))}
            </div>
          </section>
        )}

        {/* Info sécurité */}
        <div className="bg-fmc-surface border border-fmc-accent-deep/20 rounded-lg p-4 text-xs text-fmc-text-dim font-mono flex items-start gap-3">
          <CreditCard size={16} className="flex-shrink-0 mt-0.5 text-fmc-accent-deep" />
          <div>
            <p className="font-semibold text-fmc-text mb-1">Paiement sécurisé par Stripe</p>
            <p>Vos données bancaires ne transitent jamais par nos serveurs. Paiement chiffré SSL/TLS. Les crédits achetés sont permanents et ne s'expirent pas.</p>
          </div>
        </div>
      </main>
    </div>
  );
}

function PackCard({ pack, buying, onBuy, accentColor = 'accent' }) {
  const isBuying = buying === pack.id;
  const pricePerUnit = (pack.price_cents / pack.credits / 100).toFixed(2);
  const accentClass = accentColor === 'blue' ? 'text-blue-400 border-blue-400/50' : 'text-fmc-accent border-fmc-accent/50';
  const btnClass = accentColor === 'blue'
    ? 'bg-blue-600 hover:bg-blue-500 text-white'
    : 'bg-fmc-accent hover:bg-fmc-glow text-fmc-bg';

  return (
    <div className="bg-fmc-surface border border-fmc-accent-deep/40 rounded-lg p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="font-mono font-semibold text-fmc-text text-sm">{pack.name}</span>
        {pack.credits >= 50 && (
          <span className="text-xs bg-fmc-accent/20 text-fmc-accent border border-fmc-accent/30 rounded px-2 py-0.5 font-mono">
            Meilleur prix
          </span>
        )}
      </div>
      <div className={`text-2xl font-mono font-bold ${accentClass.split(' ')[0]}`}>
        {pack.credits}
        <span className="text-sm text-fmc-text-dim ml-1">crédits</span>
      </div>
      <div className="text-xs text-fmc-text-dim font-mono">
        {pricePerUnit} €/crédit
      </div>
      <div className="text-xl font-mono font-bold text-fmc-text">
        {(pack.price_cents / 100).toFixed(2)} €
      </div>
      <button
        onClick={() => onBuy(pack.id)}
        disabled={!!buying}
        className={`w-full py-2 rounded font-mono font-semibold text-sm transition-colors flex items-center justify-center gap-2 ${btnClass} disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {isBuying ? (
          <><Loader2 size={14} className="animate-spin" /> Redirection…</>
        ) : (
          <><CreditCard size={14} /> Acheter</>
        )}
      </button>
    </div>
  );
}
