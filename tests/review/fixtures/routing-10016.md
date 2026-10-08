# Review capacity fixture (#10016)

`routing-10016.json.gz` overlays only the reviewer surface of the immutable
`tests/fixtures/routing_baseline` fixtures. Their capture harness, inputs,
occurrence ledger, original receipts and pinned hashes remain unchanged.

The approved AC-01 rule changes review allowance eligibility and pace ordering.
The existing capture harness generated identical review bytes in its host-CLI
and no-CLI configurations, without permitting provider execution. All other
surfaces, including writer routing and dispatch, matched the original fixtures.

The denominator remains 1,480 reviewer cases. Of those, 1,136 receipts change:
capacity evidence and the leading pace-ordering score account for all but 24
semantic differences. Those 24 have a legacy `near_cap` or `hot` label with no
numeric allowance. Eight change selection from Grok to the appropriate Claude
reviewer because the label alone no longer proves exhaustion. The other 16
preserve selection while separating explicit health from quota labels.

`test_review_capacity_fixture_is_pinned_and_scope_bounded` independently pins
the overlay digest and limits semantic differences to those inputs. Fresh
captures and every parametrized reviewer case still compare complete receipts
exactly. Dedicated capacity tests cover numeric reserve boundaries, fresh and
stale observations, pace ordering, live/file equivalence and admission limits.
