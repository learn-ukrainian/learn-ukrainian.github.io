# Windows bulk-source maintenance (storage topology v1)

Manual, repeatable, non-destructive maintenance for the **UkrainianData** NTFS
mirror. These scripts are the supported Windows entrypoints for the approved
storage topology.

## Rules

- Use **`rclone copy` only** — never `sync`, `purge`, or delete flags.
- Resolve the share with **`Get-SmbShare -Name UkrainianData`** and operate on
  the **local NTFS** `Path`. Never verify or copy through a UNC/SMB path.
- Write a **success receipt only after verification passes**.
- Do not put account emails, hostnames, IPs, secrets, or absolute operator home
  paths into tracked receipts or logs committed to git.
- Scheduled Task install is **optional and opt-in**; the default workflow is
  manual.

## Typical flow

```powershell
# 1) Copy from a pre-configured read-only Drive remote into local NTFS
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  .\scripts\storage\windows\Copy-BulkSourcesFromDrive.ps1

# 2) Verify markers (and optional exact-file manifest)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  .\scripts\storage\windows\Verify-BulkSources.ps1
```

Optional exact-file check: pass `-ManifestPath` with JSONL rows of
`path` (posix relative), `size`, and `sha256`.

Success tokens:

- Copy: `BULK_COPY_COMPLETE`
- Verify: `BULK_SOURCES_VERIFIED` plus a receipt under
  `<share>\staging\storage-topology\receipts\`

## Related

- Mac/agent status CLI: `python -m scripts.storage status`
- Runbook: `docs/runbooks/storage-topology.md`
- Shared rule: `agents_extensions/shared/rules/storage-topology.md`
