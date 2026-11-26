Implemented tenant authentication, scoped CRUD-style transaction APIs, validation, idempotency, Decimal balances, audit logs, and reversals.
Tenant API keys are hashed and resolved from the database; no request-supplied tenant ID is accepted.
Critical financial features were prioritized before optional bulk and summary endpoints.
Currency is validated to USD/EUR/GBP and balances are calculated independently per currency.
Transfer semantics: the source client decreases and the related destination client increases.
Reversals create compensating entries and mark originals REVERSED, so history is retained.
Bulk import and monthly/historical summaries were skipped to protect core correctness within the time limit.
Main risks are SQLite concurrency, key rotation, and horizontal scaling without a migration-safe design.
At 100x load, move to PostgreSQL, pool connections, add indexes/partitioning, and use an idempotency transaction strategy.
