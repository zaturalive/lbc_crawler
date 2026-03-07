import { useState, useEffect, useCallback } from 'react';
import VehicleScore from './VehicleScore';
import Badge from './ui/Badge';
import { Card, CardContent } from './ui/Card';
import { ExternalLink, MapPin, Gauge, Calendar, Zap, Fuel, Heart, DoorOpen, Users, Palette, Settings2, ChevronLeft, ChevronRight, X } from 'lucide-react';

function ImageCarousel({ images, title, onClose }) {
  const [idx, setIdx] = useState(0);

  const prev = useCallback(() => setIdx(i => (i - 1 + images.length) % images.length), [images.length]);
  const next = useCallback(() => setIdx(i => (i + 1) % images.length), [images.length]);

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'ArrowLeft')  prev();
      if (e.key === 'ArrowRight') next();
      if (e.key === 'Escape')     onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [prev, next, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Header */}
      <div className="w-full max-w-4xl flex items-center justify-between mb-3" onClick={e => e.stopPropagation()}>
        <span className="text-white/70 font-mono text-sm truncate max-w-xs">{title}</span>
        <div className="flex items-center gap-3">
          <span className="text-white/50 font-mono text-xs">{idx + 1} / {images.length}</span>
          <button
            onClick={onClose}
            className="text-white/60 hover:text-red-400 transition-colors p-1 rounded"
            aria-label="Fermer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Image + arrows */}
      <div
        className="relative w-full max-w-4xl flex items-center justify-center"
        onClick={e => e.stopPropagation()}
      >
        {images.length > 1 && (
          <button
            onClick={prev}
            className="absolute left-0 z-10 p-2 bg-black/60 hover:bg-fmc-accent-deep/80 text-white rounded-r-lg transition-colors"
            aria-label="Image précédente"
          >
            <ChevronLeft className="h-7 w-7" />
          </button>
        )}

        <img
          src={images[idx]}
          alt={`${title} — photo ${idx + 1}`}
          className="max-h-[70vh] max-w-full object-contain rounded-lg shadow-2xl"
          onClick={() => window.open(images[idx], '_blank')}
          style={{ cursor: 'zoom-in' }}
        />

        {images.length > 1 && (
          <button
            onClick={next}
            className="absolute right-0 z-10 p-2 bg-black/60 hover:bg-fmc-accent-deep/80 text-white rounded-l-lg transition-colors"
            aria-label="Image suivante"
          >
            <ChevronRight className="h-7 w-7" />
          </button>
        )}
      </div>

      {/* Thumbnails strip */}
      {images.length > 1 && (
        <div
          className="flex gap-2 mt-4 overflow-x-auto max-w-4xl pb-1"
          onClick={e => e.stopPropagation()}
        >
          {images.map((img, i) => (
            <img
              key={i}
              src={img}
              alt={`Miniature ${i + 1}`}
              onClick={() => setIdx(i)}
              className={`h-14 w-20 object-cover rounded cursor-pointer flex-shrink-0 transition-all duration-150 ${
                i === idx ? 'ring-2 ring-fmc-accent opacity-100' : 'opacity-50 hover:opacity-80'
              }`}
            />
          ))}
        </div>
      )}

      <p className="text-white/30 font-mono text-xs mt-3">← → pour naviguer · clic image = plein écran · Échap pour fermer</p>
    </div>
  );
}

function formatMileage(km) {
  if (!km) return null;
  return new Intl.NumberFormat('fr-FR').format(km) + ' km';
}

const KEYWORD_VARIANTS = {
  'CT valide':           'success',
  'Carte grise':         'blue',
  'Premier propriétaire':'purple',
};

export default function ListingCard({ listing, onOpenModal, isLiked = false, onToggleLike, aiMode = false, aiAnalysis = null, isAnalyzing = false, isViewed = false, hasAiAnalysis = false }) {
  const { title, price, year, mileage, location, url, matched_keywords, vehicle, gearbox, horsepower, fuel_type, doors, seats, color } = listing;
  const [galleryOpen, setGalleryOpen] = useState(false);

  // Badge IA en mode IA
  const aiBadge = (() => {
    if (!aiMode) return null;
    if (isAnalyzing) return { icon: '⏳', bg: 'bg-purple-900/80', text: 'text-purple-200', label: 'Analyse…' };
    if (!aiAnalysis?.reponse) return { icon: '○', bg: 'bg-zinc-900/70', text: 'text-zinc-400', label: null };
    const r = aiAnalysis.reponse.risk_level;
    if (r === 'low')    return { icon: '✅', bg: 'bg-green-900/80',  text: 'text-green-200',  label: 'OK' };
    if (r === 'high')   return { icon: '⚠️', bg: 'bg-red-900/80',    text: 'text-red-200',    label: 'Risqué' };
    return                     { icon: '⚡', bg: 'bg-yellow-900/80', text: 'text-yellow-200', label: 'Moyen' };
  })();

  return (
    <>
    <Card
      className={`group animate-fade-in relative ${aiMode ? 'ai-mode-card' : ''} ${isAnalyzing ? 'ring-2 ring-purple-500/60 ring-offset-1 ring-offset-transparent' : ''}`}
      onClick={() => onOpenModal && onOpenModal(listing)}
    >
      <CardContent className="space-y-3">

        {/* Thumbnail image */}
        {listing.images && listing.images.length > 0 && (
          <div className="relative -mx-4 -mt-4 mb-3 overflow-hidden rounded-t-lg" style={{height: '140px'}}>
            <img
              src={listing.images[0]}
              alt={listing.title}
              className="w-full h-full object-cover cursor-pointer hover:scale-105 transition-transform duration-300"
              onClick={e => { e.stopPropagation(); setGalleryOpen(true); }}
              onError={e => { e.currentTarget.parentElement.style.display = 'none'; }}
            />
            {listing.images.length > 1 && (
              <span className="absolute bottom-2 right-2 bg-black/70 text-white text-xs font-mono px-1.5 py-0.5 rounded">
                +{listing.images.length - 1}
              </span>
            )}
            {/* Badge IA sur le thumbnail (mode IA uniquement) */}
            {aiBadge && (
              <span className={`absolute top-2 left-2 flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-mono ${aiBadge.bg} ${aiBadge.text} backdrop-blur-sm`}>
                <span>{aiBadge.icon}</span>
                {aiBadge.label && <span>{aiBadge.label}</span>}
              </span>
            )}
            <button
              className="absolute inset-0 w-full h-full opacity-0 hover:opacity-100 bg-black/30 flex items-center justify-center transition-opacity duration-200"
              onClick={e => { e.stopPropagation(); setGalleryOpen(true); }}
              aria-label="Voir toutes les photos"
            >
              <span className="text-white font-mono text-sm bg-black/60 px-3 py-1 rounded">📷 Voir photos</span>
            </button>
          </div>
        )}

        {/* Title + Price + Badges + Like */}
        <div className="flex items-start justify-between gap-2 min-w-0">
          <div className="space-y-1 min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-fmc-text group-hover:text-fmc-glow transition-colors line-clamp-2 font-mono leading-snug">
              {title || 'Annonce sans titre'}
            </h3>
            {price && (
              <p className="text-xl font-bold text-fmc-accent font-mono">
                {new Intl.NumberFormat('fr-FR').format(price)}&nbsp;€
              </p>
            )}
            {/* Badges statut */}
            {(isViewed || hasAiAnalysis) && (
              <div className="flex items-center gap-1.5 flex-wrap">
                {isViewed && (
                  <span
                    title="Annonce déjà consultée"
                    className="flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-mono bg-zinc-800/70 text-zinc-400 border border-zinc-700/50"
                  >
                    👁 Vue
                  </span>
                )}
                {hasAiAnalysis && (
                  <span
                    title="Analyse IA disponible"
                    className="flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-mono bg-purple-900/50 text-purple-300 border border-purple-700/50"
                  >
                    ✨ IA
                  </span>
                )}
              </div>
            )}
          </div>
          <button
            type="button"
            aria-label={isLiked ? 'Retirer des favoris' : 'Ajouter aux favoris'}
            onClick={e => {
              e.stopPropagation();
              onToggleLike && onToggleLike(listing.id);
            }}
            className={`flex-shrink-0 p-1.5 rounded-md border transition-all duration-200 ${
              isLiked
                ? 'border-red-500/70 text-red-400 bg-red-900/20'
                : 'border-fmc-accent-deep text-fmc-text-dim hover:border-red-500/70 hover:text-red-400 hover:bg-red-900/10'
            }`}
          >
            <Heart className={`h-3.5 w-3.5 ${isLiked ? 'fill-current' : ''}`} />
          </button>
        </div>

        {/* Meta row */}
        <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-fmc-text-dim font-mono">
          {year      && <span className="flex items-center gap-1"><Calendar  className="h-3 w-3 text-fmc-accent-deep" />{year}</span>}
          {mileage   && <span className="flex items-center gap-1"><Gauge     className="h-3 w-3 text-fmc-accent-deep" />{formatMileage(mileage)}</span>}
          {horsepower && <span className="flex items-center gap-1"><Zap      className="h-3 w-3 text-fmc-accent-deep" />{horsepower} ch</span>}
          {fuel_type  && <span className="flex items-center gap-1"><Fuel     className="h-3 w-3 text-fmc-accent-deep" /><span className="capitalize">{fuel_type}</span></span>}
          {gearbox    && <span className="flex items-center gap-1"><Settings2 className="h-3 w-3 text-fmc-accent-deep" />{gearbox === 'manual' ? 'Manuelle' : 'Auto'}</span>}
          {doors > 0  && <span className="flex items-center gap-1"><DoorOpen className="h-3 w-3 text-fmc-accent-deep" />{doors} portes</span>}
          {seats > 0  && <span className="flex items-center gap-1"><Users    className="h-3 w-3 text-fmc-accent-deep" />{seats} places</span>}
          {color      && <span className="flex items-center gap-1"><Palette  className="h-3 w-3 text-fmc-accent-deep" /><span className="capitalize">{color}</span></span>}
          {location   && <span className="flex items-center gap-1"><MapPin   className="h-3 w-3 text-fmc-accent-deep" />{location}</span>}
        </div>

        {/* Keywords */}
        {matched_keywords && matched_keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {matched_keywords.map(kw => (
              <Badge key={kw} variant={KEYWORD_VARIANTS[kw] || 'accent'}>
                {kw}
              </Badge>
            ))}
          </div>
        )}

        {/* Score */}
        <div className="fmc-divider pt-3">
          <VehicleScore vehicle={vehicle} />
        </div>

        {/* Mini résultat IA */}
        {aiAnalysis?.reponse && (
          <div className={`mt-2 p-2 rounded border text-xs font-mono space-y-1 ${
            aiAnalysis.reponse.risk_level === 'low'
              ? 'bg-green-950/40 border-green-700/40 text-green-300'
              : aiAnalysis.reponse.risk_level === 'high'
              ? 'bg-red-950/40 border-red-700/40 text-red-300'
              : 'bg-yellow-950/40 border-yellow-700/40 text-yellow-300'
          }`}>
            <div className="flex items-center gap-2">
              <span>{aiAnalysis.reponse.risk_level === 'low' ? '✅' : aiAnalysis.reponse.risk_level === 'high' ? '⚠️' : '⚡'}</span>
              <span className="font-semibold">
                {aiAnalysis.reponse.risk_level === 'low' ? 'Bon état' : aiAnalysis.reponse.risk_level === 'high' ? 'Risque élevé' : 'Attention'}
              </span>
              {aiAnalysis.cached && <span className="ml-auto text-cyan-400 text-[10px]">⚡ cache</span>}
            </div>
            {aiAnalysis.reponse.condition_summary && (
              <p className="text-[11px] leading-relaxed opacity-80 line-clamp-3">{aiAnalysis.reponse.condition_summary}</p>
            )}
            {aiAnalysis.reponse.upcoming_maintenance?.length > 0 && (
              <div className="text-[10px] opacity-70">
                🔧 {aiAnalysis.reponse.upcoming_maintenance.slice(0, 2).join(' · ')}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-1">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            className="flex-1 fmc-btn-primary text-center text-xs py-1.5 flex items-center justify-center gap-1.5"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Voir l'annonce
          </a>
          <button
            onClick={() => onOpenModal && onOpenModal(listing)}
            className="fmc-btn-ghost text-xs py-1.5 px-3 font-mono"
          >
            Détails
          </button>
        </div>

      </CardContent>
    </Card>

    {/* Image carousel */}
    {galleryOpen && listing.images?.length > 0 && (
      <ImageCarousel
        images={listing.images}
        title={listing.title}
        onClose={() => setGalleryOpen(false)}
      />
    )}
    </>
  );
}
