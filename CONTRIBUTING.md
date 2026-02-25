# Contributing to Veritix Python Service

Thanks for your interest in contributing! This guide covers everything you need to get started. Reading time: ~3 minutes.

---

## Local Setup

1. **Clone the repo and install dependencies:**

```bash
git clone https://github.com/your-org/veritix-python.git
cd veritix-python
make dev-setup
```

2. **Copy the example environment file and fill in required values:**

```bash
cp .env.example .env
```

At minimum, set `QR_SIGNING_KEY` (32+ characters) and `NEST_API_BASE_URL`.

3. **Start the stack with Docker:**

```bash
docker compose up -d
```

The API will be available at `http://localhost:8000`.

---

## Branch Naming

Use one of these prefixes:

| Prefix   | Use for                     |
| -------- | --------------------------- |
| `feat/`  | New features                |
| `fix/`   | Bug fixes                   |
| `docs/`  | Documentation only          |
| `test/`  | Tests only                  |
| `ci/`    | CI/CD pipeline changes      |
| `chore/` | Dependency updates, tooling |

**Examples:** `feat/add-bulk-qr-endpoint`, `fix/etl-pagination-bug`, `docs/api-reference`

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type: short description (max 72 chars)
```

**Types:** `feat`, `fix`, `docs`, `test`, `ci`, `chore`, `refactor`, `perf`

**Examples:**

```
feat: add batch QR generation endpoint
fix: handle missing sale_date in ETL transform
docs: add api-reference.md and etl-pipeline.md
```

---

## Pull Request Requirements

- **Must close an existing issue** — include `Closes #<issue_number>` in the PR description.
- **Must pass CI** — all checks in `.github/workflows/ci.yml` must be green.
- **Must include tests** — new behaviour requires new or updated tests; coverage must not decrease.
- **Must update docs** — if you change an endpoint or config option, update `docs/api-reference.md` or `docs/etl-pipeline.md` accordingly.

---

## Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make coverage

# Run a specific test file
pytest tests/test_etl.py -v
```

Coverage is enforced in CI. Keep it at or above the current baseline.

---

## Code Style

We use three tools — all enforced in CI:

| Tool      | Purpose              | Run locally         |
| --------- | -------------------- | ------------------- |
| **Black** | Code formatting      | `black src/ tests/` |
| **isort** | Import sorting       | `isort src/ tests/` |
| **mypy**  | Static type checking | `mypy src/`         |

Run all three before pushing:

```bash
black src/ tests/ && isort src/ tests/ && mypy src/
```

Or use the Makefile shortcut if available:

```bash
make lint
```

---

## Questions?

Open a [discussion](../../discussions) or leave a comment on the relevant issue. We're happy to help.
