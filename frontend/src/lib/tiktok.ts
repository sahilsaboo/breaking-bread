/** The numeric post id from a full TikTok video URL, or null for anything else. */
export function tiktokVideoId(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const { hostname, pathname } = new URL(url);
    if (!/(^|\.)tiktok\.com$/.test(hostname)) return null;
    return pathname.match(/\/video\/(\d+)/)?.[1] ?? null;
  } catch {
    return null;
  }
}

// TikTok's official embed player:
// https://developers.tiktok.com/doc/embed-player
export function tiktokPlayerUrl(id: string): string {
  const params = new URLSearchParams({
    controls: "1",
    progress_bar: "1",
    play_button: "1",
    volume_control: "1",
    fullscreen_button: "0",
    music_info: "0",
    description: "0",
    rel: "0",
  });
  return `https://www.tiktok.com/player/v1/${id}?${params}`;
}
