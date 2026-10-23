# Learning from mistakes

A closed loop for the CTO's own mistakes: a wrong claim, a wasted seat, a missed check, an
operator correction. Practices used: blameless postmortems (Google SRE book, ch. 15),
the "5 whys" (Toyota Production System), corrective and preventive action tracking (CAPA,
ISO 9001 § 10.2) and the hierarchy of controls (NIOSH): prefer the control that removes the
hazard over the one that asks a person to remember.

Where things go: CTO process mistakes go in this private ledger; system and production
defects go in `docs/bug-autopsies/` (public, one per root cause); consequential decisions
go in the decision journal (`docs/decisions/`).

## 1. Record

Each mistake gets one private tracker item: `lu-driver-state add --lane cto --kind commitment`
with an alias prefixed `ML-`, an owner and a done condition:

- statement: date (`date -u`), what happened as fact, impact and root cause in the CTO's
  process. Ask why until you reach why the process allowed it ("I forgot" is not a cause);
- done-when: the corrective change landed;
- evidence: the PR or commit, recorded with `lu-driver-state evidence <id>`.

Operator corrections are always entries, kept private in the tracker.

## 2. Change

An entry closes only through a concrete change: a skill or rule edit (PR), a checklist
item, or a tool check. Record the landed PR or commit with `evidence` before setting
`status <id> done --reason <reason>`. Record later verification with `note`: a later session
met the same situation and the change held. A lesson that changes nothing is not a lesson.

## 3. Escalate the control on a repeat

A repeat is a `lu-driver-state note <id> <text>` on the same item, with the recurrence count.
Reopen it with `status` if the corrective work is unfinished. Move the control one step up the ladder:
note, then skill text, then a checklist the CTO runs, then an automated check or guard in
a tool, dispatched as a reviewed PR. Text that failed once is not trusted a second time.

## 4. Read it

At session start use `lu-driver-state list --lane cto --kind commitment --all` to locate
the `ML-` items, then `show <id>` for every open entry and the last ten done ones. The
pre-post self-audit ([decisions](decisions.md#before-posting)) lists the open entries as
known traps.

## 5. Measure it

The handoff scorecard counts new mistakes and repeats this session. A repeat of a
previously verified correction is reported to the operator with the next control step.
