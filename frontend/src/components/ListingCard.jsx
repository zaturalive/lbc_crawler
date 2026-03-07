import { useState } from 'react';
import VehicleScore from './VehicleScore';
import Badge from './ui/Badge';
import { Card, CardContent } from './ui/Card';
import { ExternalLink, MapPin, Gauge, Calendar, Zap, Fuel, Heart, DoorOpen, Users, Palette, Settings2 } from 'lucide-react';

function formatMileage(km) {
  if (!km) return null;
  return new Intl.NumberFormat('fr-FR').format(km) + ' km';
}

const KEYWORD_VARIANTS = {
  'CT valide':           'success',
  'Carte grise':         'blue',
  'Premier propriétaire':'purple',
};

export default function ListingCard({ listing, onOpenModal, isLiked = false, onToggleLike, aiMode = false }) {
  const { title, price, year, mileage, location, url, matched_keywords, vehicle, gearbox, horsepower, fuel_type, doors, seats, color } = listing;
  const [galleryOpen, setGalleryOpen] = useState(false);

  return (
    <>
    <Card
      className={`group animate-fade-in relative ${aiMode ? 'ai-mode-card' : ''}`}
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
            <button
              className="absolute inset-0 w-full h-full opacity-0 hover:opacity-100 bg-black/30 flex items-center justify-center transition-opacity duration-200"
              onClick={e => { e.stopPropagation(); setGalleryOpen(true); }}
              aria-label="Voir toutes les photos"
            >
              <span className="text-white font-mono text-sm bg-black/60 px-3 py-1 rounded">📷 Voir photos</span>
            </button>
          </div>
        )}

        {/* Bouton like — positionné en haut à droite */}
        <button
          type="button"
          aria-label={isLiked ? 'Retirer des favoris' : 'Ajouter aux favoris'}
          onClick={e => {
            e.stopPropagation();
            onToggleLike && onToggleLike(listing.id);
          }}
          className={`absolute top-3 right-3 p-1.5 rounded-md border transition-all duration-200 ${
            isLiked
              ? 'border-red-500/70 text-red-400 bg-red-900/20'
              : 'border-fmc-accent-deep text-fmc-text-dim hover:border-red-500/70 hover:text-red-400 hover:bg-red-900/10'
          }`}
        >
          <Heart className={`h-3.5 w-3.5 ${isLiked ? 'fill-current' : ''}`} />
        </button>

        {/* Title + Price */}
        <div className="space-y-1 min-w-0">
          <h3 className="text-sm font-semibold text-fmc-text group-hover:text-fmc-glow transition-colors line-clamp-2 font-mono leading-snug">
            {title || 'Annonce sans titre'}
          </h3>
          {price && (
            <p className="text-xl font-bold text-fmc-accent font-mono">
              {new Intl.NumberFormat('fr-FR').format(price)}&nbsp;€
            </p>
          )}
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

    {/* Gallery lightbox */}
    {galleryOpen && listing.images && (
      <div
        className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
        onClick={() => setGalleryOpen(false)}
      >
        <div className="relative max-w-4xl w-full" onClick={e => e.stopPropagation()}>
          <button
            className="absolute -top-10 right-0 text-white font-mono text-sm hover:text-red-400"
            onClick={() => setGalleryOpen(false)}
          >
            ✕ Fermer
          </button>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {listing.images.map((img, i) => (
              <img
                key={i}
                src={img}
                alt={`Photo ${i + 1}`}
                className="w-full h-48 object-cover rounded-lg cursor-pointer hover:opacity-90"
                onClick={() => window.open(img, '_blank')}
              />
            ))}
          </div>
        </div>
      </div>
    )}
    </>
  );
}
