import { Link } from 'react-router-dom';
import { XCircle } from 'lucide-react';
import Header from '../components/Header';

export default function PaymentCancel() {
  return (
    <div className="min-h-screen bg-fmc-bg flex flex-col">
      <Header />
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="bg-fmc-surface border border-red-500/40 rounded-xl p-8 max-w-md w-full text-center">
          <XCircle size={48} className="text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-mono font-bold text-fmc-text mb-2">Paiement annulé</h2>
          <p className="text-sm text-fmc-text-dim font-mono mb-6">
            Votre paiement a été annulé. Aucun montant n'a été prélevé.
          </p>
          <div className="flex gap-3 justify-center">
            <Link to="/credits" className="fmc-btn-primary text-sm px-4 py-2">
              Retour aux crédits
            </Link>
            <Link to="/" className="fmc-btn-ghost text-sm px-4 py-2">
              Accueil
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
