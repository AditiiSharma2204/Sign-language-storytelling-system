export type TokenStatus = 'exact' | 'lemma' | 'synonym' | 'spell' | 'card' | 'dropped'

export interface Token {
  surface: string
  status: TokenStatus
  gloss: string | null
  reason: string
}

export interface SentenceResult {
  text: string
  tense: 'past' | 'present' | 'future'
  is_question: boolean
  reordered: boolean
  tokens: Token[]
  gloss: string[]
}

export interface LetterTiming {
  letter: string
  start: number
  end: number
}

export interface Segment {
  label: string
  word: string
  letters: LetterTiming[] | null
  kind: 'sign' | 'card' | 'spell'
  surface: string
  status: TokenStatus
  sentence: number
  start: number
  end: number
}

export interface Metrics {
  words_in: number
  grammar_dropped: number
  signed: number
  spelled: number
  text_cards: number
  sign_coverage: number
  conveyed_coverage: number
  baseline_coverage: number
  improvement: number
  unique_signs: number
  vocab_utilization: number
  reordered_sentences: number
  latency_ms: number
  cached?: boolean
}

export interface TranslateResult {
  input: string
  sentences: SentenceResult[]
  timeline: Segment[]
  video_url: string | null
  vtt_url: string | null
  srt_url: string | null
  duration: number
  metrics: Metrics
}

export interface VocabEntry {
  word: string
  source?: 'curated' | 'wlasl'
  url: string
  aliases: string[]
}

export interface AlphabetEntry {
  letter: string
  url: string
  has_asset: boolean
}

export interface Alphabet {
  letters: AlphabetEntry[]
  letters_with_assets: number
  missing: string[]
}
