import type {
  AmbiguousResolutionResponse,
  ResolutionResponse,
} from "../types";

export const resolvedFixture: ResolutionResponse = {
  status: "resolved",
  resolution_run_id: "resolution_lai_001",
  ehr_code: "101035685",
  normalized_address:
    "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4",
  address_aliases: ["Lai tn 1", "Nunne tn 4"],
  confidence_score: 0.92,
};

export const ambiguousFixture: AmbiguousResolutionResponse = {
  status: "ambiguous",
  resolution_run_id: "resolution_lai_ambiguous_001",
  candidates: [
    {
      ehr_code: "101035685",
      normalized_address:
        "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4",
      confidence_score: 0.92,
    },
    {
      ehr_code: "101035686",
      normalized_address: "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 3",
      confidence_score: 0.78,
    },
    {
      ehr_code: "101035690",
      normalized_address:
        "Harju maakond, Tallinn, Kesklinna linnaosa, Nunne tn 6",
      confidence_score: 0.64,
    },
  ],
};

export const unresolvedFixture: ResolutionResponse = {
  status: "unresolved",
  resolution_run_id: "resolution_lai_unresolved_001",
  candidates: [],
};
