// candidate-selection.jsx
// BUILDLoop — second screen: pick a candidate when the resolver returns >1 match.
// Inherits visual language from address-intake.jsx (top bar, step indicator, tokens).

const { useState, useEffect, useRef, useMemo } = React;

// ─── Translations ────────────────────────────────────────────────────────────
const COPY = {
  en: {
    nav_help: "Help", nav_signed_in_as: "Signed in as",
    nav_account: "Account", nav_sign_out: "Sign out",

    h1_amb: "We found a few possible matches",
    sub_amb: "Pick the building you mean. We'll fetch its register record next.",
    h1_unr: "We couldn't match this address",
    sub_unr: "The address didn't match anything in the Estonian construction register. This usually means a typo, a very new building, or an unusual format. Try one of these:",
    h1_res: "We found a few possible matches",
    sub_res: "Checking the register…",

    primary_chip: "Primary match",
    aliases: "Also known as",
    confidence: "confidence",
    none_match: "None of these — edit address",

    sugg_1: "Use the street address only (no apartment number)",
    sugg_2: "Try a nearby landmark or postal code",
    sugg_3: "Enter the EHR code directly",
    edit_addr: "Edit address",
    enter_ehr: "Enter EHR code",

    submitted: "You searched for",
  },
  et: {
    nav_help: "Abi", nav_signed_in_as: "Sisse logitud",
    nav_account: "Konto", nav_sign_out: "Logi välja",

    h1_amb: "Leidsime mitu võimalikku vastet",
    sub_amb: "Vali, milline hoone sa silmas pead. Järgmiseks toome registrikande.",
    h1_unr: "Seda aadressi ei õnnestunud tuvastada",
    sub_unr: "Aadress ei vastanud ühelegi kandele ehitisregistris. Tavaliselt on põhjuseks kirjaviga, väga uus hoone või ebatavaline vorming. Proovi üht neist:",
    h1_res: "Leidsime mitu võimalikku vastet",
    sub_res: "Otsin registrist…",

    primary_chip: "Põhivaste",
    aliases: "Tuntud ka kui",
    confidence: "kindlus",
    none_match: "Ükski ei sobi — muuda aadressi",

    sugg_1: "Kasuta ainult tänavaaadressi (ilma korterinumbrita)",
    sugg_2: "Proovi lähedalasuvat orientiiri või sihtnumbrit",
    sugg_3: "Sisesta otse EHR-kood",
    edit_addr: "Muuda aadressi",
    enter_ehr: "Sisesta EHR-kood",

    submitted: "Otsisid",
  },
};

// Realistic candidate dataset. Includes a corner-building example with aliases.
const CANDIDATES_FULL = [
  {
    id: "c1",
    address: "Lai tn 1 // Nunne tn 4, 10133 Tallinn",
    aliases: ["Lai tn 1", "Nunne tn 4"],
    ehr: "101035685",
    confidence: 92,
    primary: true,
  },
  {
    id: "c2",
    address: "Lai tn 1a, 10133 Tallinn",
    aliases: [],
    ehr: "120143580",
    confidence: 78,
    primary: false,
  },
  {
    id: "c3",
    address: "Laia tn 1, 10133 Tallinn",
    aliases: [],
    ehr: "104027311",
    confidence: 64,
    primary: false,
  },
  {
    id: "c4",
    address: "Lai tn 11, 10133 Tallinn",
    aliases: [],
    ehr: "104015902",
    confidence: 51,
    primary: false,
  },
  {
    id: "c5",
    address: "Lai tn 1, 10711 Pärnu",
    aliases: [],
    ehr: "121089430",
    confidence: 38,
    primary: false,
  },
];

// ─── Atoms (mirrors address-intake.jsx vocabulary) ──────────────────────────
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

function MenuItem({ children, danger }) {
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

function UserMenu({ t }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
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
        }}>
          <div style={{ padding: "8px 10px", color: "var(--text-3)", fontSize: 11,
            letterSpacing: "0.03em", textTransform: "uppercase",
          }}>{t.nav_signed_in_as}</div>
          <div style={{ padding: "0 10px 8px", color: "var(--text)", fontWeight: 500 }}>
            mart.kask@reaalehitus.ee
          </div>
          <div style={{ height: 1, background: "var(--hairline)", margin: "4px 0" }} />
          <MenuItem>{t.nav_account}</MenuItem>
          <MenuItem>{t.nav_help}</MenuItem>
          <div style={{ height: 1, background: "var(--hairline)", margin: "4px 0" }} />
          <MenuItem danger>{t.nav_sign_out}</MenuItem>
        </div>
      )}
    </div>
  );
}

// ─── Step indicator ─────────────────────────────────────────────────────────
// Phase 2 (Resolution) is active. Phase 1 (Address) is completed (checkmark).
function StepIndicator({ lang }) {
  const phases = lang === "et"
    ? ["Aadress", "Tuvastus", "Mustand", "Avaldatud"]
    : ["Address", "Resolution", "Draft", "Published"];
  const active = 1;
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
              fontWeight: i === active ? 600 : isDone(i) ? 500 : 500,
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

// ─── Confidence bar ─────────────────────────────────────────────────────────
function ConfidenceMeter({ value, t }) {
  // Restrained: uses primary green for high, text-2 for mid, text-3 for low.
  // No red — this isn't an error signal.
  const tone = value >= 80 ? "var(--primary)" : value >= 60 ? "var(--text-2)" : "var(--text-3)";
  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 5,
      minWidth: 96,
    }}>
      <div style={{
        fontFamily: "var(--font-mono)", fontSize: 11,
        color: "var(--text-2)", letterSpacing: "0.02em",
        whiteSpace: "nowrap",
      }}>
        <span style={{ fontWeight: 600, color: "var(--text)" }}>{value}%</span>
        <span style={{ color: "var(--text-3)", marginLeft: 6 }}>{t.confidence}</span>
      </div>
      <div style={{
        width: 96, height: 3, borderRadius: 2,
        background: "var(--surface-2)", overflow: "hidden",
        border: "1px solid var(--hairline)",
      }}>
        <div style={{
          width: `${value}%`, height: "100%",
          background: tone,
          transition: "width .3s ease",
        }} />
      </div>
    </div>
  );
}

// ─── Candidate card ─────────────────────────────────────────────────────────
function CandidateCard({ c, t, onPick }) {
  const [hover, setHover] = useState(false);
  return (
    <button
      type="button"
      onClick={() => onPick?.(c)}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        appearance: "none",
        textAlign: "left",
        width: "100%",
        background: "var(--surface)",
        border: `1px solid ${hover ? "var(--primary)" : "var(--hairline-strong)"}`,
        borderRadius: 10,
        padding: "16px 18px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        gap: 20,
        cursor: "default",
        fontFamily: "var(--font-sans)",
        color: "var(--text)",
        position: "relative",
        transition: "border-color .12s ease, box-shadow .12s ease",
        boxShadow: hover ? "0 0 0 3px rgba(31, 77, 58, 0.08)" : "none",
      }}
    >
      {c.primary && (
        <span style={{
          position: "absolute", top: 12, right: 12,
          background: "var(--accent)", color: "var(--primary)",
          padding: "3px 9px", borderRadius: 999,
          fontFamily: "var(--font-mono)", fontSize: 10,
          fontWeight: 600, letterSpacing: "0.04em",
          textTransform: "uppercase",
        }}>{t.primary_chip}</span>
      )}

      <div style={{
        display: "flex", flexDirection: "column", gap: 4,
        minWidth: 0, flex: 1,
      }}>
        <div style={{
          fontSize: 17, fontWeight: 600, letterSpacing: "-0.01em",
          color: "var(--text)", lineHeight: 1.3,
          paddingRight: c.primary ? 110 : 0,
        }}>{c.address}</div>
        <div style={{
          fontFamily: "var(--font-mono)", fontSize: 12,
          color: "var(--text-3)", letterSpacing: "0.02em",
        }}>
          EHR <span style={{ color: "var(--text-2)", fontWeight: 500 }}>{c.ehr}</span>
        </div>
        {c.aliases?.length > 0 && (
          <div style={{
            fontSize: 12.5, color: "var(--text-2)",
            marginTop: 4, lineHeight: 1.5,
          }}>
            <span style={{
              color: "var(--text-3)", fontFamily: "var(--font-mono)",
              fontSize: 11, letterSpacing: "0.04em",
              textTransform: "uppercase", fontWeight: 600, marginRight: 8,
            }}>{t.aliases}:</span>
            {c.aliases.map((a, i) => (
              <React.Fragment key={a}>
                {i > 0 && <span style={{ color: "var(--text-3)", margin: "0 6px" }}>·</span>}
                <span>{a}</span>
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      <div style={{ marginTop: c.primary ? 30 : 0, flexShrink: 0 }}>
        <ConfidenceMeter value={c.confidence} t={t} />
      </div>
    </button>
  );
}

// ─── Skeleton ──────────────────────────────────────────────────────────────
function CandidateSkeleton() {
  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--hairline)",
      borderRadius: 10,
      padding: "16px 18px",
      display: "grid",
      gridTemplateColumns: "1fr auto",
      columnGap: 20,
      alignItems: "start",
    }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <Shimmer w="62%" h={18} />
        <Shimmer w="32%" h={12} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
        <Shimmer w={84} h={11} />
        <Shimmer w={96} h={3} />
      </div>
    </div>
  );
}

function Shimmer({ w, h }) {
  return (
    <div style={{
      width: typeof w === "number" ? w : w,
      height: h,
      borderRadius: 4,
      background: "linear-gradient(90deg, var(--surface-2) 0%, rgba(13,31,23,0.05) 50%, var(--surface-2) 100%)",
      backgroundSize: "200% 100%",
      animation: "bl-shimmer 1.4s ease-in-out infinite",
    }} />
  );
}

// ─── Empty state ───────────────────────────────────────────────────────────
function NeutralIcon() {
  // Square-frame placeholder, no illustration. Just a hairline box with a dot.
  return (
    <div aria-hidden style={{
      width: 40, height: 40, borderRadius: 8,
      border: "1px solid var(--hairline-strong)",
      background: "var(--surface-2)",
      display: "inline-flex", alignItems: "center", justifyContent: "center",
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: "50%",
        background: "var(--text-3)",
      }} />
    </div>
  );
}

function UnresolvedBlock({ t, onEditAddress, onEnterEhr }) {
  return (
    <div style={{
      border: "1px solid var(--hairline)",
      borderRadius: 10,
      background: "var(--surface)",
      padding: "24px 24px 22px",
      display: "flex",
      flexDirection: "column",
      gap: 16,
    }}>
      <ul style={{
        listStyle: "none",
        margin: 0,
        padding: 0,
        display: "flex",
        flexDirection: "column",
        gap: 0,
        border: "1px solid var(--hairline)",
        borderRadius: 8,
        overflow: "hidden",
      }}>
        {[t.sugg_1, t.sugg_2, t.sugg_3].map((s, i) => (
          <li key={i} style={{
            padding: "12px 14px",
            borderTop: i > 0 ? "1px solid var(--hairline)" : "none",
            display: "flex",
            alignItems: "center",
            gap: 12,
            fontFamily: "var(--font-sans)",
            fontSize: 14,
            color: "var(--text)",
            background: "var(--surface)",
          }}>
            <span style={{
              fontFamily: "var(--font-mono)", fontSize: 11,
              color: "var(--text-3)", letterSpacing: "0.04em", fontWeight: 600,
              minWidth: 18,
            }}>{String(i + 1).padStart(2, "0")}</span>
            <span>{s}</span>
          </li>
        ))}
      </ul>
      <div style={{ display: "flex", gap: 10, marginTop: 4, flexWrap: "wrap" }}>
        <button onClick={onEditAddress} style={{
          appearance: "none", border: 0,
          background: "var(--primary)", color: "#fff",
          height: 42, padding: "0 18px", borderRadius: 8,
          fontFamily: "var(--font-sans)", fontSize: 14, fontWeight: 600,
          letterSpacing: "-0.005em", cursor: "default",
        }}>{t.edit_addr}</button>
        <button onClick={onEnterEhr} style={{
          appearance: "none", border: "1px solid var(--hairline-strong)",
          background: "var(--surface)", color: "var(--text)",
          height: 42, padding: "0 18px", borderRadius: 8,
          fontFamily: "var(--font-sans)", fontSize: 14, fontWeight: 600,
          letterSpacing: "-0.005em", cursor: "default",
        }}>{t.enter_ehr}</button>
      </div>
    </div>
  );
}

// ─── Main ──────────────────────────────────────────────────────────────────
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "state": "ambiguous",
  "lang": "en",
  "candidateCount": 3
}/*EDITMODE-END*/;

const SUBMITTED_QUERY = "Lai 1, 10133 Tallinn";

function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const { state, lang, candidateCount } = tweaks;
  const t = COPY[lang] || COPY.en;

  const candidates = CANDIDATES_FULL.slice(0, candidateCount);

  const heading = state === "unresolved" ? t.h1_unr : state === "resolving" ? t.h1_res : t.h1_amb;
  const subline = state === "unresolved" ? t.sub_unr : state === "resolving" ? t.sub_res : t.sub_amb;

  return (
    <div data-screen-label="02 Resolution — Candidate selection" style={{
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
      minHeight: "100vh",
      background: "var(--surface-2)",
      color: "var(--text)",
      fontFamily: "var(--font-sans)",
      display: "flex", flexDirection: "column",
    }}>
      {/* Top bar — same vocabulary as intake */}
      <header style={{
        height: 56, borderBottom: "1px solid var(--hairline)",
        background: "var(--surface)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "0 28px", position: "sticky", top: 0, zIndex: 10,
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
          <LangSwitch lang={lang} onChange={(v) => setTweak("lang", v)} />
          <span style={{ width: 1, height: 22, background: "var(--hairline)" }} />
          <UserMenu t={t} />
        </div>
      </header>

      <main style={{
        flex: 1, display: "flex", justifyContent: "center",
        padding: "56px 24px 96px",
      }}>
        <div style={{
          width: "100%", maxWidth: 720,
          display: "flex", flexDirection: "column", gap: 28,
        }}>
          <StepIndicator lang={lang} />

          {/* Submitted query echo — small breadcrumb above heading */}
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            fontFamily: "var(--font-sans)", fontSize: 13,
            color: "var(--text-2)",
          }}>
            <span style={{
              fontFamily: "var(--font-mono)", fontSize: 11,
              color: "var(--text-3)", letterSpacing: "0.06em",
              textTransform: "uppercase", fontWeight: 600,
            }}>{t.submitted}</span>
            <span style={{
              fontFamily: "var(--font-mono)", fontSize: 13,
              color: "var(--text)", fontWeight: 500,
              padding: "3px 8px",
              background: "var(--surface)",
              border: "1px solid var(--hairline)",
              borderRadius: 5,
            }}>{SUBMITTED_QUERY}</span>
          </div>

          {/* Heading */}
          <div>
            <h1 style={{
              margin: 0, fontSize: 30, lineHeight: 1.18,
              letterSpacing: "-0.02em", fontWeight: 600,
              color: "var(--text)", textWrap: "balance",
            }}>{heading}</h1>
            <p style={{
              margin: "12px 0 0", fontSize: 15, lineHeight: 1.55,
              color: "var(--text-2)", maxWidth: 580, textWrap: "pretty",
            }}>{subline}</p>
          </div>

          {/* State-specific body */}
          {state === "ambiguous" && (
            <>
              <ul style={{
                listStyle: "none", margin: 0, padding: 0,
                display: "flex", flexDirection: "column", gap: 12,
              }}>
                {candidates.map((c) => (
                  <li key={c.id}>
                    <CandidateCard c={c} t={t} onPick={() => {}} />
                  </li>
                ))}
              </ul>
              <div style={{ marginTop: 4 }}>
                <a href="#" style={{
                  fontFamily: "var(--font-sans)", fontSize: 13,
                  color: "var(--text-2)",
                  textDecoration: "underline", textUnderlineOffset: 3,
                  textDecorationColor: "var(--hairline-strong)",
                }}>{t.none_match}</a>
              </div>
            </>
          )}

          {state === "resolving" && (
            <ul style={{
              listStyle: "none", margin: 0, padding: 0,
              display: "flex", flexDirection: "column", gap: 12,
            }}>
              {[0, 1, 2].map((i) => (
                <li key={i}><CandidateSkeleton /></li>
              ))}
            </ul>
          )}

          {state === "unresolved" && (
            <UnresolvedBlock
              t={t}
              onEditAddress={() => {}}
              onEnterEhr={() => {}}
            />
          )}
        </div>
      </main>

      <TweaksPanel>
        <TweakSection label={lang === "et" ? "Olek" : "State"} />
        <TweakRadio
          label={lang === "et" ? "Vaade" : "View"}
          value={state}
          options={["ambiguous", "unresolved", "resolving"]}
          onChange={(v) => setTweak("state", v)}
        />
        <TweakSection label={lang === "et" ? "Andmed" : "Data"} />
        <TweakRadio
          label={lang === "et" ? "Vasted" : "Candidates"}
          value={String(candidateCount)}
          options={["2", "3", "5"]}
          onChange={(v) => setTweak("candidateCount", parseInt(v, 10))}
        />
        <TweakSection label={lang === "et" ? "Esitlus" : "Presentation"} />
        <TweakRadio
          label={lang === "et" ? "Keel" : "Language"}
          value={lang}
          options={["et", "en"]}
          onChange={(v) => setTweak("lang", v)}
        />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
