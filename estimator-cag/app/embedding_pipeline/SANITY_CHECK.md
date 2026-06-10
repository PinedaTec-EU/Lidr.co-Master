# Sanity Check

Status: completed

## Pair A - Semantically close texts

Text 1: `OAuth 2.0 authentication backend with JWT tokens for fintech mobile app`

Text 2: `Authorization service using JSON Web Tokens for a banking application`

Expected interpretation: high similarity, because both texts describe authentication and authorization flows in a financial product context.

Observed similarity: `0.5957`

## Pair B - Unrelated texts

Text 1: `OAuth 2.0 authentication backend with JWT tokens for fintech mobile app`

Text 2: `Database migration from MySQL to PostgreSQL with zero downtime`

Expected interpretation: low similarity, because one text is about auth for a fintech app and the other is about infrastructure migration.

Observed similarity: `0.1920`

## Pair C - Generic and ambiguous texts

Text 1: `Backend services`

Text 2: `API development`

Expected interpretation: ambiguous. A moderate similarity would not be surprising because both descriptions are short and generic.

Observed similarity: `0.5407`

## Notes

The results are directionally correct for a minimum pipeline:

- Pair A is clearly much closer than Pair B, even if it stays just below the aspirational `> 0.6` threshold from the exercise text.
- Pair B is comfortably low, which is the most important sanity signal for this phase because it shows the embeddings separate auth semantics from database migration work.
- Pair C is relatively high for two short generic texts. That is not surprising: both phrases live in the same broad backend/API semantic neighborhood and provide very little disambiguating context.

What this tells us:

- The pipeline works end to end and the embeddings are usable for basic discrimination.
- Very short or generic texts can cluster more than intuition might suggest, which is exactly why contextual chunk headers matter in the main ingestion flow.
