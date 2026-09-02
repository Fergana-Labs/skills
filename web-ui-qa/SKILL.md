---
name: web-ui-qa
description: Verify web UI behavior by operating the real application in a browser and collecting evidence from the page, console, and network. Use when asked to manually test a frontend workflow, reproduce a UI bug, validate a visual change, or provide browser-based QA evidence. Do not use as a substitute for writing automated tests when the request specifically calls for test coverage.
---

# Web UI QA

Exercise the product as a user would and report what actually happened. A passing build or unit
test is supporting evidence, not proof that a browser workflow works.

## Prepare

- Read the repository instructions and the code or change under test before launching anything.
- Turn the request into observable success criteria: starting state, user action, and expected page
  state.
- Use the project's documented local startup and authentication path. Keep server output available
  so browser failures can be matched to application errors.
- Test production or another shared environment only when the user explicitly put it in scope.
- If required credentials, fixtures, or services are unavailable, report the exact blocker. Do not
  invent data, bypass authentication, or quietly switch environments.

## Exercise the workflow

Use the available browser automation tool so every step is reproducible.

1. Set a deliberate viewport and begin at the user-visible entry point for the workflow.
2. Reach the target state through visible controls. Deep-link only when the workflow itself starts
   at that URL.
3. Perform the requested actions and verify the resulting UI state, not merely that a click
   succeeded.
4. Inspect browser console errors and failed network requests after meaningful transitions.
5. Test the closest relevant boundary: the original failure case for a bug fix, one invalid action
   for a form, or a nearby width for responsive behavior.

Keep the test matrix proportional. One complete happy path and one meaningful boundary usually
provide better evidence than many shallow variations.

When QA accompanies an implementation, reproduce the issue before editing when practical. After
the change, reload from a clean state and repeat the exact workflow. Run focused automated tests as
additional regression coverage when the repository has them.

## Capture evidence

Take screenshots only when appearance or transient page state matters. Keep review-only images
outside the repository unless the user requested them as project artifacts.

Report:

- environment and viewport;
- exact workflow exercised;
- expected and observed results;
- relevant console or network findings;
- automated checks run; and
- anything not tested, with the reason.

Do not claim a workflow passed if any required step was skipped. On a review-only request, report
failures without changing the application unless the user also asked for a fix.
