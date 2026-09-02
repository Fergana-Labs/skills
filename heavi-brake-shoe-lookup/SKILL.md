---
name: heavi-brake-shoe-lookup
description: Identify heavy-truck brake shoes from a VIN and fitment details using Heavi's trusted sources in the right order. Use for brake-shoe lookup, fitment, supersession, and cross-reference questions.
---

# brake-shoe lookup

Identify the brake shoe only when the available evidence uniquely supports one fitment. This skill
encodes Heavi's lookup workflow but contains no customer data.

For an example of how the evidence fits together, read
[references/example-catalog.md](references/example-catalog.md).

## Required evidence

A VIN is a starting point, not a fitment answer. Establish:

- vehicle or build identifier;
- axle position: steer, drive, or trailer;
- brake dimensions or brake family; and
- any configuration that distinguishes two shoes with the same dimensions.

Do not ask the customer for information that an available source can answer.

## Source order

1. Consult the OE build source for the vehicle's as-built brake configuration.
2. Consult the Heavi cheat sheet for known fitments, normalized part numbers, and supersessions.
3. If the result is still ambiguous, ask one question for the missing discriminator.
4. Confirm the candidate in an authoritative manufacturer catalog.
5. Use open-web search only to locate an authoritative source, never as fitment evidence by itself.

Retail listings, search snippets, and repeated unsourced claims do not become authoritative through
agreement.

## Decide

Return a part number only when the fitment keys identify one current part and the authoritative
sources do not conflict.

Keep these relationships distinct:

- **direct fit** — explicitly fits the resolved configuration;
- **supersession** — the manufacturer replaced an older number with a current number; and
- **cross-reference** — another supplier claims interchange, which is not proof of fitment.

Never turn a cross-reference into a supersession or infer fitment from dimensions alone. If sources
conflict or a required discriminator is unavailable, say that the part is not yet identified and
name the exact evidence needed.

## Answer

Give the customer:

- the current part number, or a clear unresolved result;
- the fitment facts used;
- the authoritative sources that support the conclusion; and
- any superseded number, labeled as superseded.

Do not expose internal search steps or pad the answer with alternative parts that were ruled out.
