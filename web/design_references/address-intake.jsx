// address-intake.jsx
// BUILDLoop — first screen after sign-in: address intake.
// All copy in two languages, tokens straight from web/BRAND.md.

const { useState, useEffect, useRef, useMemo } = React;

// ─── Translations ────────────────────────────────────────────────────────────
const COPY = {
  en: {
    nav_help: "Help",
    nav_signed_in_as: "Signed in as",
    nav_account: "Account",
    nav_sign_out: "Sign out",
    h1: "Create a building passport",
    sub: "Enter the address of the building you want to assess. We'll resolve it against the Estonian construction register (EHR) and prepare a draft passport for review.",
    addr_label: "Building address",
    addr_hint: "Currently supports Estonian addresses.",
    title_label: "Project title",
    title_optional: "Optional",
    title_hint: "Used internally — e.g. \"Pelguranna kvartal — phase 2\".",
    ehr_link_open: "I already have an EHR code",
    ehr_link_close: "Use an address instead",
    ehr_label: "EHR code",
    ehr_hint: "7–9 digit code from the Estonian construction register.",
    cta_idle: "Find building",
    cta_busy: "Finding building…",
    cta_retry: "Try again",
    cta_found: "Found",
    explainer_title: "What happens next",
    step1_h: "Enter address",
    step1_p: "Any Estonian street address. Apartment number isn't needed — passports are issued per building.",
    step2_h: "We resolve it to a building",
    step2_p: "BUILDLoop matches your address to its EHR code and pulls the public construction register record.",
    step3_h: "Review and publish",
    step3_p: "You review the draft, attach photos and condition notes, then publish a versioned passport.",
    err_title: "We couldn't find that address in the register",
    err_body: "Check the format, or try a nearby landmark.",
    err_action: "Edit address",
    err_help: "Need help?",
    legal: "BUILDLoop is operated by TalTech. Material passports issued through this tool are versioned, evidence-backed records.",
  },
  et: {
    nav_help: "Abi",
    nav_signed_in_as: "Sisse logitud",
    nav_account: "Konto",
    nav_sign_out: "Logi välja",
    h1: "Loo hoone materjalipass",
    sub: "Sisesta hoone aadress, mida soovid hinnata. Seome selle ehitisregistri (EHR) kandega ja koostame ülevaatamiseks passi mustandi.",
    addr_label: "Hoone aadress",
    addr_hint: "Toetab Eesti aadresse.",
    title_label: "Projekti nimi",
    title_optional: "Valikuline",
    title_hint: "Sisemiseks kasutamiseks — nt „Pelguranna kvartal — II etapp\".",
    ehr_link_open: "Mul on juba EHR-kood",
    ehr_link_close: "Kasuta hoopis aadressi",
    ehr_label: "EHR-kood",
    ehr_hint: "7–9-kohaline ehitisregistri kood.",
    cta_idle: "Leia hoone",
    cta_busy: "Otsin hoonet…",
    cta_retry: "Proovi uuesti",
    cta_found: "Leitud",
    explainer_title: "Mis edasi juhtub",
    step1_h: "Sisesta aadress",
    step1_p: "Sobib iga Eesti aadress. Korterinumbrit pole vaja — pass koostatakse hoone kohta.",
    step2_h: "Seome hoonega",
    step2_p: "BUILDLoop leiab aadressile vastava EHR-koodi ja võtab avaliku registriinfo.",
    step3_h: "Vaata üle ja avalda",
    step3_p: "Vaatad mustandi üle, lisad fotod ja seisundimärkmed ning avaldad versioonitud passi.",
    err_title: "Seda aadressi ei leitud registrist",
    err_body: "Kontrolli vormingut või proovi lähedalasuva orientiiriga.",
    err_action: "Muuda aadressi",
    err_help: "Vajad abi?",
    legal: "BUILDLoopi haldab TalTech. Selle tööriista kaudu väljastatud materjalipassid on versioonitud, tõenditega kannete kogumikud.",
  },
};

// Plausible Tallinn addresses for placeholder rotation
const SAMPLE_ADDRESSES = [
  "Lai 1, 10133 Tallinn",
  "Roosikrantsi 11, 10119 Tallinn",
  "Pärnu mnt 105, 11312 Tallinn",
  "Tartu mnt 80, 10112 Tallinn",
  "Telliskivi 60a, 10412 Tallinn",
];

// ─── Atoms ───────────────────────────────────────────────────────────────────
function Wordmark({ size = 16 }) {
  return (
    <span style={{
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: size,
      letterSpacing: "-0.01em",
      color: "var(--text)",
      display: "inline-flex",
      alignItems: "baseline",
      gap: 0,
    }}>
      <span>BUILD</span>
      <span style={{
        color: "var(--primary)",
        fontWeight: 700,
      }}>Loop</span>
    </span>
  );
}

function LangSwitch({ lang, onChange }) {
  return (
    <div role="group" aria-label="Language" style={{
      display: "inline-flex",
      border: "1px solid var(--hairline)",
      borderRadius: 6,
      overflow: "hidden",
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      letterSpacing: "0.04em",
    }}>
      {["et", "en"].map((code) => {
        const active = lang === code;
        return (
          <button
            key={code}
            onClick={() => onChange(code)}
            aria-pressed={active}
            style={{
              appearance: "none",
              border: 0,
              padding: "5px 9px",
              minWidth: 28,
              background: active ? "var(--text)" : "transparent",
              color: active ? "var(--surface)" : "var(--text-2)",
              cursor: "default",
              fontFamily: "inherit",
              fontSize: "inherit",
              letterSpacing: "inherit",
              textTransform: "uppercase",
              fontWeight: 600,
            }}
          >
            {code}
          </button>
        );
      })}
    </div>
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
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        style={{
          appearance: "none",
          border: "1px solid var(--hairline)",
          background: "var(--surface)",
          color: "var(--text)",
          height: 30,
          padding: "0 10px 0 6px",
          borderRadius: 6,
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          fontFamily: "var(--font-sans)",
          fontSize: 13,
          cursor: "default",
        }}
      >
        <span aria-hidden style={{
          width: 22, height: 22, borderRadius: "50%",
          background: "var(--accent)", color: "var(--primary)",
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          fontSize: 11, fontWeight: 600, letterSpacing: "0.02em",
        }}>MK</span>
        <span style={{ color: "var(--text-2)" }}>Mart Kask</span>
        <span aria-hidden style={{
          color: "var(--text-3)", fontSize: 9, marginLeft: 2, transform: "translateY(1px)",
        }}>▾</span>
      </button>
      {open && (
        <div style={{
          position: "absolute",
          top: "calc(100% + 6px)",
          right: 0,
          minWidth: 220,
          background: "var(--surface)",
          border: "1px solid var(--hairline)",
          borderRadius: 8,
          boxShadow: "0 8px 24px rgba(13,31,23,0.08)",
          padding: 6,
          fontFamily: "var(--font-sans)",
          fontSize: 13,
        }}>
          <div style={{
            padding: "8px 10px",
            color: "var(--text-3)",
            fontSize: 11,
            letterSpacing: "0.03em",
            textTransform: "uppercase",
          }}>{t.nav_signed_in_as}</div>
          <div style={{
            padding: "0 10px 8px",
            color: "var(--text)",
            fontWeight: 500,
          }}>mart.kask@reaalehitus.ee</div>
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

function MenuItem({ children, danger = false }) {
  return (
    <button style={{
      appearance: "none",
      border: 0,
      background: "transparent",
      width: "100%",
      textAlign: "left",
      padding: "7px 10px",
      borderRadius: 5,
      color: danger ? "#7a2a2a" : "var(--text)",
      fontFamily: "inherit",
      fontSize: "inherit",
      cursor: "default",
    }}
    onMouseEnter={(e) => e.currentTarget.style.background = "var(--surface-2)"}
    onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
    >{children}</button>
  );
}

// ─── Step indicator ────────────────────────────────────────────────────────
// Full 4-step bar on desktop; condensed "1/4 ADDRESS" with chevrons on mobile.
function StepIndicator({ lang }) {
  const phases = lang === "et"
    ? ["Aadress", "Tuvastus", "Mustand", "Avaldatud"]
    : ["Address", "Resolution", "Draft", "Published"];
  const active = 0;
  return (
    <div>
      {/* Desktop full bar */}
      <div className="bl-stepbar-full" style={{
        display: "flex", alignItems: "center", gap: 10,
        fontFamily: "var(--font-mono)", fontSize: 11,
        color: "var(--text-3)", letterSpacing: "0.06em", textTransform: "uppercase",
      }}>
        {phases.map((p, i) => (
          <React.Fragment key={p}>
            {i > 0 && <span aria-hidden style={{ color: "var(--hairline-strong)" }}>───</span>}
            <span style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              color: i === active ? "var(--primary)" : "var(--text-3)",
              fontWeight: i === active ? 600 : 500,
            }}>
              {i === active ? (
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
      {/* Mobile condensed */}
      <div className="bl-stepbar-mini" style={{
        display: "none",
        alignItems: "center", justifyContent: "space-between",
        border: "1px solid var(--hairline)",
        borderRadius: 8,
        background: "var(--surface)",
        padding: "8px 10px",
      }}>
        <button aria-label="Previous step" disabled style={{
          appearance: "none", border: 0, background: "transparent",
          color: "var(--text-3)", padding: 6, opacity: 0.4, cursor: "default",
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

// Subtle dotted spinner — no SVG complexity, just CSS rotation
function Spinner() {
  return (
    <span aria-hidden style={{
      display: "inline-block",
      width: 14, height: 14,
      borderRadius: "50%",
      border: "1.5px solid currentColor",
      borderRightColor: "transparent",
      borderBottomColor: "transparent",
      opacity: 0.85,
      animation: "bl-spin 0.7s linear infinite",
    }} />
  );
}

// ─── Field ──────────────────────────────────────────────────────────────────
function Field({
  id, label, optional, hint, value, onChange, placeholder,
  readOnly, error, mono, autoFocus, density,
}) {
  const inputH = density === "compact" ? 40 : 46;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <label htmlFor={id} style={{
        display: "flex",
        alignItems: "baseline",
        justifyContent: "space-between",
        fontFamily: "var(--font-sans)",
        fontSize: 13,
        fontWeight: 500,
        color: "var(--text)",
        letterSpacing: "-0.005em",
      }}>
        <span>{label}</span>
        {optional && (
          <span style={{
            fontSize: 11,
            fontWeight: 400,
            color: "var(--text-3)",
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.02em",
          }}>{optional}</span>
        )}
      </label>
      <input
        id={id}
        type="text"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        readOnly={readOnly}
        autoFocus={autoFocus}
        aria-invalid={error || undefined}
        style={{
          appearance: "none",
          height: inputH,
          padding: "0 14px",
          borderRadius: 8,
          border: `1px solid ${error ? "var(--danger)" : "var(--hairline-strong)"}`,
          background: readOnly ? "var(--surface-2)" : "var(--surface)",
          color: "var(--text)",
          fontFamily: mono ? "var(--font-mono)" : "var(--font-sans)",
          fontSize: 15,
          letterSpacing: mono ? "0.005em" : "-0.005em",
          outline: "none",
          transition: "border-color .12s ease, background .12s ease",
          width: "100%",
          boxSizing: "border-box",
        }}
        onFocus={(e) => { if (!readOnly && !error) e.currentTarget.style.borderColor = "var(--primary)"; }}
        onBlur={(e) => { if (!error) e.currentTarget.style.borderColor = "var(--hairline-strong)"; }}
      />
      {hint && (
        <p style={{
          margin: 0,
          fontSize: 12,
          color: "var(--text-3)",
          fontFamily: "var(--font-sans)",
          lineHeight: 1.5,
        }}>{hint}</p>
      )}
    </div>
  );
}

// ─── Error block ────────────────────────────────────────────────────────────
// Neutral tone — single clear action + Need help?
function ErrorBlock({ t, onDismiss }) {
  return (
    <div role="alert" style={{
      border: "1px solid var(--hairline-strong)",
      background: "var(--surface)",
      borderLeft: "3px solid var(--text)",
      borderRadius: 6,
      padding: "14px 16px",
      display: "flex",
      flexDirection: "column",
      gap: 8,
      fontFamily: "var(--font-sans)",
    }}>
      <div style={{
        fontWeight: 600,
        color: "var(--text)",
        fontSize: 14,
        letterSpacing: "-0.005em",
      }}>{t.err_title}</div>
      <p style={{
        margin: 0,
        color: "var(--text-2)",
        fontSize: 13,
        lineHeight: 1.5,
      }}>{t.err_body}</p>
      <div style={{ display: "flex", gap: 14, alignItems: "center", marginTop: 2 }}>
        <button onClick={onDismiss} style={{
          appearance: "none",
          border: 0,
          background: "transparent",
          color: "var(--primary)",
          fontFamily: "inherit",
          fontSize: 13,
          fontWeight: 600,
          padding: 0,
          cursor: "default",
          textDecoration: "underline",
          textUnderlineOffset: 3,
          textDecorationColor: "var(--accent)",
        }}>{t.err_action}</button>
        <span aria-hidden style={{ color: "var(--text-3)", fontSize: 13 }}>·</span>
        <a href="#" style={{
          color: "var(--text-3)",
          fontSize: 13,
          textDecoration: "underline",
          textUnderlineOffset: 3,
          textDecorationColor: "var(--hairline-strong)",
        }}>{t.err_help}</a>
      </div>
    </div>
  );
}

// ─── Found confirmation chip ───────────────────────────────────────────────
function FoundChip({ t, address }) {
  return (
    <div role="status" aria-live="polite" style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 8,
      padding: "7px 12px 7px 10px",
      borderRadius: 999,
      background: "var(--accent)",
      color: "var(--primary)",
      fontFamily: "var(--font-sans)",
      fontSize: 13,
      fontWeight: 500,
      letterSpacing: "-0.003em",
      animation: "bl-fade-in .2s ease-out",
      maxWidth: "100%",
      width: "fit-content",
    }}>
      <span aria-hidden style={{
        width: 14, height: 14, borderRadius: "50%",
        background: "var(--primary)", color: "#fff",
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        fontSize: 9, fontWeight: 700,
      }}>✓</span>
      <span style={{ fontWeight: 600 }}>{t.cta_found}</span>
      <span style={{
        fontFamily: "var(--font-mono)",
        opacity: 0.8,
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}>{address}</span>
    </div>
  );
}

// ─── Explainer ──────────────────────────────────────────────────────────────
// 3 cards mapping to phases 1–3 (Address / Resolution / Draft). Published is the
// end state, not a step the user takes — intentionally omitted.
function Explainer({ t, dim, lang }) {
  const phases = [
    { n: "01", phase: lang === "et" ? "Aadress" : "Address",      h: t.step1_h, p: t.step1_p },
    { n: "02", phase: lang === "et" ? "Tuvastus" : "Resolution",   h: t.step2_h, p: t.step2_p },
    { n: "03", phase: lang === "et" ? "Mustand" : "Draft",         h: t.step3_h, p: t.step3_p },
  ];
  return (
    <section aria-labelledby="explainer-h" style={{
      opacity: dim ? 0.55 : 1,
      filter: dim ? "saturate(0.5)" : "none",
      transition: "opacity .25s ease, filter .25s ease",
      pointerEvents: dim ? "none" : "auto",
    }}>
      <h2 id="explainer-h" style={{
        margin: "0 0 14px",
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color: "var(--text-3)",
        fontFamily: "var(--font-mono)",
      }}>{t.explainer_title}</h2>
      <ol className="bl-explainer-grid" style={{
        listStyle: "none",
        margin: 0,
        padding: 0,
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 0,
        border: "1px solid var(--hairline)",
        borderRadius: 8,
        overflow: "hidden",
        background: "var(--surface)",
      }}>
        {phases.map((s, i) => (
          <li key={s.n} className="bl-explainer-cell" data-last={i === phases.length - 1 || undefined} style={{
            padding: "16px 18px 18px",
            borderRight: i < phases.length - 1 ? "1px solid var(--hairline)" : "none",
            display: "flex",
            flexDirection: "column",
            gap: 6,
            position: "relative",
          }}>
            <div style={{
              display: "flex", alignItems: "baseline", gap: 8,
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              letterSpacing: "0.04em",
              fontWeight: 600,
            }}>
              <span style={{ color: "var(--primary)" }}>{s.n}</span>
              <span style={{ color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{s.phase}</span>
            </div>
            <div style={{
              fontFamily: "var(--font-sans)",
              fontSize: 14,
              fontWeight: 600,
              color: "var(--text)",
              letterSpacing: "-0.005em",
              marginTop: 2,
            }}>{s.h}</div>
            <p style={{
              margin: 0,
              fontFamily: "var(--font-sans)",
              fontSize: 12.5,
              lineHeight: 1.5,
              color: "var(--text-2)",
            }}>{s.p}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

// ─── Resolved card (preview of next step) ──────────────────────────────────
function ResolvedCard({ address, lang }) {
  return (
    <div style={{
      border: "1px solid var(--hairline-strong)",
      borderRadius: 8,
      background: "var(--surface)",
      padding: "18px 20px",
      display: "flex",
      flexDirection: "column",
      gap: 14,
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        color: "var(--primary)",
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        fontWeight: 600,
      }}>
        <span style={{
          width: 6, height: 6, borderRadius: "50%",
          background: "var(--primary)",
          display: "inline-block",
        }} />
        {lang === "et" ? "Aadress tuvastatud" : "Address resolved"}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <Detail
          label={lang === "et" ? "Aadress" : "Address"}
          value={address}
        />
        <Detail
          label={lang === "et" ? "EHR-kood" : "EHR code"}
          value="120143580"
          mono
        />
        <Detail
          label={lang === "et" ? "Hoone tüüp" : "Building type"}
          value={lang === "et" ? "Korterelamu (3 korrust)" : "Apartment building (3 storeys)"}
        />
        <Detail
          label={lang === "et" ? "Ehitusaasta" : "Year built"}
          value="1936"
          mono
        />
      </div>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        paddingTop: 14, borderTop: "1px solid var(--hairline)",
      }}>
        <span style={{
          fontFamily: "var(--font-sans)", fontSize: 12.5, color: "var(--text-2)",
        }}>
          {lang === "et"
            ? "Järgmine: kontrolli kannet ja koosta mustand."
            : "Next: confirm the record and draft the passport."}
        </span>
        <button style={{
          appearance: "none",
          border: 0,
          background: "var(--primary)",
          color: "#fff",
          height: 36,
          padding: "0 16px",
          borderRadius: 7,
          fontFamily: "var(--font-sans)",
          fontSize: 13,
          fontWeight: 600,
          cursor: "default",
          letterSpacing: "-0.005em",
        }}>
          {lang === "et" ? "Jätka" : "Continue"} →
        </button>
      </div>
    </div>
  );
}

function Detail({ label, value, mono }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <span style={{
        fontFamily: "var(--font-mono)", fontSize: 10.5,
        color: "var(--text-3)", letterSpacing: "0.06em", textTransform: "uppercase",
        fontWeight: 600,
      }}>{label}</span>
      <span style={{
        fontFamily: mono ? "var(--font-mono)" : "var(--font-sans)",
        fontSize: 14, color: "var(--text)", fontWeight: mono ? 500 : 500,
      }}>{value}</span>
    </div>
  );
}

// ─── Main ───────────────────────────────────────────────────────────────────
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "state": "idle",
  "lang": "en",
  "density": "comfortable"
}/*EDITMODE-END*/;

function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const { state, lang, density } = tweaks;
  const t = COPY[lang] || COPY.en;

  const [address, setAddress] = useState("");
  const [project, setProject] = useState("");
  const [ehrOpen, setEhrOpen] = useState(false);
  const [ehr, setEhr] = useState("");
  const placeholder = useMemo(() => SAMPLE_ADDRESSES[0], []);

  // When user manually drives the form, simulate a real submit.
  // Tweaks override state directly so designers can inspect each variant.
  const submit = (e) => {
    e?.preventDefault?.();
    if (state === "submitting") return;
    setTweak("state", "submitting");
    window.setTimeout(() => {
      const value = ehrOpen ? ehr : address;
      const ok = ehrOpen
        ? /^\d{7,9}$/.test(value.trim())
        : value.trim().length > 4 && /\d{4,5}/.test(value);
      setTweak("state", ok ? "resolved" : "error");
      // Auto-clear the resolved state back to idle after the chip shows for a moment.
      // (Real app would route to the next screen — chip is the visible bridge.)
      if (ok) {
        window.setTimeout(() => {
          // Only clear if still on resolved (user hasn't navigated tweaks)
          setTweak("state", "idle");
        }, 1400);
      }
    }, 1100);
  };

  const reset = () => {
    setTweak("state", "idle");
  };

  const isBusy = state === "submitting";
  const isError = state === "error";
  const isResolved = state === "resolved";

  // What address to show in the chip — whatever was typed, falling back to placeholder
  const resolvedAddress = (ehrOpen ? `EHR ${ehr.trim()}` : address.trim()) || placeholder;

  return (
    <div data-screen-label="01 Address intake" style={{
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
      "--danger": "#a83232",
      "--danger-text": "#5a1a1a",
      "--danger-bg": "#fbf2f0",
      "--danger-border": "#e8c7c0",
      "--font-sans": "'Geist', ui-sans-serif, system-ui, -apple-system, 'Helvetica Neue', sans-serif",
      "--font-mono": "'Geist Mono', ui-monospace, 'SF Mono', Menlo, monospace",
      minHeight: "100vh",
      background: "var(--surface-2)",
      color: "var(--text)",
      fontFamily: "var(--font-sans)",
      display: "flex",
      flexDirection: "column",
    }}>
      {/* Top bar */}
      <header style={{
        height: 56,
        borderBottom: "1px solid var(--hairline)",
        background: "var(--surface)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 28px",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Wordmark size={17} />
          <span style={{
            fontFamily: "var(--font-mono)",
            fontSize: 10.5,
            color: "var(--text-3)",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            border: "1px solid var(--hairline)",
            padding: "2px 7px",
            borderRadius: 4,
            background: "var(--surface-2)",
          }}>v0.1 · MVP</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <LangSwitch lang={lang} onChange={(v) => setTweak("lang", v)} />
          <span style={{ width: 1, height: 22, background: "var(--hairline)" }} />
          <UserMenu t={t} />
        </div>
      </header>

      {/* Page */}
      <main style={{
        flex: 1,
        display: "flex",
        justifyContent: "center",
        padding: "64px 24px 96px",
      }}>
        <div style={{
          width: "100%",
          maxWidth: 640,
          display: "flex",
          flexDirection: "column",
          gap: density === "compact" ? 24 : 32,
        }}>
          {/* Step indicator — full on desktop, condensed on mobile */}
          <StepIndicator lang={lang} />

          {/* Heading */}
          <div>
            <h1 style={{
              margin: 0,
              fontSize: 32,
              lineHeight: 1.15,
              letterSpacing: "-0.02em",
              fontWeight: 600,
              color: "var(--text)",
              textWrap: "balance",
            }}>{t.h1}</h1>
            <p style={{
              margin: "14px 0 0",
              fontSize: 15,
              lineHeight: 1.55,
              color: "var(--text-2)",
              maxWidth: 540,
              textWrap: "pretty",
            }}>{t.sub}</p>
          </div>

          {/* Error (above inputs, per brief) */}
          {isError && <ErrorBlock t={t} onDismiss={reset} />}

          {/* Form */}
          <form onSubmit={submit} style={{
            display: "flex",
            flexDirection: "column",
            gap: density === "compact" ? 16 : 20,
          }}>
            {ehrOpen ? (
              <Field
                id="bl-ehr"
                label={t.ehr_label}
                hint={t.ehr_hint}
                value={ehr}
                onChange={setEhr}
                placeholder="120143580"
                readOnly={isBusy}
                error={isError}
                mono
                autoFocus
                density={density}
              />
            ) : (
              <Field
                id="bl-address"
                label={t.addr_label}
                hint={t.addr_hint}
                value={address}
                onChange={setAddress}
                placeholder={placeholder}
                readOnly={isBusy}
                error={isError}
                autoFocus
                density={density}
              />
            )}
            {!ehrOpen && (
              <Field
                id="bl-project"
                label={t.title_label}
                optional={t.title_optional}
                hint={t.title_hint}
                value={project}
                onChange={setProject}
                placeholder={lang === "et" ? "Pelguranna kvartal — II etapp" : "Pelguranna quarter — phase 2"}
                readOnly={isBusy}
                density={density}
              />
            )}
            {/* EHR direct-entry toggle — collapsed by default */}
            <button
              type="button"
              onClick={() => { setEhrOpen((o) => !o); }}
              disabled={isBusy}
              style={{
                appearance: "none",
                border: 0,
                background: "transparent",
                color: "var(--text-2)",
                fontFamily: "var(--font-sans)",
                fontSize: 12.5,
                padding: 0,
                marginTop: -6,
                cursor: "default",
                alignSelf: "flex-start",
                textDecoration: "underline",
                textUnderlineOffset: 3,
                textDecorationColor: "var(--hairline-strong)",
              }}
            >
              {ehrOpen ? t.ehr_link_close : t.ehr_link_open}
            </button>

            <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 4 }}>
              <button
                type="submit"
                disabled={isBusy}
                style={{
                  appearance: "none",
                  border: 0,
                  background: isBusy ? "var(--primary-hover)" : "var(--primary)",
                  color: "#fff",
                  height: density === "compact" ? 42 : 46,
                  padding: "0 20px",
                  borderRadius: 8,
                  fontFamily: "var(--font-sans)",
                  fontSize: 14.5,
                  fontWeight: 600,
                  letterSpacing: "-0.005em",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 10,
                  cursor: "default",
                  transition: "background .12s ease",
                  alignSelf: "flex-start",
                }}
                onMouseEnter={(e) => { if (!isBusy) e.currentTarget.style.background = "var(--primary-hover)"; }}
                onMouseLeave={(e) => { if (!isBusy) e.currentTarget.style.background = "var(--primary)"; }}
              >
                {isBusy && <Spinner />}
                {isBusy ? t.cta_busy : isError ? t.cta_retry : t.cta_idle}
                {!isBusy && <span aria-hidden style={{ opacity: 0.7, marginLeft: 2 }}>→</span>}
              </button>
              {isResolved && <FoundChip t={t} address={resolvedAddress} />}
            </div>
          </form>

          {/* Explainer — visible always; desaturated while submitting */}
          <Explainer t={t} dim={isBusy} lang={lang} />

          {/* Legal */}
          <p style={{
            margin: 0,
            paddingTop: 16,
            borderTop: "1px solid var(--hairline)",
            fontSize: 12,
            lineHeight: 1.55,
            color: "var(--text-3)",
            maxWidth: 580,
          }}>{t.legal}</p>
        </div>
      </main>

      {/* Tweaks */}
      <TweaksPanel>
        <TweakSection label={lang === "et" ? "Olek" : "State"} />
        <TweakRadio
          label={lang === "et" ? "Vaade" : "View"}
          value={state}
          options={["idle", "submitting", "error", "resolved"]}
          onChange={(v) => setTweak("state", v)}
        />
        <TweakSection label={lang === "et" ? "Esitlus" : "Presentation"} />
        <TweakRadio
          label={lang === "et" ? "Keel" : "Language"}
          value={lang}
          options={["et", "en"]}
          onChange={(v) => setTweak("lang", v)}
        />
        <TweakRadio
          label={lang === "et" ? "Tihedus" : "Density"}
          value={density}
          options={["compact", "comfortable"]}
          onChange={(v) => setTweak("density", v)}
        />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
