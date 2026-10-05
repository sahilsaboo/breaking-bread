import { ILLUSTRATIONS, type IllustrationName } from "@/lib/illustrations.generated";

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
