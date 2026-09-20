import { useEffect, useState } from 'react'
import { fetchHealth, translate } from './api'
import Dictionary from './components/Dictionary'
import Metrics from './components/Metrics'
import Pipeline from './components/Pipeline'
import Player from './components/Player'
import type { TranslateResult } from './types'

const EXAMPLES = [
  'Yesterday the kids played in the park and I like the library.',
  'I go to school tomorrow, but my brother sleeps at home.',
  "The dog doesn't like water. Where do you walk?",
  'My mom and dad ate pizza with my wife in the morning.',
]

type Tab = 'translate' | 'dictionary' | 'about'

function loadHistory(): string[] {
  try {
    return JSON.parse(localStorage.getItem('signstory:history') ?? '[]')
  } catch {
    return []
  }
}

export default function App() {
  const [tab, setTab] = useState<Tab>('translate')
  const [text, setText] = useState(EXAMPLES[0])
  const [result, setResult] = useState<TranslateResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<string[]>(loadHistory)
  const [noClips, setNoClips] = useState(false)

  useEffect(() => {
    fetchHealth().then((h) => setNoClips(h.vocab_size === 0)).catch(() => undefined)
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem('signstory:history', JSON.stringify(history))
    } catch {
      /* storage unavailable */
    }
  }, [history])

  // Shareable links: /?q=some+text runs the translation on load.
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get('q')
    if (q) {
      setText(q)
      void run(q)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function run(input = text) {
    if (!input.trim() || loading) return
    setLoading(true)
    setError('')
    try {
      setResult(await translate(input))
      window.history.replaceState(null, '', `?q=${encodeURIComponent(input)}`)
      setHistory((h) => [input, ...h.filter((x) => x !== input)].slice(0, 6))
    } catch (e) {
      setError(e instanceof TypeError ? 'Cannot reach the API. Is the backend running on port 8000?' : (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <header className="nav">
        <div className="nav-inner">
          <div className="brand">
            <span className="logo" aria-hidden />
            SignStory
          </div>
          <nav>
            {(['translate', 'dictionary', 'about'] as Tab[]).map((t) => (
              <button key={t} className={t === tab ? 'on' : ''} onClick={() => setTab(t)}>
                {t === 'about' ? 'How it works' : t[0].toUpperCase() + t.slice(1)}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="container">
        {tab === 'translate' && (
          <>
            <section className="hero">
              <h1>English to ASL, sentence by sentence.</h1>
              <p className="muted">
                Type a sentence or a short story. SignStory converts it into ASL gloss order and stitches the
                matching sign clips into one video.
              </p>
            </section>

            <div className="card composer">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) void run()
                }}
                rows={4}
                maxLength={1200}
                placeholder="Write a sentence or a short story…"
                aria-label="Text to translate"
              />
              <div className="composer-bar">
                <div className="chips">
                  {EXAMPLES.map((ex) => (
                    <button key={ex} className="chip example" onClick={() => { setText(ex); void run(ex) }}>
                      {ex.length > 34 ? ex.slice(0, 34) + '…' : ex}
                    </button>
                  ))}
                </div>
                <span className="muted mono">{text.length}/1200</span>
                <button className="btn primary" disabled={loading || !text.trim()} onClick={() => void run()}>
                  {loading ? 'Generating…' : 'Generate signs'}
                </button>
              </div>
              {history.length > 0 && (
                <div className="history">
                  <span className="muted">Recent</span>
                  {history.map((h) => (
                    <button key={h} className="link" onClick={() => setText(h)} title={h}>
                      {h.length > 40 ? h.slice(0, 40) + '…' : h}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {noClips && (
              <div className="notice" role="status">
                No sign clips are installed, so every word is fingerspelled. See “Getting the sign clips” in the README to
                add the vocabulary.
              </div>
            )}

            {error && <div className="error" role="alert">{error}</div>}

            {result && (
              <div className="results">
                {result.video_url ? (
                  <Player result={result} />
                ) : (
                  <div className="card empty">None of these words have signs in the vocabulary yet.</div>
                )}
                <div className="side">
                  <Metrics m={result.metrics} />
                </div>
                <div className="wide">
                  <Pipeline sentences={result.sentences} />
                </div>
              </div>
            )}
          </>
        )}

        {tab === 'dictionary' && <Dictionary />}
        {tab === 'about' && <About />}
      </main>

      <footer className="footer muted">Signs from the WLASL dataset · Built with FastAPI, FFmpeg and React</footer>
    </>
  )
}

function About() {
  const steps = [
    ['1 · Tokenise', 'Expand contractions, lowercase, split into words and sentences.'],
    ['2 · Match', 'Exact vocabulary match → synonym map → vocabulary-aware lemmatizer (played → play, kids → children).'],
    ['3 · ASL grammar', 'Drop articles, “to be”, auxiliaries and prepositions. Move time signs first and wh-words last.'],
    ['4 · Fingerspell', 'Words with no sign, and capitalised names in mid-sentence, are spelled letter by letter, with a pause between double letters. Words that have their own ASL sign but no clip (not, it, where…) show a labelled text card instead.'],
    ['5 · Render', 'Each clip is normalised once, cached, then joined losslessly with FFmpeg. Timings drive the synced captions.'],
  ]
  return (
    <section className="about">
      <h1>How it works</h1>
      <p className="muted">
        A rule-based translation pipeline. It does not claim full ASL fluency: it handles the grammar rules above over a
        closed vocabulary and is explicit about everything it cannot sign.
      </p>
      <ol className="steps">
        {steps.map(([t, d]) => (
          <li key={t} className="card">
            <h3>{t}</h3>
            <p className="muted">{d}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}
