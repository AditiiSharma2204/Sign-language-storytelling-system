import type { Alphabet, TranslateResult, VocabEntry } from './types'

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function translate(text: string): Promise<TranslateResult> {
  const res = await fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return parse(res)
}

export async function fetchVocab(): Promise<VocabEntry[]> {
  const data = await parse<{ words: VocabEntry[] }>(await fetch('/api/vocab'))
  return data.words
}

export async function fetchAlphabet(): Promise<Alphabet> {
  return parse(await fetch('/api/alphabet'))
}

export async function fetchHealth(): Promise<{ vocab_size: number }> {
  return parse(await fetch('/api/health'))
}
