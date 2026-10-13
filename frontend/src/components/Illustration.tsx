import {
  ILLUSTRATIONS,
  ILLUSTRATIONS_MONO,
  type IllustrationName,
  type MonoIllustrationName,
} from "@/lib/illustrations.generated";

/**
 * A Fluent Emoji (flat) drawing on a soft pastel tile. The SVG bodies come
 * from our own generated file, never from user or API data.
 */
export function Illustration({
  name,
  size = 48,
  tint = "bg-sky-soft",
  className = "",
}: {
  name: IllustrationName;
  size?: number;
  tint?: string;
  className?: string;
}) {
  return (
    <span
      className={`inline-grid shrink-0 place-items-center rounded-2xl ${tint} ${className}`}
      style={{ width: size, height: size }}
      aria-hidden
    >
      <svg
        viewBox="0 0 32 32"
        width={Math.round(size * 0.62)}
        height={Math.round(size * 0.62)}
        dangerouslySetInnerHTML={{ __html: ILLUSTRATIONS[name] }}
      />
    </span>
  );
}

/**
 * A single-color Fluent Emoji (high contrast) icon on a tile. It draws in the
 * current text color (`color`, dark green by default), so a row of these reads
 * as one set.
 */
export function MonoIllustration({
  name,
  size = 48,
  tint = "bg-card",
  color = "text-accent",
  className = "",
}: {
  name: MonoIllustrationName;
  size?: number;
  tint?: string;
  color?: string;
  className?: string;
}) {
  return (
    <span
      className={`inline-grid shrink-0 place-items-center rounded-2xl ${tint} ${color} ${className}`}
      style={{ width: size, height: size }}
      aria-hidden
    >
      <svg
        viewBox="0 0 32 32"
        width={Math.round(size * 0.56)}
        height={Math.round(size * 0.56)}
        dangerouslySetInnerHTML={{ __html: ILLUSTRATIONS_MONO[name] }}
      />
    </span>
  );
}
