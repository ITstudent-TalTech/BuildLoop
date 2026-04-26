// passport-draft.jsx
// BUILDLoop — third screen: auto-generated passport draft, read-only review.
// Inherits TopBar / StepIndicator / tokens from bl-shared.jsx.

const { useState: pdUseState, useMemo: pdUseMemo, useRef: pdUseRef } = React;

// ─── Translations ────────────────────────────────────────────────────────────
const PD_COPY = {
  en: {
    title: "Passport draft",
    sub: "This is what we extracted from the construction register. Review each section before publishing.",
    review: "Review and edit",
    regenerate: "Regenerate draft",

    quality_pill: "Draft quality",
    pct_complete: "complete",
    pct_confidence: "confidence",
    quality_help: "Completeness is the share of schema fields populated. Confidence is the parser's certainty in the extracted values, weighted by source quality.",

    sec_id: "Identity",
    sec_profile: "Building profile",
    sec_struct: "Structural systems",
    sec_tech: "Technical systems",
    sec_loc: "Location",
    sec_parts: "Building parts",
    sec_quality: "Quality",

    fields_populated: "fields populated",
    high_conf: "high confidence",
    med_conf: "medium confidence",
    low_conf: "low confidence",

    missing_badge: "Missing",
    evidence_pdf: "From EHR PDF",
    evidence_register: "From EHR register",
    evidence_cadastre: "From cadastre",
    page: "page",
    confidence_label: "Confidence",
    last_updated: "Last updated",
    high: "high", med: "medium", low: "low",

    parts_id: "Identifier", parts_type: "Type", parts_name: "Name",
    parts_use: "Use", parts_area: "Area",
    parts_empty: "No building parts in the register record. You can add them during review.",

    completeness: "Schema completeness",
    overall_conf: "Confidence",
    per_section: "Per-section breakdown",
    section_h: "Section",
    completeness_h: "Complete",
    conf_h: "Confidence",
    missing_fields: "Missing fields",

    // Field labels
    f_ehr: "EHR code",
    f_norm: "Normalized address",
    f_aliases: "Address aliases",
    f_country: "Country",
    f_orig: "Original input",
    f_btype: "Building type",
    f_bstatus: "Building status",
    f_bname: "Building name",
    f_use_cat: "Use categories",
    f_floors_above: "Floors above ground",
    f_floors_below: "Floors below ground",
    f_footprint: "Footprint area",
    f_heated: "Heated area",
    f_net: "Net area",
    f_public: "Public-use area",
    f_tech_area: "Technical area",
    f_height: "Height",
    f_length: "Length",
    f_width: "Width",
    f_volume: "Volume",
    f_foundation: "Foundation type",
    f_load_bearing: "Load-bearing material",
    f_wall_type: "Wall type",
    f_facade: "Facade finish",
    f_floor_struct: "Floor structure",
    f_roof_struct: "Roof structure",
    f_roof_cover: "Roof covering",
    f_electricity: "Electricity",
    f_water: "Water",
    f_sewer: "Sewerage",
    f_heat: "Heat source",
    f_gas: "Gas",
    f_vent: "Ventilation",
    f_lifts: "Lifts",
    f_geom: "Geometry method",
    f_shape: "Shape type",
    f_coords: "Coordinates",
  },
  et: {
    title: "Passi mustand",
    sub: "Need on andmed, mille me ehitisregistrist välja võtsime. Vaata iga sektsioon enne avaldamist üle.",
    review: "Vaata üle ja muuda",
    regenerate: "Loo mustand uuesti",

    quality_pill: "Mustandi kvaliteet",
    pct_complete: "valminud",
    pct_confidence: "kindlus",
    quality_help: "Valmidus näitab, mitu skeemi välja on täidetud. Kindlus näitab, kuivõrd parser usub eraldatud väärtuseid, allika kvaliteediga kaalutuna.",

    sec_id: "Identiteet",
    sec_profile: "Hoone profiil",
    sec_struct: "Konstruktsioon",
    sec_tech: "Tehnosüsteemid",
    sec_loc: "Asukoht",
    sec_parts: "Hooneosad",
    sec_quality: "Kvaliteet",

    fields_populated: "välja täidetud",
    high_conf: "kõrge kindlus",
    med_conf: "keskmine kindlus",
    low_conf: "madal kindlus",

    missing_badge: "Puudub",
    evidence_pdf: "EHR PDF-ist",
    evidence_register: "EHR registrist",
    evidence_cadastre: "Katastrist",
    page: "lk",
    confidence_label: "Kindlus",
    last_updated: "Viimati uuendatud",
    high: "kõrge", med: "keskmine", low: "madal",

    parts_id: "Tunnus", parts_type: "Tüüp", parts_name: "Nimi",
    parts_use: "Kasutus", parts_area: "Pind",
    parts_empty: "Registrikandes pole hooneosi. Saad need ülevaatusel lisada.",

    completeness: "Skeemi valmidus",
    overall_conf: "Kindlus",
    per_section: "Sektsioonide kaupa",
    section_h: "Sektsioon",
    completeness_h: "Valmidus",
    conf_h: "Kindlus",
    missing_fields: "Puuduvad väljad",

    f_ehr: "EHR-kood",
    f_norm: "Normaliseeritud aadress",
    f_aliases: "Aadressi sünonüümid",
    f_country: "Riik",
    f_orig: "Algne sisend",
    f_btype: "Hoone tüüp",
    f_bstatus: "Hoone staatus",
    f_bname: "Hoone nimi",
    f_use_cat: "Kasutusotstarbed",
    f_floors_above: "Maapealsed korrused",
    f_floors_below: "Maa-alused korrused",
    f_footprint: "Ehitisealune pind",
    f_heated: "Köetav pind",
    f_net: "Netopind",
    f_public: "Avaliku kasutuse pind",
    f_tech_area: "Tehniline pind",
    f_height: "Kõrgus",
    f_length: "Pikkus",
    f_width: "Laius",
    f_volume: "Maht",
    f_foundation: "Vundamendi tüüp",
    f_load_bearing: "Kandev materjal",
    f_wall_type: "Seinatüüp",
    f_facade: "Fassaadi viimistlus",
    f_floor_struct: "Põranda konstruktsioon",
    f_roof_struct: "Katuse konstruktsioon",
    f_roof_cover: "Katusekate",
    f_electricity: "Elekter",
    f_water: "Vesi",
    f_sewer: "Kanalisatsioon",
    f_heat: "Soojusallikas",
    f_gas: "Gaas",
    f_vent: "Ventilatsioon",
    f_lifts: "Liftid",
    f_geom: "Geomeetria meetod",
    f_shape: "Kuju tüüp",
    f_coords: "Koordinaadid",
  },
};

// ─── Number formatting ─────────────────────────────────────────────────────
// EN uses comma thousands separator. ET uses NBSP (per Estonian Language Council).
function fmtNum(n, lang) {
  const sep = lang === "et" ? "\u00A0" : ",";
  const parts = String(n).split(".");
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, sep);
  return parts.join(lang === "et" ? "," : ".");
}

// Translate value strings that need localization.
const VALUE_COPY = {
  en: {
    res: "Residential", inuse: "In use", apartment_bldg: "Apartment building",
    concrete_strip: "Concrete strip foundation", brick: "Brick",
    load_bearing_ext: "Load-bearing exterior walls",
    plaster: "Plaster", rc: "Reinforced concrete",
    wooden_truss: "Wooden truss", clay_tile: "Clay tile",
    connected: "Connected", central: "Central",
    district: "District heating", not_conn: "Not connected", natural: "Natural",
    cadastral: "Cadastral", polygon: "Polygon",
    estonia: "Estonia", apt_2: "2-room", apt_3: "3-room", living: "Living",
    apartment: "Apartment", commercial: "Commercial", retail: "Retail",
  },
  et: {
    res: "Elamu", inuse: "Kasutuses", apartment_bldg: "Korterelamu",
    concrete_strip: "Betoonist lintvundament", brick: "Tellis",
    load_bearing_ext: "Kandvad välisseinad",
    plaster: "Krohv", rc: "Raudbetoon",
    wooden_truss: "Puidust sõrestik", clay_tile: "Savikivikatus",
    connected: "Ühendatud", central: "Keskne",
    district: "Kaugküte", not_conn: "Puudub", natural: "Loomulik",
    cadastral: "Kataster", polygon: "Polügoon",
    estonia: "Eesti", apt_2: "2-toaline", apt_3: "3-toaline", living: "Elamine",
    apartment: "Korter", commercial: "Äri", retail: "Kauplus",
  },
};

// ─── Building data ─────────────────────────────────────────────────────────
// Each field: key, value, unit, confidence (high/med/low), source, page, mono?
// `value: null` = missing.
function buildSections(t, vc, lang, density) {
  // density: how many fields to mark missing. 'complete'=0, 'partial'=2, 'sparse'=6.
  const sparseHints = {
    complete: new Set(),
    partial: new Set(["bname", "public"]),
    sparse: new Set(["bname", "public", "tech_area", "length", "width", "facade"]),
  };
  const miss = sparseHints[density] || sparseHints.partial;

  const m = (key, value) => miss.has(key) ? null : value;

  return [
    {
      id: "identity",
      title: t.sec_id,
      fields: [
        { key: "ehr", label: t.f_ehr, value: "101035685", mono: true, conf: "high", source: "register" },
        { key: "norm", label: t.f_norm, value: "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4", conf: "high", source: "register" },
        { key: "aliases", label: t.f_aliases, value: "Lai tn 1 · Nunne tn 4", conf: "high", source: "register" },
        { key: "country", label: t.f_country, value: vc.estonia, conf: "high", source: "register" },
        { key: "orig", label: t.f_orig, value: "Lai 1, 10133 Tallinn", mono: true, conf: "high", source: "user" },
      ],
    },
    {
      id: "profile",
      title: t.sec_profile,
      fields: [
        { key: "btype", label: t.f_btype, value: vc.res, conf: "high", source: "pdf", page: 1 },
        { key: "bstatus", label: t.f_bstatus, value: vc.inuse, conf: "high", source: "register" },
        { key: "bname", label: t.f_bname, value: m("bname", null), conf: "low", source: "pdf", page: 1 },
        { key: "use_cat", label: t.f_use_cat, value: `${vc.apartment_bldg} (11200)`, conf: "high", source: "register" },
        { key: "fa", label: t.f_floors_above, value: "4", mono: true, conf: "high", source: "pdf", page: 2 },
        { key: "fb", label: t.f_floors_below, value: "1", mono: true, conf: "high", source: "pdf", page: 2 },
        { key: "footprint", label: t.f_footprint, value: `${fmtNum(412, lang)} m²`, mono: true, conf: "high", source: "cadastre" },
        { key: "heated", label: t.f_heated, value: `${fmtNum(1648, lang)} m²`, mono: true, conf: "high", source: "pdf", page: 3 },
        { key: "net", label: t.f_net, value: `${fmtNum(1532, lang)} m²`, mono: true, conf: "high", source: "pdf", page: 3 },
        { key: "public", label: t.f_public, value: m("public", null), conf: "low", source: "pdf", page: 3 },
        { key: "tech_area", label: t.f_tech_area, value: m("tech_area", `${fmtNum(38, lang)} m²`), mono: true, conf: "med", source: "pdf", page: 3 },
        { key: "height", label: t.f_height, value: `14${lang === "et" ? "," : "."}2 m`, mono: true, conf: "high", source: "pdf", page: 4 },
        { key: "length", label: t.f_length, value: m("length", "32 m"), mono: true, conf: "med", source: "cadastre" },
        { key: "width", label: t.f_width, value: m("width", "13 m"), mono: true, conf: "med", source: "cadastre" },
        { key: "volume", label: t.f_volume, value: `${fmtNum(5860, lang)} m³`, mono: true, conf: "high", source: "pdf", page: 4 },
      ],
    },
    {
      id: "struct",
      title: t.sec_struct,
      fields: [
        { key: "foundation", label: t.f_foundation, value: vc.concrete_strip, conf: "high", source: "pdf", page: 5 },
        { key: "load_bearing", label: t.f_load_bearing, value: vc.brick, conf: "high", source: "pdf", page: 5 },
        { key: "wall_type", label: t.f_wall_type, value: vc.load_bearing_ext, conf: "high", source: "pdf", page: 5 },
        { key: "facade", label: t.f_facade, value: m("facade", vc.plaster), conf: "med", source: "pdf", page: 5 },
        { key: "floor_struct", label: t.f_floor_struct, value: vc.rc, conf: "high", source: "pdf", page: 6 },
        { key: "roof_struct", label: t.f_roof_struct, value: vc.wooden_truss, conf: "high", source: "pdf", page: 6 },
        { key: "roof_cover", label: t.f_roof_cover, value: vc.clay_tile, conf: "high", source: "pdf", page: 6 },
      ],
    },
    {
      id: "tech",
      title: t.sec_tech,
      fields: [
        { key: "elec", label: t.f_electricity, value: vc.connected, conf: "high", source: "register" },
        { key: "water", label: t.f_water, value: vc.central, conf: "high", source: "register" },
        { key: "sewer", label: t.f_sewer, value: vc.central, conf: "high", source: "register" },
        { key: "heat", label: t.f_heat, value: vc.district, conf: "high", source: "register" },
        { key: "gas", label: t.f_gas, value: vc.not_conn, conf: "high", source: "register" },
        { key: "vent", label: t.f_vent, value: vc.natural, conf: "med", source: "pdf", page: 7 },
        { key: "lifts", label: t.f_lifts, value: "0", mono: true, conf: "high", source: "register" },
      ],
    },
    {
      id: "loc",
      title: t.sec_loc,
      fields: [
        { key: "geom", label: t.f_geom, value: vc.cadastral, conf: "high", source: "cadastre" },
        { key: "shape", label: t.f_shape, value: vc.polygon, conf: "high", source: "cadastre" },
        { key: "coords", label: t.f_coords, value: "59.4395° N, 24.7445° E", mono: true, conf: "high", source: "cadastre" },
      ],
      mapPreview: true,
    },
    {
      id: "parts",
      title: t.sec_parts,
      table: true,
      parts: [
        { id: "P1", type: vc.apartment, name: vc.apt_2, use: vc.living, area: `54 m²` },
        { id: "P2", type: vc.apartment, name: vc.apt_3, use: vc.living, area: `71 m²` },
        { id: "P3", type: vc.apartment, name: vc.apt_2, use: vc.living, area: `52 m²` },
        { id: "P4", type: vc.apartment, name: vc.apt_3, use: vc.living, area: `68 m²` },
        { id: "P5", type: vc.apartment, name: vc.apt_2, use: vc.living, area: `49 m²` },
      ],
    },
  ];
}

// ─── Section status counts ─────────────────────────────────────────────────
function sectionStatus(sec, t) {
  if (sec.table) {
    const n = sec.parts?.length || 0;
    return { text: `${n} ${n === 1 ? "row" : "rows"}`, conf: "high" };
  }
  const total = sec.fields.length;
  const filled = sec.fields.filter((f) => f.value != null).length;
  const confs = sec.fields.map((f) => f.conf);
  const overall = confs.filter((c) => c === "low").length > 1 ? "low"
    : confs.filter((c) => c === "med").length > 2 ? "med" : "high";
  const confLabel = overall === "high" ? t.high_conf : overall === "med" ? t.med_conf : t.low_conf;
  return { text: `${filled} of ${total} ${t.fields_populated} · ${confLabel}`, conf: overall, filled, total };
}

function overallQuality(sections) {
  const all = sections.flatMap((s) => s.table ? [] : s.fields);
  const total = all.length;
  const filled = all.filter((f) => f.value != null).length;
  const completeness = Math.round((filled / total) * 100);
  // Weighted confidence: high=1.0, med=0.7, low=0.4. Missing = 0.
  const score = all.reduce((acc, f) => {
    if (f.value == null) return acc;
    return acc + (f.conf === "high" ? 1.0 : f.conf === "med" ? 0.7 : 0.4);
  }, 0);
  const confidence = Math.round((score / total) * 100);
  return { completeness, confidence };
}

// ─── Confidence icon ───────────────────────────────────────────────────────
function ConfidenceIcon({ conf }) {
  // filled green (high) / outlined green (med) / hollow gray (low)
  const size = 14;
  if (conf === "high") {
    return (
      <span aria-hidden style={{
        width: size, height: size, borderRadius: "50%",
        background: "var(--primary)",
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        flexShrink: 0,
      }}>
        <span style={{
          width: 5, height: 5, borderRadius: "50%",
          background: "var(--accent)",
        }} />
      </span>
    );
  }
  if (conf === "med") {
    return (
      <span aria-hidden style={{
        width: size, height: size, borderRadius: "50%",
        border: "1.5px solid var(--primary)",
        background: "transparent",
        flexShrink: 0,
      }} />
    );
  }
  return (
    <span aria-hidden style={{
      width: size, height: size, borderRadius: "50%",
      border: "1px dashed var(--text-3)",
      background: "transparent",
      flexShrink: 0,
    }} />
  );
}

function MissingBadge({ t }) {
  return (
    <span style={{
      fontFamily: "var(--font-mono)", fontSize: 10,
      color: "var(--text-3)", letterSpacing: "0.05em",
      textTransform: "uppercase", fontWeight: 600,
      padding: "2px 7px", borderRadius: 4,
      border: "1px dashed var(--hairline-strong)",
      background: "var(--surface-2)",
    }}>{t.missing_badge}</span>
  );
}

// ─── Evidence popover ──────────────────────────────────────────────────────
function EvidenceCell({ field, t, lang }) {
  const [open, setOpen] = pdUseState(false);
  if (field.value == null) {
    return <MissingBadge t={t} />;
  }
  const sourceText = field.source === "pdf" ? `${t.evidence_pdf} · ${t.page} ${field.page}`
    : field.source === "cadastre" ? t.evidence_cadastre
    : field.source === "user" ? (lang === "et" ? "Kasutaja sisend" : "User input")
    : t.evidence_register;
  const confText = field.conf === "high" ? t.high : field.conf === "med" ? t.med : t.low;
  return (
    <span style={{ position: "relative", display: "inline-flex" }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <ConfidenceIcon conf={field.conf} />
      {open && (
        <div role="tooltip" style={{
          position: "absolute", top: "calc(100% + 8px)", right: 0,
          width: 240, padding: "10px 12px",
          background: "var(--text)", color: "var(--surface)",
          borderRadius: 7, fontSize: 11.5, lineHeight: 1.5,
          fontFamily: "var(--font-sans)",
          boxShadow: "0 10px 24px rgba(13,31,23,0.18)",
          zIndex: 30,
        }}>
          <div style={{ marginBottom: 4 }}>{sourceText}</div>
          <div style={{ color: "rgba(255,255,255,0.7)" }}>
            {t.confidence_label}: <span style={{ color: "var(--accent)" }}>{confText}</span>
          </div>
          <div style={{ color: "rgba(255,255,255,0.55)", fontSize: 10.5, marginTop: 2 }}>
            {t.last_updated} 2026-04-26
          </div>
        </div>
      )}
    </span>
  );
}

// ─── Field row ─────────────────────────────────────────────────────────────
function FieldRow({ field, t, lang, isLast }) {
  const isMissing = field.value == null;
  return (
    <div id={`field-${field.key}`} style={{
      display: "grid",
      gridTemplateColumns: "minmax(180px, 30%) 1fr auto",
      alignItems: "baseline",
      gap: 16,
      padding: "11px 0",
      borderBottom: isLast ? "none" : "1px solid var(--hairline)",
    }}>
      <div style={{
        fontSize: 13, color: "var(--text-2)", fontWeight: 500, lineHeight: 1.45,
      }}>{field.label}</div>
      <div style={{
        fontFamily: field.mono ? "var(--font-mono)" : "var(--font-sans)",
        fontSize: field.mono ? 13 : 14,
        color: isMissing ? "var(--text-3)" : "var(--text)",
        lineHeight: 1.45, wordBreak: "break-word",
      }}>{isMissing ? "—" : field.value}</div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", minWidth: 24 }}>
        <EvidenceCell field={field} t={t} lang={lang} />
      </div>
    </div>
  );
}

// ─── Section card ──────────────────────────────────────────────────────────
function SectionCard({ section, t, lang, expanded, onToggle, confDisplay }) {
  const status = sectionStatus(section, t);
  const open = expanded;
  return (
    <section style={{
      background: "var(--surface)",
      border: "1px solid var(--hairline)",
      borderRadius: 10,
      overflow: "hidden",
    }}>
      <header
        onClick={onToggle}
        style={{
          padding: "16px 22px",
          borderBottom: open ? "1px solid var(--hairline)" : "none",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          gap: 16, cursor: "default",
        }}
      >
        <div style={{ display: "flex", alignItems: "baseline", gap: 14, flex: 1, minWidth: 0 }}>
          <h2 style={{
            margin: 0, fontSize: 17, fontWeight: 600,
            letterSpacing: "-0.01em", color: "var(--text)",
          }}>{section.title}</h2>
          <span style={{
            fontFamily: "var(--font-mono)", fontSize: 11,
            color: "var(--text-3)", letterSpacing: "0.02em",
          }}>{status.text}</span>
        </div>
        <span aria-hidden style={{
          color: "var(--text-3)", fontSize: 12,
          transform: open ? "rotate(180deg)" : "rotate(0)",
          transition: "transform .15s ease",
          fontFamily: "var(--font-mono)",
        }}>▾</span>
      </header>
      {open && (
        <div style={{ padding: "4px 22px 14px" }}>
          {section.table ? (
            <PartsTable parts={section.parts} t={t} />
          ) : (
            section.fields.map((f, i) => (
              <FieldRow
                key={f.key}
                field={f}
                t={t}
                lang={lang}
                isLast={i === section.fields.length - 1}
              />
            ))
          )}
          {section.mapPreview && <MapPreview />}
        </div>
      )}
    </section>
  );
}

// ─── Parts table ───────────────────────────────────────────────────────────
function PartsTable({ parts, t }) {
  if (!parts || parts.length === 0) {
    return (
      <div style={{
        padding: "20px 0",
        fontSize: 13, color: "var(--text-2)", fontStyle: "italic",
        lineHeight: 1.5,
      }}>{t.parts_empty}</div>
    );
  }
  const headers = [t.parts_id, t.parts_type, t.parts_name, t.parts_use, t.parts_area];
  return (
    <div style={{ paddingTop: 8 }}>
      <table style={{
        width: "100%", borderCollapse: "collapse",
        fontFamily: "var(--font-sans)", fontSize: 13,
      }}>
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={h} style={{
                textAlign: "left",
                padding: "8px 10px 8px 0",
                borderBottom: "1px solid var(--hairline-strong)",
                fontFamily: "var(--font-mono)", fontSize: 10.5,
                color: "var(--text-3)", letterSpacing: "0.05em",
                textTransform: "uppercase", fontWeight: 600,
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {parts.map((p, i) => (
            <tr key={p.id}>
              <td style={{
                padding: "10px 10px 10px 0",
                borderBottom: i < parts.length - 1 ? "1px solid var(--hairline)" : "none",
                fontFamily: "var(--font-mono)", fontSize: 12.5,
                color: "var(--text)", fontWeight: 500,
              }}>{p.id}</td>
              <td style={{
                padding: "10px 10px 10px 0",
                borderBottom: i < parts.length - 1 ? "1px solid var(--hairline)" : "none",
                color: "var(--text)",
              }}>{p.type}</td>
              <td style={{
                padding: "10px 10px 10px 0",
                borderBottom: i < parts.length - 1 ? "1px solid var(--hairline)" : "none",
                color: "var(--text)",
              }}>{p.name}</td>
              <td style={{
                padding: "10px 10px 10px 0",
                borderBottom: i < parts.length - 1 ? "1px solid var(--hairline)" : "none",
                color: "var(--text-2)",
              }}>{p.use}</td>
              <td style={{
                padding: "10px 0",
                borderBottom: i < parts.length - 1 ? "1px solid var(--hairline)" : "none",
                fontFamily: "var(--font-mono)", fontSize: 12.5,
                color: "var(--text)", textAlign: "right",
              }}>{p.area}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Map preview (decorative tile) ─────────────────────────────────────────
function MapPreview() {
  // Stylized cadastral parcel rendering — no real map. Indicates location is set.
  return (
    <div style={{
      marginTop: 14, height: 120,
      borderRadius: 8, overflow: "hidden",
      border: "1px solid var(--hairline)",
      position: "relative",
      background: "var(--surface-2)",
    }}>
      <svg viewBox="0 0 600 120" preserveAspectRatio="xMidYMid slice"
        style={{ width: "100%", height: "100%", display: "block" }}>
        <defs>
          <pattern id="bl-grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none"
              stroke="rgba(13,31,23,0.06)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="600" height="120" fill="url(#bl-grid)" />
        {/* faint surrounding parcels */}
        <path d="M 40 20 L 180 18 L 200 90 L 60 100 Z" fill="rgba(13,31,23,0.04)" stroke="rgba(13,31,23,0.12)" />
        <path d="M 220 24 L 360 12 L 380 60 L 240 78 Z" fill="rgba(13,31,23,0.04)" stroke="rgba(13,31,23,0.12)" />
        <path d="M 400 18 L 560 22 L 570 95 L 410 100 Z" fill="rgba(13,31,23,0.04)" stroke="rgba(13,31,23,0.12)" />
        <path d="M 220 80 L 380 70 L 400 110 L 240 118 Z" fill="rgba(13,31,23,0.04)" stroke="rgba(13,31,23,0.12)" />
        {/* the active parcel */}
        <path d="M 250 30 L 340 22 L 354 64 L 264 72 Z" fill="rgba(31,77,58,0.15)" stroke="var(--primary)" strokeWidth="1.5" />
        <circle cx="304" cy="48" r="6" fill="var(--primary)" />
        <circle cx="304" cy="48" r="11" fill="none" stroke="var(--primary)" strokeOpacity="0.3" strokeWidth="1.5" />
      </svg>
      <div style={{
        position: "absolute", bottom: 8, left: 10,
        fontFamily: "var(--font-mono)", fontSize: 10.5,
        color: "var(--text-2)", letterSpacing: "0.04em",
        background: "var(--surface)", padding: "2px 7px",
        borderRadius: 4, border: "1px solid var(--hairline)",
      }}>59.4395° N, 24.7445° E</div>
    </div>
  );
}

// ─── Quality section (custom — different from FieldRow layout) ─────────────
function QualitySection({ sections, t, lang, expanded, onToggle, onJumpToField }) {
  const overall = pdUseMemo(() => overallQuality(sections), [sections]);
  const perSection = sections.filter((s) => !s.table).map((s) => {
    const total = s.fields.length;
    const filled = s.fields.filter((f) => f.value != null).length;
    const pct = Math.round((filled / total) * 100);
    const confs = s.fields.map((f) => f.conf);
    const overall = confs.filter((c) => c === "low").length > 1 ? "low"
      : confs.filter((c) => c === "med").length > 2 ? "med" : "high";
    return { id: s.id, title: s.title, completeness: pct, conf: overall };
  });
  const missing = sections
    .filter((s) => !s.table)
    .flatMap((s) => s.fields.filter((f) => f.value == null).map((f) => ({ key: f.key, label: f.label })));

  return (
    <section style={{
      background: "var(--surface)",
      border: "1px solid var(--hairline)",
      borderRadius: 10,
      overflow: "hidden",
    }}>
      <header onClick={onToggle} style={{
        padding: "16px 22px",
        borderBottom: expanded ? "1px solid var(--hairline)" : "none",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        gap: 16, cursor: "default",
      }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 14, flex: 1, minWidth: 0 }}>
          <h2 style={{
            margin: 0, fontSize: 17, fontWeight: 600,
            letterSpacing: "-0.01em", color: "var(--text)",
          }}>{t.sec_quality}</h2>
          <span style={{
            fontFamily: "var(--font-mono)", fontSize: 11,
            color: "var(--text-3)", letterSpacing: "0.02em",
          }}>{overall.completeness}% · {overall.confidence}%</span>
        </div>
        <span aria-hidden style={{
          color: "var(--text-3)", fontSize: 12,
          transform: expanded ? "rotate(180deg)" : "rotate(0)",
          transition: "transform .15s ease",
          fontFamily: "var(--font-mono)",
        }}>▾</span>
      </header>
      {expanded && (
        <div style={{ padding: "18px 22px 22px" }}>
          {/* Two large bars */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 28, marginBottom: 22 }}>
            <QualityBar label={t.completeness} value={overall.completeness} />
            <QualityBar label={t.overall_conf} value={overall.confidence} />
          </div>

          {/* Per-section breakdown */}
          <div style={{
            fontFamily: "var(--font-mono)", fontSize: 10.5,
            color: "var(--text-3)", letterSpacing: "0.06em",
            textTransform: "uppercase", fontWeight: 600,
            marginBottom: 8,
          }}>{t.per_section}</div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr>
                <th style={qualityTh}>{t.section_h}</th>
                <th style={{ ...qualityTh, width: "30%" }}>{t.completeness_h}</th>
                <th style={{ ...qualityTh, width: 130, textAlign: "right" }}>{t.conf_h}</th>
              </tr>
            </thead>
            <tbody>
              {perSection.map((s) => (
                <tr key={s.id}>
                  <td style={qualityTd}>{s.title}</td>
                  <td style={qualityTd}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <div style={{
                        flex: 1, height: 4, borderRadius: 2,
                        background: "var(--surface-2)", border: "1px solid var(--hairline)",
                        overflow: "hidden", maxWidth: 160,
                      }}>
                        <div style={{
                          width: `${s.completeness}%`, height: "100%",
                          background: s.completeness >= 80 ? "var(--primary)" : "var(--text-2)",
                        }} />
                      </div>
                      <span style={{
                        fontFamily: "var(--font-mono)", fontSize: 12,
                        color: "var(--text-2)", minWidth: 36,
                      }}>{s.completeness}%</span>
                    </div>
                  </td>
                  <td style={{ ...qualityTd, textAlign: "right" }}>
                    <span style={{
                      fontFamily: "var(--font-mono)", fontSize: 11,
                      color: s.conf === "high" ? "var(--primary)" : s.conf === "med" ? "var(--text-2)" : "var(--text-3)",
                      letterSpacing: "0.04em", textTransform: "uppercase", fontWeight: 600,
                    }}>{s.conf === "high" ? t.high : s.conf === "med" ? t.med : t.low}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Missing fields list */}
          {missing.length > 0 && (
            <div style={{ marginTop: 22 }}>
              <div style={{
                fontFamily: "var(--font-mono)", fontSize: 10.5,
                color: "var(--text-3)", letterSpacing: "0.06em",
                textTransform: "uppercase", fontWeight: 600,
                marginBottom: 8,
              }}>{t.missing_fields} ({missing.length})</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {missing.map((m) => (
                  <a key={m.key} href={`#field-${m.key}`}
                    onClick={(e) => { e.preventDefault(); onJumpToField(m.key); }}
                    style={{
                      fontSize: 12.5, color: "var(--text)",
                      background: "var(--surface-2)",
                      border: "1px solid var(--hairline-strong)",
                      borderRadius: 999,
                      padding: "4px 11px",
                      textDecoration: "none",
                      cursor: "default",
                    }}>{m.label}</a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

const qualityTh = {
  textAlign: "left",
  padding: "8px 10px 8px 0",
  borderBottom: "1px solid var(--hairline-strong)",
  fontFamily: "var(--font-mono)", fontSize: 10.5,
  color: "var(--text-3)", letterSpacing: "0.05em",
  textTransform: "uppercase", fontWeight: 600,
};
const qualityTd = {
  padding: "10px 10px 10px 0",
  borderBottom: "1px solid var(--hairline)",
  color: "var(--text)",
  verticalAlign: "middle",
};

function QualityBar({ label, value }) {
  return (
    <div>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "baseline",
        marginBottom: 6,
      }}>
        <span style={{
          fontSize: 13, color: "var(--text-2)", fontWeight: 500,
        }}>{label}</span>
        <span style={{
          fontFamily: "var(--font-mono)", fontSize: 18,
          fontWeight: 600, color: "var(--text)",
        }}>{value}<span style={{ color: "var(--text-3)", fontSize: 13, marginLeft: 1 }}>%</span></span>
      </div>
      <div style={{
        height: 6, borderRadius: 3,
        background: "var(--surface-2)", border: "1px solid var(--hairline)",
        overflow: "hidden",
      }}>
        <div style={{
          width: `${value}%`, height: "100%",
          background: value >= 80 ? "var(--primary)" : "var(--text-2)",
          transition: "width .3s ease",
        }} />
      </div>
    </div>
  );
}

// ─── Sticky identity strip ─────────────────────────────────────────────────
function IdentityStrip({ t, overall, lang }) {
  const [showHelp, setShowHelp] = pdUseState(false);
  return (
    <div style={{
      position: "sticky", top: 56, zIndex: 5,
      background: "var(--surface-2)",
      borderBottom: "1px solid var(--hairline)",
      padding: "16px 28px",
    }}>
      <div style={{
        maxWidth: 840, margin: "0 auto",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        gap: 24, flexWrap: "wrap",
      }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{
            fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em",
            color: "var(--text)", lineHeight: 1.3,
          }}>Lai tn 1 // Nunne tn 4, 10133 Tallinn</div>
          <div style={{
            fontFamily: "var(--font-mono)", fontSize: 11.5,
            color: "var(--text-3)", marginTop: 3,
          }}>EHR <span style={{ color: "var(--text-2)", fontWeight: 500 }}>101035685</span></div>
        </div>

        <div style={{ position: "relative", display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span style={{
            background: "var(--surface)",
            border: "1px solid var(--hairline-strong)",
            borderRadius: 999,
            padding: "5px 12px",
            display: "inline-flex", alignItems: "center", gap: 8,
            fontFamily: "var(--font-mono)", fontSize: 11.5,
            color: "var(--text-2)", letterSpacing: "0.02em",
          }}>
            <span style={{
              fontSize: 10, color: "var(--text-3)",
              letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 600,
            }}>{t.quality_pill}</span>
            <span style={{ color: "var(--text)", fontWeight: 600 }}>{overall.completeness}%</span>
            <span style={{ color: "var(--text-3)" }}>{t.pct_complete}</span>
            <span style={{ color: "var(--hairline-strong)" }}>·</span>
            <span style={{ color: "var(--text)", fontWeight: 600 }}>{overall.confidence}%</span>
            <span style={{ color: "var(--text-3)" }}>{t.pct_confidence}</span>
          </span>
          <button
            aria-label="What does this mean?"
            onMouseEnter={() => setShowHelp(true)}
            onMouseLeave={() => setShowHelp(false)}
            onFocus={() => setShowHelp(true)}
            onBlur={() => setShowHelp(false)}
            style={{
              appearance: "none", border: "1px solid var(--hairline-strong)",
              background: "var(--surface)", color: "var(--text-3)",
              width: 22, height: 22, borderRadius: "50%",
              fontSize: 11, fontFamily: "var(--font-mono)", fontWeight: 600,
              cursor: "default",
              display: "inline-flex", alignItems: "center", justifyContent: "center",
            }}
          >i</button>
          {showHelp && (
            <div role="tooltip" style={{
              position: "absolute", top: "calc(100% + 10px)", right: 0,
              width: 280, padding: "11px 13px",
              background: "var(--text)", color: "var(--surface)",
              borderRadius: 8, fontSize: 12, lineHeight: 1.5,
              boxShadow: "0 12px 28px rgba(13,31,23,0.2)",
              zIndex: 30,
            }}>{t.quality_help}</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main ──────────────────────────────────────────────────────────────────
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "state": "complete",
  "lang": "en",
  "expanded_identity": true,
  "expanded_profile": true,
  "expanded_struct": true,
  "expanded_tech": true,
  "expanded_loc": true,
  "expanded_parts": true,
  "expanded_quality": true,
  "confDisplay": "icon"
}/*EDITMODE-END*/;

function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const { state, lang, confDisplay } = tweaks;
  const t = PD_COPY[lang] || PD_COPY.en;
  const vc = VALUE_COPY[lang] || VALUE_COPY.en;

  const sections = pdUseMemo(() => buildSections(t, vc, lang, state), [t, vc, lang, state]);
  const overall = pdUseMemo(() => overallQuality(sections), [sections]);

  const expandedMap = {
    identity: tweaks.expanded_identity,
    profile: tweaks.expanded_profile,
    struct: tweaks.expanded_struct,
    tech: tweaks.expanded_tech,
    loc: tweaks.expanded_loc,
    parts: tweaks.expanded_parts,
    quality: tweaks.expanded_quality,
  };

  const jumpToField = (key) => {
    // Find which section it's in, expand it, then scroll the field into view.
    const sec = sections.find((s) => !s.table && s.fields.some((f) => f.key === key));
    if (sec) setTweak(`expanded_${sec.id}`, true);
    // Defer scroll so the section has rendered.
    setTimeout(() => {
      const el = document.getElementById(`field-${key}`);
      if (el) {
        const top = el.getBoundingClientRect().top + window.scrollY - 180;
        window.scrollTo({ top, behavior: "smooth" });
        el.style.transition = "background-color 1.5s ease";
        el.style.backgroundColor = "rgba(200, 230, 211, 0.5)";
        setTimeout(() => { el.style.backgroundColor = "transparent"; }, 1200);
      }
    }, 80);
  };

  return (
    <BLShell screenLabel="03 Draft — Passport draft">
      <TopBar lang={lang} onLangChange={(v) => setTweak("lang", v)} />

      <IdentityStrip t={t} overall={overall} lang={lang} />

      <main style={{
        flex: 1, padding: "32px 24px 96px",
      }}>
        <div style={{
          width: "100%", maxWidth: 840, margin: "0 auto",
          display: "flex", flexDirection: "column", gap: 24,
        }}>
          <StepIndicator lang={lang} active={2} />

          {/* Title row + actions */}
          <div style={{
            display: "flex", alignItems: "flex-start", justifyContent: "space-between",
            gap: 24, flexWrap: "wrap",
          }}>
            <div style={{ flex: 1, minWidth: 280 }}>
              <h1 style={{
                margin: 0, fontSize: 30, lineHeight: 1.18,
                letterSpacing: "-0.02em", fontWeight: 600,
                color: "var(--text)", textWrap: "balance",
              }}>{t.title}</h1>
              <p style={{
                margin: "10px 0 0", fontSize: 15, lineHeight: 1.55,
                color: "var(--text-2)", maxWidth: 560, textWrap: "pretty",
              }}>{t.sub}</p>
            </div>
            <div style={{ display: "flex", gap: 12, alignItems: "center", flexShrink: 0, marginTop: 6 }}>
              <button style={{
                appearance: "none", border: 0,
                background: "transparent", color: "var(--text-2)",
                fontSize: 13, fontWeight: 500, cursor: "default",
                textDecoration: "underline", textDecorationColor: "var(--hairline-strong)",
                textUnderlineOffset: 3, padding: "10px 4px",
              }}>{t.regenerate}</button>
              <button style={{
                appearance: "none", border: 0,
                background: "var(--primary)", color: "#fff",
                height: 42, padding: "0 18px", borderRadius: 8,
                fontFamily: "var(--font-sans)", fontSize: 14, fontWeight: 600,
                letterSpacing: "-0.005em", cursor: "default",
                display: "inline-flex", alignItems: "center", gap: 8,
              }}>{t.review} <span aria-hidden style={{ fontFamily: "var(--font-mono)", fontWeight: 400 }}>→</span></button>
            </div>
          </div>

          {/* Sections */}
          {sections.map((sec) => (
            <SectionCard
              key={sec.id}
              section={sec}
              t={t}
              lang={lang}
              expanded={expandedMap[sec.id]}
              onToggle={() => setTweak(`expanded_${sec.id}`, !expandedMap[sec.id])}
              confDisplay={confDisplay}
            />
          ))}

          <QualitySection
            sections={sections}
            t={t}
            lang={lang}
            expanded={expandedMap.quality}
            onToggle={() => setTweak("expanded_quality", !expandedMap.quality)}
            onJumpToField={jumpToField}
          />
        </div>
      </main>

      <TweaksPanel>
        <TweakSection label={lang === "et" ? "Andmed" : "Data"} />
        <TweakRadio
          label={lang === "et" ? "Mustand" : "Draft"}
          value={state}
          options={["complete", "partial", "sparse"]}
          onChange={(v) => setTweak("state", v)}
        />
        <TweakSection label={lang === "et" ? "Sektsioonid" : "Sections"} />
        {[
          ["identity", t.sec_id], ["profile", t.sec_profile],
          ["struct", t.sec_struct], ["tech", t.sec_tech],
          ["loc", t.sec_loc], ["parts", t.sec_parts],
          ["quality", t.sec_quality],
        ].map(([id, label]) => (
          <TweakToggle
            key={id}
            label={label}
            value={tweaks[`expanded_${id}`]}
            onChange={(v) => setTweak(`expanded_${id}`, v)}
          />
        ))}
        <TweakSection label={lang === "et" ? "Esitlus" : "Presentation"} />
        <TweakRadio
          label={lang === "et" ? "Keel" : "Language"}
          value={lang}
          options={["et", "en"]}
          onChange={(v) => setTweak("lang", v)}
        />
        <TweakRadio
          label={lang === "et" ? "Kindlus" : "Confidence"}
          value={confDisplay}
          options={["icon", "label", "both"]}
          onChange={(v) => setTweak("confDisplay", v)}
        />
      </TweaksPanel>
    </BLShell>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
