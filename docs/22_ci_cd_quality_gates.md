# Milestone 22 — CI/CD and Automated Quality Gates

## Objective

M22 adds a lightweight, deterministic GitHub Actions quality gate before changes are considered production-ready. It does not redesign deployment, call production services, alter database objects or data, or move Render deployment into GitHub Actions.

## CI Architecture

```text
Developer change
      ↓
Git commit / push or pull request
      ↓
GitHub Actions CI
      ↓
Compile + repository safety + deterministic tests
      ↓
PASS → eligible for the existing Render deployment path
FAIL → fix before considering the change production-ready
```

GitHub Actions and Render are separate systems. CI validates source changes. Render continues to deploy the Git-backed Streamlit service through its existing configuration. Neon remains the managed PostgreSQL service, and Gemini remains the governed external planning provider. The workflow does not require Render API keys and does not invoke a deployment hook.

## Workflow

File: `.github/workflows/ci.yml`

Triggers:

- Pushes to `main`
- Pull requests targeting `main`

The single `quality-gates` job runs on `ubuntu-latest`, uses Python 3.12, has read-only repository permissions, and has a 20-minute timeout.

Steps:

1. Check out the repository.
2. Set up Python 3.12 and cache pip downloads using `requirements.txt` as the cache key input.
3. Install declared dependencies and pytest.
4. Compile Python under `etl`, `streamlit_app`, `tests`, `database`, and `scripts`.
5. Run the repository safety check.
6. Run the focused deterministic tests.

## Selected Tests

The default CI suite reuses existing tests:

- `test_anomalies.py` — robust anomaly guardrails and completed periods
- `test_portfolio.py` — Product/Seller concentration and signal rules
- `test_comparisons.py` and `test_insight_comparisons.py` — Compare Mode, KPI explanation, scope, and causal wording
- `test_health.py` — deterministic Business Health scoring
- `test_forecasting.py` — forecasting metrics, backtesting, guardrails, models, and M20 failure isolation
- `test_assistant.py` — approved deterministic planning and filter behavior
- `test_assistant_ranking.py` — ranking direction, metric-aware charts, and stable widget keys
- `test_assistant_security.py` — SQL allowlists, structural validation, bounded results, and adversarial prompts
- `test_assistant_trends.py` — monthly semantics, causality guardrail, append-only history, and mocked provider failure

These tests are deterministic and require no production credentials.

## Intentionally Excluded Tests

- Live database milestone validators and reconciliation scripts require a populated PostgreSQL instance and are reserved for focused local/release validation.
- Streamlit `AppTest` milestone validators traverse database-backed pages and are excluded from ordinary CI for the same reason.
- Live Neon production validation is not run from pull requests.
- Live Gemini calls are excluded to avoid secrets, quota usage, network variability, and non-determinism. Existing tests cover provider failure with mocks/fakes.
- Full historical M9–M21 regression is not duplicated in every push; it remains a milestone/release validation tool.

## Repository and Secret Safety

`scripts/check_repository_safety.py` reads tracked path names with `git ls-files`; it never opens secret files or prints secret values. CI fails if Git tracks:

- `.env` or another non-example `.env*` file
- `.streamlit/secrets.toml`
- `docs/API key details.txt`
- `*.dump`, `*.backup`, or `*.bak` database exports

The script also requires placeholder-only values for database fields and `AI_API_KEY` in `.env.example`. Provider name, model, and public API base URL remain normal non-secret configuration.

This is intentionally a simple repository guard, not a replacement for GitHub secret scanning or a full credential-detection platform.

## Failure Behavior

Any failed install, compile, repository-safety check, or test makes the job fail. The workflow has no deployment step, so a failed job cannot directly modify Render, Neon, Gemini, database objects, or business data. Repository branch protection should require the CI check before merging if strict enforcement is desired.

## Developer Workflow

Before pushing, run the same gates from the repository root:

```bash
python -m compileall -q etl streamlit_app tests database scripts
python scripts/check_repository_safety.py
python -m pytest -q tests/test_anomalies.py tests/test_assistant.py tests/test_assistant_ranking.py tests/test_assistant_security.py tests/test_assistant_trends.py tests/test_comparisons.py tests/test_forecasting.py tests/test_health.py tests/test_insight_comparisons.py tests/test_portfolio.py
```

When a change touches a live integration or database-backed page, additionally run only the corresponding existing focused validator outside ordinary CI. After CI passes and reviewed code reaches the Render deployment branch, use the M21 production smoke workflow: health endpoint, directly affected page, representative read-only database check, and one governed Assistant request only when Assistant behavior changed.
