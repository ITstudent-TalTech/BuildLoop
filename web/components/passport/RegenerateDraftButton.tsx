"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { generatePassportDraft } from "@/lib/api";

interface RegenerateDraftButtonProps {
  projectId: string;
}

export default function RegenerateDraftButton({
  projectId,
}: RegenerateDraftButtonProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRegenerate() {
    if (!confirm("Regenerate this draft from source documents?")) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await generatePassportDraft(projectId);
      router.refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Regeneration failed";
      setError(message);
      setTimeout(() => setError(null), 4000);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="relative">
      <button
        className="text-sm text-ink-soft underline-offset-2 hover:underline disabled:cursor-not-allowed disabled:opacity-60"
        disabled={isLoading}
        onClick={() => {
          void handleRegenerate();
        }}
        type="button"
      >
        {isLoading ? "Regenerating…" : "Regenerate draft"}
      </button>
      {error ? (
        <p className="absolute right-0 top-full mt-2 w-56 text-right text-sm text-red-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}
