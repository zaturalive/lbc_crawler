import { useState, useEffect } from 'react';
import PatternSelector from './PatternSelector';
import Button from './ui/Button';
import Input from './ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/Select';
import { Save, Trash2, X as XIcon } from 'lucide-react';

const GEARBOX_OPTIONS = [
  { value: '__any__', label: 'Peu importe' },
  { value: 'manual', label: 'Manuelle' },
  { value: 'automatic', label: 'Automatique' },
];

const FUEL_OPTIONS = [
  { value: '__any__', label: 'Peu importe' },
  { value: 'essence', label: 'Essence' },
  { value: 'diesel', label: 'Diesel' },
  { value: 'hybride', label: 'Hybride' },
  { value: 'electrique', label: 'Électrique' },
  { value: 'gpl', label: 'GPL' },
];

const RADIUS_OPTIONS = [
  { value: '10', label: '10 km' },
  { value: '30', label: '30 km' },
  { value: '50', label: '50 km' },
  { value: '100', label: '100 km' },
];

const EMPTY_FORM = {
  brand: '', model: '', price_min: '', price_max: '',
  mileage_min: '', mileage_max: '', year_min: '',
  horsepower_min: '', horsepower_max: '', gearbox: '', fuel: '',
  city: '', radius: '30',
};

function loadPresets() {
  try { return JSON.parse(localStorage.getItem('fmc_presets') || '[]'); }
  catch { return []; }
}

export default function SearchForm({ onResults, onLoading, initialValues = null }) {
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [selectedPatterns, setSelectedPatterns] = useState([]);
  const [customRegex, setCustomRegex] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Presets
  const [presets, setPresets] = useState(loadPresets);
  const [showSaveForm, setShowSaveForm] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [selectedPresetId, setSelectedPresetId] = useState('');

  function set(key, val) { setForm(f => ({ ...f, [key]: val })); }

  useEffect(() => {
    if (!initialValues) return;
    const { selectedPatterns: sp, customRegex: cr, ...rest } = initialValues;
    setForm(prev => ({ ...EMPTY_FORM, ...rest }));
    if (sp) setSelectedPatterns(sp);
    if (cr) setCustomRegex(cr);
  }, [initialValues]);

  function handleReset() {
    setForm({ ...EMPTY_FORM });
    setSelectedPatterns([]);
    setCustomRegex('');
    setError('');
  }

  // ── Presets ───────────────────────────────────────
  function savePreset() {
    if (!presetName.trim()) return;
    const entry = {
      id: Date.now(),
      name: presetName.trim(),
      params: { ...form, selectedPatterns, customRegex },
    };
    const updated = [...presets, entry];
    setPresets(updated);
    localStorage.setItem('fmc_presets', JSON.stringify(updated));
    setPresetName('');
    setShowSaveForm(false);
  }

  function loadPreset(preset) {
    const { selectedPatterns: sp, customRegex: cr, ...rest } = preset.params;
    setForm({ ...EMPTY_FORM, ...rest });
    setSelectedPatterns(sp || []);
    setCustomRegex(cr || '');
  }

  function deletePreset(id) {
    const updated = presets.filter(p => p.id !== id);
    setPresets(updated);
    localStorage.setItem('fmc_presets', JSON.stringify(updated));
  }

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
        mileage_min: form.mileage_min ? Number(form.mileage_min) : null,
        mileage_max: form.mileage_max ? Number(form.mileage_max) : null,
        year_min: form.year_min ? Number(form.year_min) : null,
        horsepower_min: form.horsepower_min ? Number(form.horsepower_min) : null,
        horsepower_max: form.horsepower_max ? Number(form.horsepower_max) : null,
        gearbox: (form.gearbox && form.gearbox !== '__any__') ? form.gearbox : null,
        fuel: (form.fuel && form.fuel !== '__any__') ? form.fuel : null,
        city: form.city || null,
        radius: form.city ? Number(form.radius) : null,
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
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Marque</label>
          <Input
            value={form.brand}
            onChange={e => set('brand', e.target.value)}
            placeholder="ex: Peugeot"
          />
        </div>
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Modèle</label>
          <Input
            value={form.model}
            onChange={e => set('model', e.target.value)}
            placeholder="ex: 308"
          />
        </div>
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Boîte de vitesses</label>
          <Select value={form.gearbox} onValueChange={val => set('gearbox', val)}>
            <SelectTrigger>
              <SelectValue placeholder="Choisir une option" />
            </SelectTrigger>
            <SelectContent>
              {GEARBOX_OPTIONS.map(o => (
                <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Carburant</label>
          <Select value={form.fuel} onValueChange={val => set('fuel', val)}>
            <SelectTrigger>
              <SelectValue placeholder="Choisir une option" />
            </SelectTrigger>
            <SelectContent>
              {FUEL_OPTIONS.map(o => (
                <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Prix min (€)</label>
          <Input
            type="number"
            min="0"
            value={form.price_min}
            onChange={e => set('price_min', e.target.value)}
            placeholder="0"
          />
        </div>
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Prix max (€)</label>
          <Input
            type="number"
            min="0"
            value={form.price_max}
            onChange={e => set('price_max', e.target.value)}
            placeholder="15000"
          />
        </div>
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Kilométrage min</label>
          <Input
            type="number"
            min="0"
            value={form.mileage_min}
            onChange={e => set('mileage_min', e.target.value)}
            placeholder="50000"
          />
        </div>
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Kilométrage max</label>
          <Input
            type="number"
            min="0"
            value={form.mileage_max}
            onChange={e => set('mileage_max', e.target.value)}
            placeholder="150000"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Année min</label>
          <Input
            type="number"
            min="1990"
            max={new Date().getFullYear()}
            value={form.year_min}
            onChange={e => set('year_min', e.target.value)}
            placeholder="2010"
          />
        </div>
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Chevaux min</label>
          <Input
            type="number"
            min="0"
            value={form.horsepower_min}
            onChange={e => set('horsepower_min', e.target.value)}
            placeholder="70"
          />
        </div>
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Chevaux max</label>
          <Input
            type="number"
            min="0"
            value={form.horsepower_max}
            onChange={e => set('horsepower_max', e.target.value)}
            placeholder="150"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Ville</label>
          <Input
            value={form.city}
            onChange={e => set('city', e.target.value)}
            placeholder="ex: Paris, Lyon, Bordeaux..."
          />
        </div>
        <div className="space-y-2 min-w-0">
          <label className="text-sm font-semibold text-fmc-text">Rayon autour de la ville</label>
          <Select value={form.radius} onValueChange={val => set('radius', val)}>
            <SelectTrigger>
              <SelectValue placeholder="Rayon" />
            </SelectTrigger>
            <SelectContent>
              {RADIUS_OPTIONS.map(o => (
                <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <PatternSelector
        selected={selectedPatterns}
        onChange={setSelectedPatterns}
        customRegex={customRegex}
        onCustomRegexChange={setCustomRegex}
      />

      {error && (
        <div className="rounded-md bg-red-900/20 p-4">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      <Button type="submit" variant="primary" fullWidth size="lg" disabled={loading}>
        {loading ? 'Recherche en cours...' : 'Chercher'}
      </Button>

      {/* Bouton reset */}
      <button
        type="button"
        onClick={handleReset}
        className="w-full text-xs text-fmc-text-dim hover:text-fmc-text font-mono flex items-center justify-center gap-1 py-1 transition-colors"
      >
        <XIcon className="h-3 w-3" />
        Effacer tout
      </button>

      {/* ── Presets ────────────────────────────────────── */}
      <div className="pt-2 border-t border-fmc-accent-deep/40 space-y-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowSaveForm(v => !v)}
            className="fmc-btn-ghost text-xs py-1 px-2 flex items-center gap-1"
          >
            <Save className="h-3 w-3" />
            Sauvegarder
          </button>

          {presets.length > 0 && (
            <select
              className="fmc-input text-xs flex-1"
              style={{ height: '28px', paddingTop: '2px', paddingBottom: '2px' }}
              value={selectedPresetId}
              onChange={e => {
                const val = e.target.value;
                setSelectedPresetId(val);
                const preset = presets.find(p => p.id === Number(val));
                if (preset) {
                  loadPreset(preset);
                  setSelectedPresetId('');
                }
              }}
            >
              <option value="" disabled>Charger un preset…</option>
              {presets.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          )}
        </div>

        {/* Formulaire inline de sauvegarde */}
        {showSaveForm && (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={presetName}
              onChange={e => setPresetName(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); savePreset(); } }}
              placeholder="Nom du preset…"
              className="fmc-input text-xs flex-1"
              style={{ height: '28px' }}
              autoFocus
            />
            <button type="button" onClick={savePreset}
              className="fmc-btn-primary text-xs py-0.5 px-2">OK</button>
            <button type="button" onClick={() => { setShowSaveForm(false); setPresetName(''); }}
              className="fmc-btn-ghost text-xs py-0.5 px-2">✕</button>
          </div>
        )}

        {/* Liste des presets avec bouton supprimer */}
        {presets.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {presets.map(p => (
              <div key={p.id}
                className="flex items-center gap-0.5 bg-fmc-surface border border-fmc-accent-deep rounded px-1.5 py-0.5 font-mono text-xs"
              >
                <button
                  type="button"
                  onClick={() => loadPreset(p)}
                  className="text-fmc-text-muted hover:text-fmc-text transition-colors"
                  title={`Charger "${p.name}"`}
                >
                  {p.name}
                </button>
                <button
                  type="button"
                  onClick={() => deletePreset(p.id)}
                  className="ml-1 text-fmc-text-dim hover:text-red-400 transition-colors"
                  title="Supprimer"
                >
                  <Trash2 className="h-2.5 w-2.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </form>
  );
}
