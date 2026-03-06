import './VehicleScore.css';

const scoreColor = (score) => {
  if (score === null || score === undefined) return 'grey';
  if (score >= 7) return 'green';
  if (score >= 4) return 'orange';
  return 'red';
};

export default function VehicleScore({ vehicle }) {
  if (!vehicle) return null;

  const { reliability_score, common_issues } = vehicle;
  const color = scoreColor(reliability_score);

  return (
    <div className="vehicle-score">
      <div className={`vehicle-score__badge vehicle-score__badge--${color}`}>
        {reliability_score !== null && reliability_score !== undefined
          ? <><strong>{reliability_score}</strong><span>/10</span></>
          : <span>N/A</span>
        }
      </div>
      {common_issues && common_issues.length > 0 ? (
        <ul className="vehicle-score__issues">
          {common_issues.slice(0, 3).map((issue, i) => (
            <li key={i}>{issue}</li>
          ))}
        </ul>
      ) : (
        <p className="vehicle-score__no-data">Données fiabilité non disponibles</p>
      )}
    </div>
  );
}
