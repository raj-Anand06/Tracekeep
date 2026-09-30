# Tracekeep web

The public product surface for Tracekeep. It renders a complete synthetic handoff immediately and connects to the local read-only demo API when it is available.

## Run locally

From the Tracekeep repository root:

```bash
make demo
make api
make web
```

The website runs at `http://localhost:3000` and the demo API at `http://localhost:8000`.

## Checks

```bash
npm --prefix apps/web run lint
npm --prefix apps/web test
```

Set `NEXT_PUBLIC_TRACEKEEP_API_URL` when the API is hosted somewhere other than `http://localhost:8000`.
