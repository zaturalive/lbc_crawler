import Badge from './ui/Badge';
import { clsx } from 'clsx';

const scoreVariant = (score) => {
  if (score === null || score === undefined) return 'default';
  if (score >= 80) return 'success';
  if (score >= 50) return 'warning';
  return 'danger';
};

const scoreBorderClass = (score) => {
  if (score === null || score === undefined) return 'border-fmc-border';
  if (score >= 80) return 'border-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]';
  if (score >= 50) return 'border-yellow-500';
  return 'border-red-500';
};

const scoreTextClass = (score) => {
  if (score === null || score === undefined) return 'text-fmc-text-muted';
  if (score >= 80) return 'text-fmc-success';
  if (score >= 50) return 'text-fmc-warning';
  return 'text-fmc-danger';
};

// Parse issue string in format "title:description"
function parseIssue(issue) {
  if (typeof issue !== 'string') return { title: String(issue), description: '' };
  const colonIdx = issue.indexOf(':');
  if (colonIdx === -1) return { title: issue, description: '' };
  return {
    title: issue.slice(0, colonIdx).trim(),
    description: issue.slice(colonIdx + 1).trim(),
  };
}

export default function VehicleScore({ vehicle }) {
  if (!vehicle) return null;

  const { reliability_score, common_issues, total_testimonials } = vehicle;
  const hasScore = reliability_score !== null && reliability_score !== undefined;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className={clsx(
          'fmc-score flex items-center justify-center rounded-full border-2 w-12 h-12 font-bold text-lg',
          scoreBorderClass(reliability_score),
          scoreTextClass(reliability_score),
        )}>
          {hasScore ? (reliability_score / 10).toFixed(1) : '–'}
        </div>
        <span className="text-fmc-text-dim text-xs leading-tight">
          {hasScore
            ? `${(reliability_score / 10).toFixed(1)}/10 fiabilité${total_testimonials ? ` · ${total_testimonials.toLocaleString('fr-FR')} tém.` : ''}`
            : 'N/A'
          }
        </span>
      </div>
      {common_issues && common_issues.length > 0 ? (
        <ul className="space-y-2 text-sm">
          {common_issues.slice(0, 3).map((issue, i) => {
            const { title, description } = parseIssue(issue);
            return (
              <li key={i}>
                <span className="font-medium text-fmc-text capitalize">• {title}</span>
                {description && (
                  <span className="text-fmc-text-muted text-xs block ml-4">
                    {description.slice(0, 80)}{description.length > 80 ? '…' : ''}
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="text-sm text-fmc-text-muted">Données fiabilité non disponibles</p>
      )}
    </div>
  );
}
