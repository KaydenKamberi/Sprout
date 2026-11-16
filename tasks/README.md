# Task cards

Every checkpoint gets one task card in this folder, named after the checkpoint:
`tasks/<checkpoint>.md`, for example `tasks/B3.md`.

Kayden writes the cards with Claude Code from the spec (`docs/Sprout Master Specification v3.md`),
in weekly batches, a week ahead of their due week. The owner reads the card and agrees to it
before their coding agent touches any code. The owner then makes a branch named after the
checkpoint (for example `b3-ingest`) and gives the card to their agent.

## What a card holds (spec 3.9, step 1)

- The checkpoint and its "Done when".
- The spec sections it depends on, copied in, not linked.
- The files it may create or change.
- The test or gate that proves it.
- The standing rules below.

## Standing rules in every task card (spec 3.9)

- MySQL 8.4 only. Never use Replit's built-in database, SQLite or any other database.
- Never rename, remove or retype a field in section 8 or a column in section 9.
- Change only the files the card lists. Anything else needs a line in the pull request saying why.
- If this spec does not say, stop and ask in the pull request instead of inventing an answer.
