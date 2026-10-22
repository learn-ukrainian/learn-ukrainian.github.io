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

Each mistake gets one entry in the "Mistakes ledger" section of the CTO state file (local,
gitignored, private; never in public text):

- date (`date -u`), what happened as fact, impact;
- root cause in the CTO's process: ask why until you reach why the process allowed it
  ("I forgot" is not a cause);
- the change that prevents it; status (`open`, `changed`, `verified`); recurrence count.

Operator corrections are always entries, quoted only in the state file.

## 2. Change

An entry closes only through a concrete change: a skill or rule edit (PR), a checklist
item, or a tool check. `changed` means the change landed; `verified` means a later session
met the same situation and the change held. A lesson that changes nothing is not a lesson.

## 3. Escalate the control on a repeat

A repeat raises the recurrence count and moves the control one step up the ladder:
note, then skill text, then a checklist the CTO runs, then an automated check or guard in
a tool, dispatched as a reviewed PR. Text that failed once is not trusted a second time.

## 4. Read it

At session start read every open entry and the last ten closed ones before acting. The
pre-post self-audit ([decisions](decisions.md#before-posting)) lists the open entries as
known traps.

## 5. Measure it

The handoff scorecard counts new mistakes and repeats this session. A repeat of a
`verified` entry is reported to the operator with the next control step.
