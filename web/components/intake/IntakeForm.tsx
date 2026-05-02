"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { createIntake, resolveAddress } from "@/lib/api";

type SubmitState = "idle" | "submitting" | "resolved" | "error";

export default function IntakeForm() {
  const router = useRouter();
  const addressInputRef = useRef<HTMLInputElement>(null);
  const [addressInput, setAddressInput] = useState("");
  const [projectTitle, setProjectTitle] = useState("");
  const [isEhrEntryOpen, setIsEhrEntryOpen] = useState(false);
  const [ehrCode, setEhrCode] = useState("");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [resolvedAddress, setResolvedAddress] = useState<string | null>(null);

  const isSubmitting = submitState === "submitting";
  const trimmedEhrCode = ehrCode.trim();
  const hasEhrCode = trimmedEhrCode.length > 0;
  const isEhrCodeValid = /^\d{7,9}$/.test(trimmedEhrCode);
  const canSubmit =
    submitState === "idle" &&
    ((hasEhrCode && isEhrCodeValid) ||
      (!hasEhrCode && addressInput.trim().length > 0));

  function clearError() {
    setErrorMessage(null);
    setSubmitState("idle");
    requestAnimationFrame(() => {
      addressInputRef.current?.focus();
    });
  }

  async function handleSubmit() {
    if (!canSubmit) {
      return;
    }

    setSubmitState("submitting");
    setErrorMessage(null);
    setResolvedAddress(null);

    try {
      const trimmedAddress = addressInput.trim();
      const project_title = projectTitle.trim();

      if (hasEhrCode && isEhrCodeValid) {
        // TODO: Track 2 should support EHR-code-first resolution on the backend.
        const intake = await createIntake({
          address_input: trimmedEhrCode,
          project_title,
        });

        setResolvedAddress(`EHR ${trimmedEhrCode}`);
        setSubmitState("resolved");
        setTimeout(() => {
          router.push(`/passport/${intake.project_id}`);
        }, 1200);
        return;
      }

      const intake = await createIntake({
        address_input: trimmedAddress,
        project_title,
      });

      const resolution = await resolveAddress(intake.intake_request_id);

      if (resolution.status === "resolved") {
        setResolvedAddress(resolution.normalized_address);
        setSubmitState("resolved");
        setTimeout(() => {
          router.push(`/passport/${intake.project_id}`);
        }, 1200);
        return;
      }

      if (resolution.status === "ambiguous") {
        router.push(
          `/intake/resolve?run=${resolution.resolution_run_id}` +
            `&intake=${intake.intake_request_id}` +
            `&address=${encodeURIComponent(trimmedAddress)}`,
        );
        return;
      }

      router.push(
        `/intake/resolve?run=${resolution.resolution_run_id}` +
          `&intake=${intake.intake_request_id}` +
          `&address=${encodeURIComponent(trimmedAddress)}`,
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setErrorMessage(message);
      setSubmitState("error");
    }
  }

  return (
    <form
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        void handleSubmit();
      }}
    >
      {submitState === "error" ? (
        <div
          className="border-l-2 border-red-500 bg-red-50/40 p-3 text-sm"
          role="alert"
        >
          <p className="font-medium text-ink">We couldn&apos;t find that address</p>
          <p className="mt-1 text-ink-soft">
            {errorMessage}{" "}
            <button
              className="font-medium text-forest underline-offset-4 hover:underline"
              onClick={clearError}
              type="button"
            >
              Edit and try again
            </button>
          </p>
        </div>
      ) : null}

      <div>
        <label
          className="block text-sm font-medium text-ink"
          htmlFor="building-address"
        >
          Building address
        </label>
        <input
          aria-describedby="building-address-helper"
          className={[
            "mt-2 w-full rounded-md border border-ink/15 bg-white px-3.5 py-3 text-base text-ink outline-none transition",
            "placeholder:text-ink-soft/55 focus:border-forest focus:ring-2 focus:ring-forest/15",
            isSubmitting ? "cursor-wait bg-white/70 text-ink-soft" : "",
          ].join(" ")}
          id="building-address"
          onChange={(event) => setAddressInput(event.target.value)}
          placeholder="Lai 1, 10133 Tallinn"
          readOnly={isSubmitting}
          ref={addressInputRef}
          type="text"
          value={addressInput}
        />
        <p className="mt-2 text-sm text-ink-soft" id="building-address-helper">
          Currently supports Estonian addresses
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between gap-3">
          <label
            className="block text-sm font-medium text-ink"
            htmlFor="project-title"
          >
            Project title
          </label>
          <span className="rounded border border-ink/10 bg-white px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.06em] text-ink-soft">
            Optional
          </span>
        </div>
        <input
          aria-describedby="project-title-helper"
          className={[
            "mt-2 w-full rounded-md border border-ink/15 bg-white px-3.5 py-3 text-base text-ink outline-none transition",
            "placeholder:text-ink-soft/55 focus:border-forest focus:ring-2 focus:ring-forest/15",
            isSubmitting ? "cursor-wait bg-white/70 text-ink-soft" : "",
          ].join(" ")}
          id="project-title"
          onChange={(event) => setProjectTitle(event.target.value)}
          placeholder="Pelguranna quarter — phase 2"
          readOnly={isSubmitting}
          type="text"
          value={projectTitle}
        />
        <p className="mt-2 text-sm text-ink-soft" id="project-title-helper">
          Used internally — e.g. &apos;Pelguranna kvartal — phase 2&apos;
        </p>

        <div className="mt-3">
          <button
            className="text-sm text-ink-soft underline-offset-2 hover:underline"
            disabled={isSubmitting}
            onClick={() => setIsEhrEntryOpen((current) => !current)}
            type="button"
          >
            I already have an EHR code
          </button>

          {isEhrEntryOpen ? (
            <div className="mt-3 rounded-md border border-ink/10 bg-white p-3">
              <label
                className="block text-sm font-medium text-ink"
                htmlFor="ehr-code"
              >
                EHR code
              </label>
              <div className="mt-2 flex items-center gap-2">
                <input
                  aria-describedby="ehr-code-helper"
                  className={[
                    "w-full rounded-md border border-ink/15 bg-white px-3.5 py-3 font-mono text-base text-ink outline-none transition",
                    "placeholder:text-ink-soft/55 focus:border-forest focus:ring-2 focus:ring-forest/15",
                    hasEhrCode && !isEhrCodeValid
                      ? "border-red-500/60 focus:border-red-500 focus:ring-red-500/10"
                      : "",
                    isSubmitting ? "cursor-wait bg-white/70 text-ink-soft" : "",
                  ].join(" ")}
                  id="ehr-code"
                  inputMode="numeric"
                  onChange={(event) => setEhrCode(event.target.value)}
                  placeholder="101035685"
                  readOnly={isSubmitting}
                  type="text"
                  value={ehrCode}
                />
                <button
                  aria-label="Clear EHR code"
                  className="inline-flex size-10 shrink-0 items-center justify-center rounded-md border border-ink/10 text-ink-soft transition hover:border-forest hover:text-forest disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isSubmitting}
                  onClick={() => {
                    setEhrCode("");
                    setIsEhrEntryOpen(false);
                  }}
                  type="button"
                >
                  ×
                </button>
              </div>
              <p className="mt-2 text-sm text-ink-soft" id="ehr-code-helper">
                Enter the Estonian construction register code directly.
                We&apos;ll skip the address resolution step.
              </p>
              {hasEhrCode && !isEhrCodeValid ? (
                <p className="mt-1 text-sm text-red-700">
                  Use a 7-9 digit number.
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      <div className="pt-1">
        <button
          aria-busy={isSubmitting}
          className="inline-flex items-center gap-2 rounded-md bg-forest px-6 py-3 font-medium text-white transition hover:bg-forest/95 disabled:cursor-not-allowed disabled:bg-ink-soft/15 disabled:text-ink-soft disabled:hover:bg-ink-soft/15"
          disabled={!canSubmit}
          type="submit"
        >
          {isSubmitting ? (
            <>
              <span
                aria-hidden="true"
                className="size-4 animate-spin rounded-full border-2 border-forest-light/40 border-t-forest-light"
              />
              Finding building…
            </>
          ) : (
            <>
              Find building
              <span aria-hidden="true">→</span>
            </>
          )}
        </button>

        {submitState === "resolved" && resolvedAddress ? (
          <div className="mt-4 inline-flex items-center gap-2 rounded-md bg-forest-light px-3 py-1.5 text-sm font-medium text-forest">
            <span aria-hidden="true">✓</span>
            <span>Found {resolvedAddress}</span>
          </div>
        ) : null}
      </div>
    </form>
  );
}
