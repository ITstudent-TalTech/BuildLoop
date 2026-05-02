"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { resolveAddress } from "@/lib/api";

interface RetryResolveButtonProps {
  intakeId: string;
}

export default function RetryResolveButton({ intakeId }: RetryResolveButtonProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRetry() {
    setIsLoading(true);
    setError(null);

    try {
      await resolveAddress(intakeId);
      router.refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Retry failed";
      setError(message);
      setIsLoading(false);
    }
  }

  return (
    <div>
      <button
        aria-busy={isLoading}
        className="inline-flex items-center rounded-md bg-forest px-6 py-3 font-medium text-white transition hover:bg-forest/95 disabled:cursor-not-allowed disabled:bg-forest/45"
        disabled={isLoading}
        onClick={() => {
          void handleRetry();
        }}
        type="button"
      >
        {isLoading ? "Retrying…" : "Retry"}
      </button>
      {error ? (
        <p className="mt-3 text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
