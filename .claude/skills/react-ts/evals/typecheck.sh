#!/usr/bin/env bash
# Type-check the .ts/.tsx files an eval run produced, using the same strict
# settings as a Vite React-TS app (incl. erasableSyntaxOnly).
#
# Usage: evals/typecheck.sh <outputs-dir>
# Needs Node >= 20. Dependencies are installed once into a cache dir.
set -euo pipefail

OUT="$(cd "${1:?usage: typecheck.sh <outputs-dir>}" && pwd)"
CACHE="${TYPECHECK_CACHE:-${TMPDIR:-/tmp}/react-ts-typecheck}"

major="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$major" -lt 20 ]; then
  echo "Node >= 20 required (found $(node -v))" >&2
  exit 2
fi

# The source root is wherever src/ lives (outputs/src or outputs/frontend/src);
# loose files (e.g. a single fixed component) are checked from outputs/ itself.
SRC="$(find "$OUT" -type d -name src -not -path '*/node_modules/*' | head -1)"
SRC="${SRC:-$OUT}"

mkdir -p "$CACHE"
if [ ! -d "$CACHE/node_modules" ]; then
  (cd "$CACHE" && npm init -y >/dev/null && npm install --silent --no-audit --no-fund \
    typescript@5.8 react@19 react-dom@19 @types/react@19 @types/react-dom@19 vite@6 \
    @tanstack/react-query@5 msw@2 vitest@3 jsdom \
    @testing-library/react@16 @testing-library/dom@10 \
    @testing-library/user-event@14 @testing-library/jest-dom@6 zod@3)
fi

cat > "$CACHE/tsconfig.json" <<EOF
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true,
    "noEmit": true,
    "skipLibCheck": true,
    "types": ["vite/client", "vitest/globals", "@testing-library/jest-dom"],
    "baseUrl": "$SRC",
    "paths": { "@/*": ["./*"] }
  },
  "include": ["$SRC/**/*.ts", "$SRC/**/*.tsx", "$CACHE/css.d.ts"]
}
EOF
echo "declare module '*.css' { const c: Record<string, string>; export default c; }" > "$CACHE/css.d.ts"

# Let the outputs resolve packages from the cache.
ln -sfn "$CACHE/node_modules" "$SRC/node_modules"
trap 'rm -f "$SRC/node_modules"' EXIT

"$CACHE/node_modules/.bin/tsc" -p "$CACHE/tsconfig.json" --pretty false
echo "TYPECHECK OK: $SRC"
