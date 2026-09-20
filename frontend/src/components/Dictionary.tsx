import { useEffect, useMemo, useState } from 'react'
import { fetchAlphabet, fetchVocab } from '../api'
import type { Alphabet, VocabEntry } from '../types'

function Tile({ entry }: { entry: VocabEntry }) {
  return (
    <figure
      className="tile"
      onMouseEnter={(e) => void e.currentTarget.querySelector('video')?.play()}
      onMouseLeave={(e) => {
        const v = e.currentTarget.querySelector('video')
        if (v) {
          v.pause()
          v.currentTime = 0
        }
      }}
    >
      <video src={entry.url} muted loop playsInline preload="metadata" />
      <figcaption>
        <strong>{entry.word}</strong>
        {entry.aliases.length > 0 && <span className="muted">{entry.aliases.join(', ')}</span>}
      </figcaption>
    </figure>
  )
}

export default function Dictionary() {
  const [words, setWords] = useState<VocabEntry[]>([])
  const [q, setQ] = useState('')
  const [error, setError] = useState('')
  const [alphabet, setAlphabet] = useState<Alphabet | null>(null)

  useEffect(() => {
    fetchVocab().then(setWords).catch((e: Error) => setError(e.message))
    fetchAlphabet().then(setAlphabet).catch(() => undefined)
  }, [])

  const shown = useMemo(
    () => words.filter((w) => w.word.includes(q.toLowerCase()) || w.aliases.some((a) => a.includes(q.toLowerCase()))),
    [words, q],
  )

  return (
    <section>
      <div className="section-head">
        <div>
          <h1>Sign dictionary</h1>
          <p className="muted">
            {words.length} signs from WLASL. Hover a card to preview it. Listed synonyms are mapped to the sign
            automatically.
          </p>
        </div>
        <input
          className="search"
          type="search"
          placeholder="Search words…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search dictionary"
        />
      </div>
      {error && <p className="error">{error}</p>}
      <div className="grid">
        {shown.map((w) => (
          <Tile key={w.word} entry={w} />
        ))}
      </div>
      {!error && words.length > 0 && shown.length === 0 && <p className="muted">No signs match “{q}”.</p>}

      {alphabet && (
        <div className="alphabet">
          <h2>Fingerspelling alphabet</h2>
          <p className="muted small-text">
            Words without a sign are spelled letter by letter.{' '}
            {alphabet.letters_with_assets === 26
              ? 'All 26 letters use hand-shape assets.'
              : `${alphabet.letters_with_assets}/26 letters have hand-shape assets in fingerspelling/; the rest use letter cards.`}
          </p>
          <div className="letters">
            {alphabet.letters.map((l) => (
              <Tile key={l.letter} entry={{ word: l.letter.toUpperCase(), url: l.url, aliases: [] }} />
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
