export type MockResolutionMode = "resolved" | "ambiguous" | "unresolved";
export type MockDraftVariant = "complete" | "partial" | "sparse";

export type MockFailure = {
  status: number;
  code: string;
  message: string;
};

type MockOverrides = {
  MOCK_DELAY_MS?: number;
  MOCK_RESOLUTION_MODE?: MockResolutionMode;
  MOCK_DRAFT_VARIANT?: MockDraftVariant;
};

declare global {
  var BUILDLOOP_MOCK_API: MockOverrides | undefined;
}

let failNext: MockFailure | null = null;

function readEnv(name: keyof MockOverrides | "MOCK_FAIL_NEXT") {
  if (typeof process === "undefined") {
    return undefined;
  }

  return process.env[name];
}

function readQuery(name: keyof MockOverrides) {
  if (typeof window === "undefined") {
    return undefined;
  }

  return new URLSearchParams(window.location.search).get(name) ?? undefined;
}

export function getMockDelayMs() {
  const override = globalThis.BUILDLOOP_MOCK_API?.MOCK_DELAY_MS;
  const envValue = readQuery("MOCK_DELAY_MS") ?? readEnv("MOCK_DELAY_MS");
  const rawValue = override ?? (envValue ? Number(envValue) : undefined);

  return typeof rawValue === "number" && Number.isFinite(rawValue) ? rawValue : 500;
}

export function getMockResolutionMode(): MockResolutionMode {
  const value =
    globalThis.BUILDLOOP_MOCK_API?.MOCK_RESOLUTION_MODE ??
    readQuery("MOCK_RESOLUTION_MODE") ??
    readEnv("MOCK_RESOLUTION_MODE");

  if (value === "ambiguous" || value === "unresolved") {
    return value;
  }

  return "resolved";
}

export function getMockDraftVariant(): MockDraftVariant {
  const value =
    globalThis.BUILDLOOP_MOCK_API?.MOCK_DRAFT_VARIANT ??
    readQuery("MOCK_DRAFT_VARIANT") ??
    readEnv("MOCK_DRAFT_VARIANT");

  if (value === "partial" || value === "sparse") {
    return value;
  }

  return "complete";
}

export function setFailNext(failure: MockFailure) {
  failNext = failure;
}

export function consumeFailNext() {
  const current = failNext;
  failNext = null;

  return current;
}

const failNextEnv = readEnv("MOCK_FAIL_NEXT");

if (failNextEnv) {
  const [statusText, code, ...messageParts] = failNextEnv.split(":");
  const status = Number(statusText);
  const message = messageParts.join(":");

  if (Number.isInteger(status) && status >= 100 && code && message) {
    setFailNext({ status, code, message });
  } else {
    console.warn(
      `Invalid MOCK_FAIL_NEXT value "${failNextEnv}". Expected "status:code:message".`,
    );
  }
}
