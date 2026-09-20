import type { SentenceResult, TokenStatus } from '../types'

const LEGEND: { status: TokenStatus; label: string }[] = [
  { status: 'exact', label: 'Exact sign' },
  { status: 'lemma', label: 'Inflection matched' },
  { status: 'synonym', label: 'Synonym matched' },
  { status: 'spell', label: 'Fingerspelled' },
  { status: 'card', label: 'Text card (no clip)' },
  { status: 'dropped', label: 'Dropped by ASL grammar' },
]

export default function Pipeline({ sentences }: { sentences: SentenceResult[] }) {
  return (
    <div className="card">
      <div className="card-head">
        <h2>How it was translated</h2>
        <div className="legend">
          {LEGEND.map((l) => (
            <span key={l.status} className={`chip ${l.status} small`}>
              {l.label}
            </span>
          ))}
        </div>
      </div>

      {sentences.map((s, i) => (
        <div className="sentence" key={i}>
          <div className="sentence-meta">
            <span className="muted">Sentence {i + 1}</span>
            <span className="badge">{s.tense} tense</span>
            {s.is_question && <span className="badge">question · wh-word moved last</span>}
            {s.reordered && <span className="badge accent">reordered to ASL</span>}
          </div>

          <div className="row-label">English</div>
          <div className="chips">
            {s.tokens.map((t, j) => (
              <span
                key={j}
                className={`chip ${t.status}`}
                title={t.reason + (t.gloss && t.gloss !== t.surface ? ` → ${t.gloss.toUpperCase()}` : '')}
              >
                {t.surface}
                {(t.status === 'lemma' || t.status === 'synonym') && (
                  <em>→ {t.gloss}</em>
                )}
                {t.status === 'spell' && t.reason.includes('name') && <em>name</em>}
              </span>
            ))}
          </div>

          <div className="row-label">ASL gloss</div>
          <div className="gloss mono">
            {s.gloss.length ? s.gloss.join('  ') : <span className="muted">nothing to sign</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
