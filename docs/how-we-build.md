# How we build Sprout

This guide is for Eli, Ca'Marion and Megan. It shows how to build one checkpoint, from task card to merged code, using Replit and the GitHub website. You won't need to type any commands.

Kayden is away on Monday 16 Nov, so everything you need to start is here.

## 1. The big picture

1. **The spec** (`docs/Sprout Master Specification v3.md`) says what to build.
2. **A task card** in the `tasks/` folder (for example `tasks/B3.md`) is the work order for one checkpoint.
3. **Your AI coding agent** writes the code from the card.
4. **GitHub Actions** tests every pull request automatically.
5. **A reviewer and a tester check it,** then it's merged into `main`.

A few words you'll see:

- **`main`:** the shared, finished version of the code.
- **Branch:** your own copy of the code, where you work without touching `main`.
- **Pull request (PR):** a request to add your branch's changes to `main`. It's where reviews, questions and test results live.
- **CI check:** an automatic test run on your pull request. Green means it passed; red means something failed.
- **Checkpoint:** a piece of the project from the spec, such as B3 or C1. Replit also uses the word "checkpoint" for its own save points; in this guide it always means a spec checkpoint.

## 2. This week's way of working

This week we use the simple flow in section 4: you, your agent and your pull request.

From **Monday 30 Nov** the team moves to an automated loop: a manager AI hands out task cards and retries failed tests for you. This guide will be updated then.

## 3. One-time setup

### 3.1 Import the repo into Replit

1. Sign in to Replit.
2. Choose **Create App**, then **Import from GitHub**.
3. Pick the repository **KaydenKamberi/Sprout** and import it.
4. When it opens, find the **Git** tool (in the Tools list, or search the tools for "Git"). This is where you switch branches, commit and push. Button names can differ slightly between Replit versions.

### 3.2 No Replit database

1. **Don't let Replit create its own database.** If Replit or Replit Agent offers to add one (PostgreSQL, Replit Database or SQLite), say no.
2. **Sprout uses MySQL 8.4 only.** Replit can't run MySQL, so backend tests don't run in Replit. They run on GitHub (GitHub Actions) every time you push to a pull request. That's normal.
3. Put this sentence in your first message to the agent every time: *"Do not create or use any Replit database or SQLite. This project uses MySQL 8.4 only. Backend tests run in GitHub Actions, not here."*

### 3.3 Connect Mistral and Google AI Studio

1. If you haven't already, connect both to the GitHub repo **KaydenKamberi/Sprout**:
   - **Mistral:** use its GitHub connector.
   - **Google AI Studio:** use its option to import or connect a GitHub repository.
2. If you can't find the option, ask in the team chat. You can still use them by pasting in a card or an error message.

## 4. Building one checkpoint (the simple flow)

### a. Check you're ready

1. Open your task card in `tasks/`. Read section 3, **"Depends on"**.
2. On GitHub, open the **Pull requests** tab, then **Closed**, and check every card your card depends on is **merged**. If one isn't, pick a different card from the table in section 6, or ask in the team chat.
3. In Replit's Git tool, switch to `main` and press **Pull**, so your copy is up to date.

### b. Create your branch

1. In Replit's Git tool, create a new branch.
2. Name it **exactly** as the card's header says (for example `b3-ingest`).
3. Check that the Git tool now shows your branch, not `main`.

### c. Give your agent the whole card

1. Open the task card and copy **all of it**, from the top line to the end. Don't summarise it.
2. Paste it into Replit Agent with a message like this:

   > "Build this task card exactly. Change only the files listed in its section 5. Follow its standing rules. Do not create or use any Replit database or SQLite. If the card doesn't answer something, stop and tell me instead of guessing."

### d. Pick the right tool

1. **Replit Agent** builds the checkpoint.
2. **Mistral or Google AI Studio** answer questions and make small fixes. This saves your Replit credits (about $20 each) for the big checkpoints (spec 3.9).

### e. Never copy code by hand out of a chat window

1. The agent edits the files in the repo directly.
2. If a chat answer contains code, give the answer to Replit Agent and let it make the change. Don't paste code into files yourself.

### f. Push and open the pull request

1. In Replit's Git tool, write a short message (for example "B3: ingest endpoint"), **commit** your changes, then **Push**.
2. On the GitHub website, open the repo. A yellow banner says your branch had recent pushes: press **Compare & pull request**.
   - No banner? Open **Pull requests**, then **New pull request**, and pick your branch.
3. Check the top says **base: main** and **compare: your branch**.
4. **Title:** the checkpoint ID first, exactly as in the card's header (for example `B3: Ingest endpoint`).
5. **Description:** say what you built in a few sentences, and list any questions (step h).
6. Press **Create pull request**.
7. When the checks finish (step g), copy the test results into the description:
   - press **Details** on a check and copy the test summary lines;
   - edit the description with the **...** menu, then **Edit**.

### g. Watch the CI checks

1. Scroll to the bottom of your pull request. There are three checks: **server**, **web** and **firmware**. They take a minute or two.
2. **Green tick:** all tests passed.
3. **Red cross:** one failed. Then:
   1. Press **Details** next to the red check.
   2. Open the step with the red mark and find the error.
   3. Copy the **exact** error text, not a summary.
   4. Give it to your agent: *"This test failed in GitHub Actions. Fix it without changing files outside the card's list."*
   5. Commit and push the fix **to the same branch**. The checks run again by themselves.
   6. Repeat until everything is green.
4. **Your branch is behind `main`** (GitHub shows an **Update branch** button): press it, then press **Pull** in Replit's Git tool.

### h. When the card or the spec doesn't answer something

1. Don't let the agent guess.
2. Write the question on your pull request:
   - open the **Conversation** tab;
   - type it in the comment box at the bottom;
   - say which card and which step it's about.
3. Each card's section 9, **"Stop and ask"**, lists the questions already known. If yours is one of them, use the card's suggested placeholder only if the card says to, and say so in the pull request.
4. Keep working on another part of the card while you wait.

### i. Review, test and merge

1. When the checks are green, **Kayden reviews** the pull request (spec 3.9 step 4). Changes he asks for go on the same branch.
2. **The tester checks it.** The tester is never the person who built it.
   - Frontend: Ca'Marion tests Megan's checkpoints (spec 3.7), and the other frontend person reviews any change to the shared files (`web/src/api/types.ts`, `web/src/components/`).
   - Other cards: the tester is agreed on the pull request.
3. **Megan witnesses any gate** (a "G" test in the spec) the checkpoint touches.
4. Then it's merged into `main`. **Nobody merges their own pull request.**

## 5. The standing rules

Copied word for word from spec 3.9. They're in every task card too.

- MySQL 8.4 only. Never use Replit's built-in database, SQLite or any other database.
- Never rename, remove or retype a field in section 8 or a column in section 9.
- Change only the files the card lists. Anything else needs a line in the pull request saying why.
- If this spec does not say, stop and ask in the pull request instead of inventing an answer.

## 6. Who builds what this week

| Card | Owner | Due (week of) | Depends on |
| --- | --- | --- | --- |
| [B1](../tasks/B1.md) Database schema | Kayden | 9 Nov | Nothing |
| [B2](../tasks/B2.md) Data simulator | Kayden | 9 Nov | B1 |
| [B3](../tasks/B3.md) Ingest endpoint | Eli | 16 Nov | B1, B2 |
| [B4](../tasks/B4.md) Device key auth | Eli | 16 Nov | B3 |
| [B16](../tasks/B16.md) Live server on Oracle Cloud | Eli | 16 Nov | Oracle access from Kayden; B1 to load species; B3 and B4 before a real stake posts |
| [B17](../tasks/B17.md) Provisioning tools | Eli | 16 Nov | B1 (the USB tool waits for answers to its questions) |
| [B5](../tasks/B5.md) Config reply | Eli | 30 Nov | B3, B4 |
| [B6](../tasks/B6.md) Read endpoints | Eli | 30 Nov | B1 |
| [C1](../tasks/C1.md) Dashboard shell | Ca'Marion | 16 Nov | Nothing |
| [C2](../tasks/C2.md) Live data | Ca'Marion | 30 Nov | C1, B6 (and B16 for the live server) |
| [C3](../tasks/C3.md) The chart | Ca'Marion | 30 Nov | C1, C2 |

Megan has no task card this week. Her design checkpoints (D1, D3, D4 and D6) don't need a coding tool. She reviews changes to the shared web files and witnesses gates.

Eli: B3 and B4 change the same file. Finish and merge B3 before starting B4.

## 7. When you're stuck

1. Write the question in your pull request, or in the team chat if you don't have a pull request yet.
2. Say **which card** and **which step** (for example "B3, step g").
3. Paste the **exact** error text, not a description of it.
