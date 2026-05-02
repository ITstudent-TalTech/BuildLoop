"use client";

import { useRouter } from "next/navigation";

export default function PassportRetryButton() {
  const router = useRouter();

  return (
    <button
      className="inline-flex items-center rounded-md bg-forest px-6 py-3 font-medium text-white transition hover:bg-forest/95"
      onClick={() => router.refresh()}
      type="button"
    >
      Retry
    </button>
  );
}
