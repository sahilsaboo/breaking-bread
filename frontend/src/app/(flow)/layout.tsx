// The link → recipe → location → pantry → results screens share one narrow,
// phone-friendly column.
export default function FlowLayout({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-xl px-4 pt-2 pb-12">{children}</div>;
}
