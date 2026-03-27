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

// Extract label from "Label: N témoignages" format
function parseIssueName(issue) {
  if (typeof issue !== 'string') return String(issue);
  const colonIdx = issue.indexOf(':');
  return colonIdx !== -1 ? issue.slice(0, colonIdx).trim() : issue;
}

export default function VehicleScore({ vehicle }) {
  if (!vehicle) return null;

  const { reliability_score, common_issues, known_issues_text, total_testimonials, reliability_rank } = vehicle;
  const hasScore = reliability_score !== null && reliability_score !== undefined;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className={clsx(
          'fmc-score flex items-center justify-center rounded-full border-2 w-12 h-12 font-bold text-lg',
          scoreBorderClass(reliability_score),
          scoreTextClass(reliability_score),
        )}>
          {hasScore ? reliability_score : '–'}
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-fmc-text-dim text-xs leading-tight">
            {hasScore
              ? `/100 fiabilité${total_testimonials ? ` · ${total_testimonials.toLocaleString('fr-FR')} tém.` : ''}`
              : 'N/A'
            }
          </span>
          {reliability_rank && (
            <span className="text-fmc-text-muted text-[10px] font-mono capitalize">
              Catégorie : {reliability_rank}
            </span>
          )}
        </div>
      </div>

      {/* Problèmes courants (labels uniquement) */}
      {common_issues && common_issues.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {common_issues.slice(0, 5).map((issue, i) => (
            <span key={i} className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-zinc-800/70 text-zinc-400 border border-zinc-700/40">
              {parseIssueName(issue)}
            </span>
          ))}
        </div>
      )}

      {/* Descriptions détaillées des problèmes */}
      {known_issues_text && known_issues_text.length > 0 ? (
        <ul className="space-y-1.5 text-xs">
          {known_issues_text.slice(0, 2).map((issueBlock, i) => {
            const text = typeof issueBlock === 'string' ? issueBlock : String(issueBlock);
            // Split on ". " ou ":" to extract individual points
            const sentences = text.split(/(?<=[.!?])\s+/).filter(s => s.length > 20);
            const preview = sentences[0] || text;
            return (
              <li key={i} className="text-fmc-text-muted leading-relaxed">
                {preview.slice(0, 120)}{preview.length > 120 ? '…' : ''}
              </li>
            );
          })}
        </ul>
      ) : common_issues && common_issues.length > 0 ? null : (
        <p className="text-sm text-fmc-text-muted">Données fiabilité non disponibles</p>
      )}
    </div>
  );
}
