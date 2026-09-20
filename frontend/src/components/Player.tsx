import { useCallback, useEffect, useRef, useState } from 'react'
import type { TranslateResult } from '../types'

const SPEEDS = [0.5, 0.75, 1, 1.25]

export default function Player({ result }: { result: TranslateResult }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [active, setActive] = useState(0)
  const [activeLetter, setActiveLetter] = useState(-1)
  const [speed, setSpeed] = useState(1)
  const [loop, setLoop] = useState(false)
  const { timeline, duration } = result

  // Keep the highlighted word in sync with the video clock.
  useEffect(() => {
    const v = videoRef.current
    if (!v) return
    let raf = 0
    const tick = () => {
      const t = v.currentTime
      const i = timeline.findIndex((s) => t >= s.start && t < s.end)
      if (i >= 0) {
        setActive(i)
        setActiveLetter(timeline[i].letters?.findIndex((l) => t >= l.start && t < l.end) ?? -1)
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [timeline])

  useEffect(() => {
    const v = videoRef.current
    if (v) v.playbackRate = speed
  }, [speed, result.video_url])

  const seek = useCallback(
    (i: number) => {
      const v = videoRef.current
      if (!v) return
      v.currentTime = timeline[i].start + 0.01
      setActive(i)
      void v.play()
    },
    [timeline],
  )

  if (!result.video_url) return null
  const current = timeline[active]

  return (
    <div className="card player">
      <div className="video-wrap">
        <video
          ref={videoRef}
          key={result.video_url}
          src={result.video_url}
          controls
          autoPlay
          muted
          playsInline
          loop={loop}
          onLoadedMetadata={(e) => (e.currentTarget.playbackRate = speed)}
        />
        {current && (
          <div className={`caption ${current.kind}`} aria-live="polite">
            {current.letters
              ? current.letters.map((l, i) => (
                  <span key={i} className={i === activeLetter ? 'letter on' : 'letter'}>
                    {l.letter}
                  </span>
                ))
              : current.label}
          </div>
        )}
      </div>

      <div className="timeline" role="list" aria-label="Sign sequence">
        {timeline.map((s, i) => (
          <button
            key={i}
            role="listitem"
            className={`seg ${s.kind} ${i === active ? 'on' : ''}`}
            style={{ flexGrow: s.end - s.start }}
            onClick={() => seek(i)}
            title={`${s.label} · ${s.start.toFixed(1)}s`}
          >
            <span>{s.label}</span>
          </button>
        ))}
      </div>

      <div className="player-bar">
        <div className="speed" role="group" aria-label="Playback speed">
          {SPEEDS.map((s) => (
            <button key={s} className={s === speed ? 'on' : ''} onClick={() => setSpeed(s)}>
              {s}×
            </button>
          ))}
        </div>
        <label className="toggle">
          <input type="checkbox" checked={loop} onChange={(e) => setLoop(e.target.checked)} />
          Loop
        </label>
        <span className="muted mono">{duration.toFixed(1)}s · {timeline.length} signs</span>
        <span className="spacer" />
        <a className="btn ghost" href={result.video_url} download>
          MP4
        </a>
        {result.srt_url && (
          <a className="btn ghost" href={result.srt_url} download>
            SRT
          </a>
        )}
      </div>
    </div>
  )
}
