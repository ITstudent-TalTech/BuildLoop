// bl-shared.jsx
// BUILDLoop — shared primitives across all screens.
// Top bar (Wordmark + LangSwitch + UserMenu), step indicator, design tokens.
// Anything that should look identical on every screen lives here.

const { useState: blUseState, useEffect: blUseEffect, useRef: blUseRef } = React;

// ─── Tokens ────────────────────────────────────────────────────────────────
// Applied as CSS custom properties on the BLShell root. Single source of truth.
const BL_TOKENS = {
  "--surface": "#ffffff",
  "--surface-2": "#f6f8f7",
  "--primary": "#1f4d3a",
  "--primary-hover": "#173829",
  "--accent": "#c8e6d3",
  "--text": "#0d1f17",
  "--text-2": "#4a5852",
  "--text-3": "#7c8a85",
  "--hairline": "rgba(13, 31, 23, 0.08)",
  "--hairline-strong": "rgba(13, 31, 23, 0.16)",
  "--font-sans": "'Geist', ui-sans-serif, system-ui, -apple-system, 'Helvetica Neue', sans-serif",
  "--font-mono": "'Geist Mono', ui-monospace, 'SF Mono', Menlo, monospace",
};

// ─── Translations for shared chrome only ───────────────────────────────────
const BL_NAV_COPY = {
  en: {
    nav_help: "Help", nav_signed_in_as: "Signed in as",
    nav_account: "Account", nav_sign_out: "Sign out",
    phases: ["Address", "Resolution", "Draft", "Published"],
  },
  et: {
    nav_help: "Abi", nav_signed_in_as: "Sisse logitud",
    nav_account: "Konto", nav_sign_out: "Logi välja",
    phases: ["Aadress", "Tuvastus", "Mustand", "Avaldatud"],
  },
};

// ─── Wordmark ──────────────────────────────────────────────────────────────
function Wordmark({ size = 16 }) {
  return (
    <span style={{
      fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: size,
      letterSpacing: "-0.01em", color: "var(--text)",
      display: "inline-flex", alignItems: "baseline",
    }}>
      <span>BUILD</span>
      <span style={{ color: "var(--primary)", fontWeight: 700 }}>Loop</span>
    </span>
  );
}

// ─── Language switch ───────────────────────────────────────────────────────
function LangSwitch({ lang, onChange }) {
  return (
    <div role="group" aria-label="Language" style={{
      display: "inline-flex", border: "1px solid var(--hairline)",
      borderRadius: 6, overflow: "hidden",
      fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.04em",
    }}>
      {["et", "en"].map((code) => {
        const active = lang === code;
        return (
          <button key={code} onClick={() => onChange(code)} aria-pressed={active}
            style={{
              appearance: "none", border: 0, padding: "5px 9px", minWidth: 28,
              background: active ? "var(--text)" : "transparent",
              color: active ? "var(--surface)" : "var(--text-2)",
              cursor: "default", fontFamily: "inherit", fontSize: "inherit",
              letterSpacing: "inherit", textTransform: "uppercase", fontWeight: 600,
            }}>{code}</button>
        );
      })}
    </div>
  );
}

// ─── Account menu ──────────────────────────────────────────────────────────
function BLMenuItem({ children, danger }) {
  return (
    <button style={{
      appearance: "none", border: 0, background: "transparent",
      width: "100%", textAlign: "left", padding: "7px 10px", borderRadius: 5,
      color: danger ? "#7a2a2a" : "var(--text)",
      fontFamily: "inherit", fontSize: "inherit", cursor: "default",
    }}
    onMouseEnter={(e) => e.currentTarget.style.background = "var(--surface-2)"}
    onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
    >{children}</button>
  );
}

function UserMenu({ lang = "en" }) {
  const t = BL_NAV_COPY[lang] || BL_NAV_COPY.en;
  const [open, setOpen] = blUseState(false);
  const ref = blUseRef(null);
  blUseEffect(() => {
    if (!open) return;
    const onDoc = (e) => { if (!ref.current?.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);
  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button onClick={() => setOpen((o) => !o)} aria-expanded={open} style={{
        appearance: "none", border: "1px solid var(--hairline)",
        background: "var(--surface)", color: "var(--text)", height: 30,
        padding: "0 10px 0 6px", borderRadius: 6,
        display: "inline-flex", alignItems: "center", gap: 8,
        fontFamily: "var(--font-sans)", fontSize: 13, cursor: "default",
      }}>
        <span aria-hidden style={{
          width: 22, height: 22, borderRadius: "50%",
          background: "var(--accent)", color: "var(--primary)",
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          fontSize: 11, fontWeight: 600,
        }}>MK</span>
        <span style={{ color: "var(--text-2)" }}>Mart Kask</span>
        <span aria-hidden style={{ color: "var(--text-3)", fontSize: 9, marginLeft: 2 }}>▾</span>
      </button>
      {open && (
        <div style={{
          position: "absolute", top: "calc(100% + 6px)", right: 0, minWidth: 220,
          background: "var(--surface)", border: "1px solid var(--hairline)",
          borderRadius: 8, boxShadow: "0 8px 24px rgba(13,31,23,0.08)",
          padding: 6, fontFamily: "var(--font-sans)", fontSize: 13,
          zIndex: 20,
        }}>
          <div style={{ padding: "8px 10px", color: "var(--text-3)", fontSize: 11,
            letterSpacing: "0.03em", textTransform: "uppercase",
          }}>{t.nav_signed_in_as}</div>
          <div style={{ padding: "0 10px 8px", color: "var(--text)", fontWeight: 500 }}>
            mart.kask@reaalehitus.ee
          </div>
          <div style={{ height: 1, background: "var(--hairline)", margin: "4px 0" }} />
          <BLMenuItem>{t.nav_account}</BLMenuItem>
          <BLMenuItem>{t.nav_help}</BLMenuItem>
          <div style={{ height: 1, background: "var(--hairline)", margin: "4px 0" }} />
          <BLMenuItem danger>{t.nav_sign_out}</BLMenuItem>
        </div>
      )}
    </div>
  );
}

// ─── Top bar ───────────────────────────────────────────────────────────────
function TopBar({ lang, onLangChange, sticky = true }) {
  return (
    <header style={{
      height: 56, borderBottom: "1px solid var(--hairline)",
      background: "var(--surface)",
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "0 28px",
      position: sticky ? "sticky" : "static", top: 0, zIndex: 10,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <Wordmark size={17} />
        <span style={{
          fontFamily: "var(--font-mono)", fontSize: 10.5,
          color: "var(--text-3)", letterSpacing: "0.08em", textTransform: "uppercase",
          border: "1px solid var(--hairline)", padding: "2px 7px", borderRadius: 4,
          background: "var(--surface-2)",
        }}>v0.1 · MVP</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <LangSwitch lang={lang} onChange={onLangChange} />
        <span style={{ width: 1, height: 22, background: "var(--hairline)" }} />
        <UserMenu lang={lang} />
      </div>
    </header>
  );
}

// ─── Step indicator ─────────────────────────────────────────────────────────
// `active` is 0-indexed: 0=Address, 1=Resolution, 2=Draft, 3=Published.
// Phases before `active` are rendered as "done" (checkmark + accent).
function StepIndicator({ lang, active = 0 }) {
  const phases = (BL_NAV_COPY[lang] || BL_NAV_COPY.en).phases;
  const isDone = (i) => i < active;
  return (
    <div>
      <div className="bl-stepbar-full" style={{
        display: "flex", alignItems: "center", gap: 10,
        fontFamily: "var(--font-mono)", fontSize: 11,
        color: "var(--text-3)", letterSpacing: "0.06em", textTransform: "uppercase",
      }}>
        {phases.map((p, i) => (
          <React.Fragment key={p}>
            {i > 0 && <span aria-hidden style={{
              color: i <= active ? "var(--primary)" : "var(--hairline-strong)",
            }}>───</span>}
            <span style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              color: i === active ? "var(--primary)" : isDone(i) ? "var(--text-2)" : "var(--text-3)",
              fontWeight: i === active ? 600 : 500,
            }}>
              {isDone(i) ? (
                <span aria-hidden style={{
                  width: 16, height: 16, borderRadius: 3,
                  background: "var(--accent)", color: "var(--primary)",
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                  fontSize: 10, fontWeight: 700,
                }}>✓</span>
              ) : i === active ? (
                <span aria-hidden style={{
                  width: 16, height: 16, borderRadius: 3,
                  background: "var(--primary)", color: "#fff",
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                  fontSize: 10, fontWeight: 700,
                }}>{i + 1}</span>
              ) : (
                <span aria-hidden style={{
                  width: 16, height: 16, borderRadius: 3,
                  border: "1px solid var(--hairline-strong)",
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                  fontSize: 10, fontWeight: 600, color: "var(--text-3)",
                }}>{i + 1}</span>
              )}
              {p}
            </span>
          </React.Fragment>
        ))}
      </div>
      <div className="bl-stepbar-mini" style={{
        display: "none",
        alignItems: "center", justifyContent: "space-between",
        border: "1px solid var(--hairline)", borderRadius: 8,
        background: "var(--surface)", padding: "8px 10px",
      }}>
        <button aria-label="Previous step" style={{
          appearance: "none", border: 0, background: "transparent",
          color: "var(--text-2)", padding: 6, cursor: "default",
          fontFamily: "var(--font-mono)", fontSize: 14,
        }}>‹</button>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 8,
          fontFamily: "var(--font-mono)", fontSize: 11,
          letterSpacing: "0.08em", textTransform: "uppercase",
        }}>
          <span style={{ color: "var(--text-3)" }}>{active + 1}/{phases.length}</span>
          <span style={{ color: "var(--primary)", fontWeight: 600 }}>{phases[active]}</span>
        </span>
        <button aria-label="Next step" disabled style={{
          appearance: "none", border: 0, background: "transparent",
          color: "var(--text-3)", padding: 6, opacity: 0.4, cursor: "default",
          fontFamily: "var(--font-mono)", fontSize: 14,
        }}>›</button>
      </div>
    </div>
  );
}

// ─── Shell ─────────────────────────────────────────────────────────────────
// Wraps any screen with the BL token surface + flex column layout.
// Children render inside; consumers add their own <main> or sticky strips.
function BLShell({ children, screenLabel, ...rest }) {
  return (
    <div data-screen-label={screenLabel} style={{
      ...BL_TOKENS,
      minHeight: "100vh",
      background: "var(--surface-2)",
      color: "var(--text)",
      fontFamily: "var(--font-sans)",
      display: "flex", flexDirection: "column",
      ...rest.style,
    }}>
      {children}
    </div>
  );
}

// Make available to other Babel scripts.
Object.assign(window, {
  BL_TOKENS, BL_NAV_COPY,
  Wordmark, LangSwitch, UserMenu, TopBar,
  StepIndicator, BLShell,
});
