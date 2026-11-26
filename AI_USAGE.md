# AI Usage

GitHub Copilot and ChatGPT-style assistance were used to inspect requirements and implement the Python/FastAPI solution.

Main prompts covered workspace inspection, project structure, tenant isolation, transaction validation, idempotency, balances, reversal/audit behavior, tests, and documentation.

Accepted suggestions were the FastAPI/SQLAlchemy separation, Pydantic validation, database unique constraints, and compensating reversal entries.

Rejected or modified suggestions that could weaken isolation, use floats for money, overwrite transaction history, or return cross-tenant data.

The implementation was manually reviewed for route scoping and financial semantics, and validated with isolated pytest runs and application startup checks.
