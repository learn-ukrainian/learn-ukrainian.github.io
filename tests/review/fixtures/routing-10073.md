# Gemini native-review routing revision (#10073)

`routing-10073.json.gz` overlays the frozen routing baseline and the #10016
capacity revision. It changes only the catalog, role receipts, routing holders,
and reviewer receipts. Other captured surfaces retain their original fixtures.

The reviewer matrix grows from 1,480 to 1,504 inputs; the role matrix grows from
840 to 870. Every historical input is retained. The regression test compares
each historical review receipt and verifies that existing non-Google candidates
retain their eligibility, scores, and provenance. A changed selection must be
Gemini at low or medium risk. Separate boundary tests cover high/critical risk,
security paths, author independence, native endpoint identity, and exact-head
verdict publication and consumption.

The overlay was captured with the original byte-pinned capture script under
its hermetic host-CLI configuration. Fresh captures under both host-CLI states
and the no-CLI configuration must match the revised fixture. The test pins the
overlay digest separately. This fixture is deterministic regression evidence;
the accountable driver still owns the live review, independent approval, CI,
and landing proof.
