"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { formatDuration } from "@/lib/format";
import { tiktokPlayerUrl, tiktokVideoId } from "@/lib/tiktok";

import { Illustration } from "../Illustration";

type PlayerMessage = { "x-tiktok-player"?: boolean; type?: string; value?: unknown };

/**
 * The source video, kept next to the current step. For TikTok links it jumps
 * to the step's part of the video and loops that clip. Anything else (Reels,
 * pasted text) gets a link out instead, since only TikTok's player can seek.
 */
export function VideoPanel({
  sourceUrl,
  start,
  end,
}: {
  sourceUrl: string | null | undefined;
  start: number | null | undefined;
  end: number | null | undefined;
}) {
  const id = tiktokVideoId(sourceUrl);
  const frame = useRef<HTMLIFrameElement>(null);
  const [ready, setReady] = useState(false);
  const [loop, setLoop] = useState(true);
  // Read inside the message handler without re-subscribing on every step.
  const clip = useRef({ start, end, loop });
  useEffect(() => {
    clip.current = { start, end, loop };
  }, [start, end, loop]);

  const send = useCallback((type: string, value?: number) => {
    frame.current?.contentWindow?.postMessage({ "x-tiktok-player": true, type, value }, "*");
  }, []);

  const playClip = useCallback(() => {
    if (clip.current.start == null) return;
    send("seekTo", clip.current.start);
    send("play");
  }, [send]);

  useEffect(() => {
    function onMessage(e: MessageEvent) {
      if (e.origin !== "https://www.tiktok.com") return;
      let msg: PlayerMessage = e.data;
      if (typeof msg === "string") {
        try {
          msg = JSON.parse(msg);
        } catch {
          return;
        }
      }
      if (!msg?.["x-tiktok-player"]) return;
      if (msg.type === "onPlayerReady") setReady(true);
      if (msg.type === "onCurrentTime") {
        const now = (msg.value as { currentTime?: number })?.currentTime ?? 0;
        const { start: s, end: t, loop: looping } = clip.current;
        if (looping && s != null && t != null && now >= t) send("seekTo", s);
      }
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [send]);

  // Jump to the new step's clip whenever the step changes.
  useEffect(() => {
    if (ready) playClip();
  }, [ready, start, playClip]);

  if (!id) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-3xl bg-sky-soft p-6 text-center">
        <Illustration name="clapper-board" size={64} tint="bg-card" />
        <p className="text-sm text-muted">
          We can follow along in the video for TikTok links.
          {sourceUrl && (
            <>
              {" "}
              <a href={sourceUrl} target="_blank" rel="noreferrer" className="font-semibold text-accent-ink underline">
                Watch the original
              </a>
            </>
          )}
        </p>
      </div>
    );
  }

  const hasClip = start != null;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="aspect-[9/16] h-[34vh] overflow-hidden rounded-3xl bg-foreground/90 shadow-lg ring-4 ring-card lg:h-[min(640px,calc(100vh-9rem))]">
        <iframe
          ref={frame}
          src={tiktokPlayerUrl(id)}
          title="Recipe video"
          className="size-full"
          allow="autoplay; fullscreen; encrypted-media"
        />
      </div>
      {hasClip && (
        <div className="flex flex-wrap items-center justify-center gap-2 text-sm">
          <span className="rounded-full bg-sorbet-soft px-3 py-1 font-semibold text-sorbet-ink tabular-nums">
            This step: {formatDuration(Math.floor(start))}
            {end != null && `–${formatDuration(Math.floor(end))}`}
          </span>
          <button type="button" className="btn-secondary py-1 text-sm" onClick={playClip} disabled={!ready}>
            Replay
          </button>
          <label className="flex cursor-pointer items-center gap-1.5 text-muted">
            <input type="checkbox" className="accent-accent" checked={loop} onChange={(e) => setLoop(e.target.checked)} />
            Loop
          </label>
        </div>
      )}
    </div>
  );
}
