# Operator consult allowance

An operator consult allowance lets one parked or non-active catalog model take an ACP ask,
consult or discussion seat. Examples are Claude Fable 5.1 (`claude-fable-5-1`, no consult
role) and GPT-6 Astra (`gpt-6-astra`, red-team exception expired). The seat is limited to
the model, task or time window that the operator signed. Without a valid allowance, both
models are refused exactly as before.

An allowance never admits any of these:

- a review, critique or approval of record
- a sealed review
- an advisory (designated-approval) role
- resolver, ladder or substitution selection
- execution, writer or driver work

The verifier is `scripts/review/operator_allowance.py`.

## Why a signature

Any agent that runs as the host user can write files in that user's directories. A plain
local record would therefore let an agent grant itself an allowance. The record is signed
with an OpenSSH key that the operator keeps off this host, on their own device or a hardware
key. It is verified with `ssh-keygen -Y verify` against a signer file that only root can
change.

Fixed trust anchors (no environment variable, option, worktree file or argument changes them):

| Anchor | Value |
| --- | --- |
| Signer file | `/etc/learn-ukrainian/operator-allowance-signers` |
| Signer identity | `operator@learn-ukrainian` |
| Signature namespace | `lu-allowance` |
| Verifier binary | `/usr/bin/ssh-keygen` |

The verifier refuses the signer file when any of these is true:

- It is a symlink or not a regular file.
- It is not owned by root.
- It is group- or world-writable.
- A directory above it is not owned by root, or is group- or world-writable without the
  sticky bit.

The repository ships no signer file. Until the operator installs one, nothing is admitted.

**Residual risk:** an account with root can replace the signer file. This is the same trust
boundary as any other host secret. A task-scoped allowance admits only calls whose validated
task id equals the signed one. It narrows the seat to that task, but it does not
authenticate who is calling.

## One-time setup

1. On your own device, not this host, create the signing key. A hardware-backed key works
   too, for example `-t ed25519-sk`.

   ```bash
   ssh-keygen -t ed25519 -C operator@learn-ukrainian -f ~/.ssh/lu-allowance
   ```

2. On this host, install the public key as root:

   ```bash
   sudo install -d -o root -g root -m 0755 /etc/learn-ukrainian
   printf 'operator@learn-ukrainian namespaces="lu-allowance" %s\n' "$(cat lu-allowance.pub)" |
     sudo tee /etc/learn-ukrainian/operator-allowance-signers >/dev/null
   sudo chown root:root /etc/learn-ukrainian/operator-allowance-signers
   sudo chmod 0644 /etc/learn-ukrainian/operator-allowance-signers
   ```

   Copy only `lu-allowance.pub` to the host. The private key never goes there.

## Granting an allowance

1. On your device, write the record as canonical JSON: sorted keys, no spaces, and one
   trailing newline. `jq -cS` produces this form. Use the canonical catalog id; aliases are
   refused. Times are UTC in the form `YYYY-MM-DDTHH:MM:SSZ`.

   A window allowance lasts at most 24 hours:

   ```bash
   jq -cS -n '{schema:"lu-operator-allowance.v1", model:"gpt-6-astra", activity:"consult",
     scope:{kind:"window"}, order_ref:"chat-2026-11-05",
     issued_at:"2026-11-05T09:00:00Z", expires_at:"2026-11-06T09:00:00Z"}' > astra.json
   ```

   A task allowance admits only that task id:

   ```bash
   jq -cS -n '{schema:"lu-operator-allowance.v1", model:"claude-fable-5-1", activity:"consult",
     scope:{kind:"task", task_id:"cto-1234-consult"}, order_ref:"chat-2026-11-05",
     issued_at:"2026-11-05T09:00:00Z", expires_at:"2026-11-05T21:00:00Z"}' > fable.json
   ```

2. Sign it. This writes `astra.json.sig`:

   ```bash
   ssh-keygen -Y sign -f ~/.ssh/lu-allowance -n lu-allowance astra.json
   ```

3. Copy both files, unchanged, to this host's per-user record directory,
   `${XDG_CONFIG_HOME:-$HOME/.config}/learn-ukrainian/operator-allowances/`. Keep them as
   `<name>.json` and `<name>.json.sig`.

4. Optionally, check the signature on the host:

   ```bash
   ssh-keygen -Y verify -f /etc/learn-ukrainian/operator-allowance-signers \
     -I operator@learn-ukrainian -n lu-allowance -s astra.json.sig < astra.json
   ```

Each record is valid only while `issued_at <= now < expires_at`. To revoke one early, delete
its two files.

## What gets recorded

Every admitted call names its allowance under `operator_allowance`, both in the runner's usage
record and in the persisted ACP ask receipt. The entry gives the model, activity, scope, order
reference, `issued_at`, `expires_at` and the SHA-256 of the record.
