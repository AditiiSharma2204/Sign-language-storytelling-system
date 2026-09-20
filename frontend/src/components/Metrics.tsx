import type { Metrics as M } from '../types'

const pct = (n: number) => `${Math.round(n * 100)}%`

function Bar({ label, value, tone }: { label: string; value: number; tone: 'base' | 'new' | 'spell' }) {
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track">
        <div className={`bar-fill ${tone}`} style={{ width: pct(value) }} />
      </div>
      <span className="mono bar-value">{pct(value)}</span>
    </div>
  )
}

export default function Metrics({ m }: { m: M }) {
  return (
    <div className="card">
      <div className="card-head">
        <h2>Metrics</h2>
        <span className="muted mono">
          {m.latency_ms} ms{m.cached ? ' · cached render' : ''}
        </span>
      </div>

      <div className="compare">
        <Bar label="Exact match only" value={m.baseline_coverage} tone="base" />
        <Bar label="SignStory signs" value={m.sign_coverage} tone="new" />
        <Bar label="+ fingerspelling" value={m.conveyed_coverage} tone="spell" />
        <p className="muted small-text">
          Sign coverage = words that got a sign ÷ words that need one (articles, “to be” and
          prepositions excluded). The baseline counts exact vocabulary matches only.
          {m.improvement > 0 && (
            <strong> +{Math.round(m.improvement * 100)} points on this input.</strong>
          )}
        </p>
      </div>

      <div className="stats">
        <Stat value={m.signed} label="signed" />
        <Stat value={m.spelled} label="fingerspelled" />
        <Stat value={m.text_cards} label="text cards" />
        <Stat value={m.grammar_dropped} label="dropped (grammar)" />
        <Stat value={m.unique_signs} label="unique signs" />
        <Stat value={pct(m.vocab_utilization)} label="vocab used" />
      </div>
    </div>
  )
}

function Stat({ value, label }: { value: number | string; label: string }) {
  return (
    <div className="stat">
      <div className="stat-value mono">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
