"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const ZIP = /^\d{5}$/;

export function LocationForm({ recipeId }: { recipeId: string }) {
  const router = useRouter();
  const [zip, setZip] = useState("");
  const [touched, setTouched] = useState(false);
  const valid = ZIP.test(zip);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (!valid) return;
    router.push(`/recipes/${recipeId}/pantry?zip=${zip}`);
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3">
      <label htmlFor="zip" className="text-sm font-medium">
        ZIP code
      </label>
      <input
        id="zip"
        className="input max-w-40 text-lg tracking-widest"
        inputMode="numeric"
        autoComplete="postal-code"
        maxLength={5}
        placeholder="02139"
        value={zip}
        onChange={(e) => setZip(e.target.value.replace(/\D/g, ""))}
        onBlur={() => setTouched(true)}
        aria-invalid={touched && !valid}
        aria-describedby="zip-help"
        autoFocus
      />
      <p id="zip-help" className={`text-sm ${touched && !valid ? "text-danger" : "text-muted"}`}>
        {touched && !valid
          ? "Enter a 5-digit ZIP code."
          : "We only use this to look up prices near you. It isn't saved."}
      </p>
      <button type="submit" className="btn-primary mt-2">
        Next: what do you already have?
      </button>
    </form>
  );
}
