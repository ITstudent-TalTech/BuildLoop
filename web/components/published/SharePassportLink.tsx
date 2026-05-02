"use client";

import { useEffect, useState } from "react";

export default function SharePassportLink() {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) {
      return;
    }

    const timeout = window.setTimeout(() => setCopied(false), 2000);
    return () => window.clearTimeout(timeout);
  }, [copied]);

  async function handleCopy() {
    await navigator.clipboard.writeText(window.location.href);
    setCopied(true);
  }

  return (
    <div className="mt-6 text-center text-sm">
      <button
        className="text-ink-soft underline-offset-2 hover:underline"
        onClick={() => {
          void handleCopy();
        }}
        type="button"
      >
        Share this passport
      </button>
      {copied ? (
        <span className="ml-2 font-mono text-xs uppercase tracking-[0.06em] text-forest">
          Copied
        </span>
      ) : null}
    </div>
  );
}
