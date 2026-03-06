import VehicleScore from './VehicleScore';
import './ListingCard.css';

function formatMileage(km) {
  if (!km) return null;
  return new Intl.NumberFormat('fr-FR').format(km) + ' km';
}

const KEYWORD_COLORS = {
  'CT valide': 'green',
  'Carte grise': 'blue',
  'Premier propriétaire': 'purple',
};

export default function ListingCard({ listing }) {
  const { title, price, year, mileage, location, url, matched_keywords, vehicle } = listing;

  return (
    <div className="listing-card">
      <div className="listing-card__header">
        <h3 className="listing-card__title">{title || 'Annonce sans titre'}</h3>
        {price && <span className="listing-card__price">{new Intl.NumberFormat('fr-FR').format(price)} €</span>}
      </div>
      <div className="listing-card__meta">
        {year && <span>{year}</span>}
        {mileage && <span>{formatMileage(mileage)}</span>}
        {location && <span>{location}</span>}
      </div>
      {matched_keywords && matched_keywords.length > 0 && (
        <div className="listing-card__keywords">
          {matched_keywords.map(kw => (
            <span
              key={kw}
              className={`listing-card__badge listing-card__badge--${KEYWORD_COLORS[kw] || 'default'}`}
            >
              {kw}
            </span>
          ))}
        </div>
      )}
      <VehicleScore vehicle={vehicle} />
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="listing-card__cta"
      >
        Voir l'annonce
      </a>
    </div>
  );
}
