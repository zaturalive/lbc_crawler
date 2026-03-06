import { useState } from 'react';
import ResultsGrid from '../components/ResultsGrid';
import SearchForm from '../components/SearchForm';
import './Home.css';

export default function Home() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="home">
      <header className="home__header">
        <h1>find_my_car</h1>
        <p>Trouvez votre voiture idéale parmi des milliers d'annonces LeBonCoin</p>
      </header>
      <main className="home__main">
        <SearchForm onResults={setResults} onLoading={setLoading} />
        <ResultsGrid results={results} loading={loading} />
      </main>
    </div>
  );
}
