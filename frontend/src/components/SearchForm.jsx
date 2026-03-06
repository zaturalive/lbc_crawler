import { useState } from 'react';
import PatternSelector from './PatternSelector';
import './SearchForm.css';

const GEARBOX_OPTIONS = [
  { value: '', label: 'Peu importe' },
  { value: 'manual', label: 'Manuelle' },
  { value: 'automatic', label: 'Automatique' },
];

export default function SearchForm({ onResults, onLoading }) {
  const [form, setForm] = useState({
    brand: '', model: '', price_min: '', price_max: '',
    mileage_max: '', year_min: '', horsepower_min: '', horsepower_max: '', gearbox: '',
  });
  const [selectedPatterns, setSelectedPatterns] = useState([]);
  const [customRegex, setCustomRegex] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function set(key, val) { setForm(f => ({ ...f, [key]: val })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    onLoading(true);
    try {
      const { searchListings } = await import('../api/client');
      const payload = {
        brand: form.brand || null,
        model: form.model || null,
        price_min: form.price_min ? Number(form.price_min) : null,
        price_max: form.price_max ? Number(form.price_max) : null,
        mileage_max: form.mileage_max ? Number(form.mileage_max) : null,
        year_min: form.year_min ? Number(form.year_min) : null,
        horsepower_min: form.horsepower_min ? Number(form.horsepower_min) : null,
        horsepower_max: form.horsepower_max ? Number(form.horsepower_max) : null,
        gearbox: form.gearbox || null,
        pattern_ids: selectedPatterns,
        custom_regex: customRegex || null,
      };
      const result = await searchListings(payload);
      onResults(result);
    } catch (err) {
      setError(err.message || 'Une erreur est survenue. Réessayez.');
      onResults(null);
    } finally {
      setLoading(false);
      onLoading(false);
    }
  }

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      <div className="search-form__row">
        <div className="search-form__field">
          <label>Marque</label>
          <input value={form.brand} onChange={e => set('brand', e.target.value)} placeholder="ex: Peugeot" />
        </div>
        <div className="search-form__field">
          <label>Modèle</label>
          <input value={form.model} onChange={e => set('model', e.target.value)} placeholder="ex: 308" />
        </div>
      </div>
      <div className="search-form__row">
        <div className="search-form__field">
          <label>Prix min (€)</label>
          <input type="number" min="0" value={form.price_min} onChange={e => set('price_min', e.target.value)} placeholder="0" />
        </div>
        <div className="search-form__field">
          <label>Prix max (€)</label>
          <input type="number" min="0" value={form.price_max} onChange={e => set('price_max', e.target.value)} placeholder="15000" />
        </div>
      </div>
      <div className="search-form__row">
        <div className="search-form__field">
          <label>Kilométrage max</label>
          <input type="number" min="0" value={form.mileage_max} onChange={e => set('mileage_max', e.target.value)} placeholder="150000" />
        </div>
        <div className="search-form__field">
          <label>Année min</label>
          <input type="number" min="1990" max={new Date().getFullYear()} value={form.year_min} onChange={e => set('year_min', e.target.value)} placeholder="2010" />
        </div>
      </div>
      <div className="search-form__row">
        <div className="search-form__field">
          <label>Chevaux min</label>
          <input type="number" min="0" value={form.horsepower_min} onChange={e => set('horsepower_min', e.target.value)} placeholder="70" />
        </div>
        <div className="search-form__field">
          <label>Chevaux max</label>
          <input type="number" min="0" value={form.horsepower_max} onChange={e => set('horsepower_max', e.target.value)} placeholder="150" />
        </div>
        <div className="search-form__field">
          <label>Boîte de vitesses</label>
          <select value={form.gearbox} onChange={e => set('gearbox', e.target.value)}>
            {GEARBOX_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>
      <PatternSelector
        selected={selectedPatterns}
        onChange={setSelectedPatterns}
        customRegex={customRegex}
        onCustomRegexChange={setCustomRegex}
      />
      {error && <p className="search-form__error">{error}</p>}
      <button type="submit" className="search-form__submit" disabled={loading}>
        {loading ? 'Recherche en cours...' : 'Chercher'}
      </button>
    </form>
  );
}
