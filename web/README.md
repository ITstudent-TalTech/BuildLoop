# BUILDLoop Frontend

BUILDLoop is a mocks-first Next.js frontend for generating and reviewing digital building passports from Estonian construction register data. Track 1 is the frontend MVP: intake, resolution, draft review, publication confirmation, and component playground all run against local API fixtures.

## Project Notes

- Frontend instructions: [AGENTS.md](./AGENTS.md)
- Brand tokens and tone: [BRAND.md](./BRAND.md)
- This app is mocks-only for now. Real backend integration is Track 2 work.

## Quick Start

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Demo URLs

- `/` — landing page
- `/intake` — address intake form
- `/passport/demo-project-id` — passport draft view, controlled by `MOCK_DRAFT_VARIANT`
- `/dev/components` — component playground

## Mock Controls

Set these in `.env.local` and restart the dev server:

- `MOCK_DELAY_MS=500` controls artificial mock API latency.
- `MOCK_RESOLUTION_MODE=resolved` can be `resolved`, `ambiguous`, or `unresolved`.
- `MOCK_DRAFT_VARIANT=complete` can be `complete`, `partial`, or `sparse`.
- `MOCK_FAIL_NEXT=503:server_unavailable:Database is down` forces the next mock API call to fail once.
