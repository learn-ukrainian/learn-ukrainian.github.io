"""Closed-schema GitHub publishing; public bytes are scanned once and replayed.

Call publish(verb, ...typed fields...) or use python -m scripts.publish.
There is no argv, arbitrary endpoint, GraphQL document or payload passthrough.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

from scripts.common import github_client
from scripts.opsec import prepublish as gate
from scripts.opsec.gh_snapshot import repository

# Each field has one type and one meaning; strings never select gh flags.
COMMON = {"repo": "repo"}
TEXT = {"title": "text", "body": "text", "body_file": "file"}
EDIT = {**TEXT, "add_labels": "texts", "remove_labels": "texts", "milestone": "text"}
ASSETS = {"assets": "assets"}
SCHEMAS = {
    "issue-create": ({"title", "body"}, {**COMMON, **TEXT, "labels": "texts", "milestone": "text"}),
    "issue-edit": ({"number"}, {**COMMON, **EDIT, "number": "number", "remove_milestone": "bool"}),
    "issue-comment": ({"number", "body"}, {**COMMON, "number": "number", "body": "text", "body_file": "file"}),
    "issue-comment-json": ({"number", "body"}, {**COMMON, "number": "number", "body": "text", "body_file": "file"}),
    "issue-close": ({"number"}, {**COMMON, "number": "number", "comment": "text", "reason": "reason"}),
    "pr-create": (
        {"title", "body", "base", "head"},
        {**COMMON, **TEXT, "base": "text", "head": "text", "draft": "bool"},
    ),
    "pr-edit": ({"number"}, {**COMMON, **EDIT, "number": "number"}),
    "pr-comment": ({"number", "body"}, {**COMMON, "number": "number", "body": "text", "body_file": "file"}),
    "pr-review": (
        {"number", "verdict"},
        {**COMMON, "number": "number", "verdict": "verdict", "body": "text", "body_file": "file"},
    ),
    "pr-merge": (
        {"number"},
        {**COMMON, "number": "number", "subject": "text", "body": "text", "body_file": "file", "match_head": "sha"},
    ),
    "pr-update-branch": ({"number"}, {**COMMON, "number": "number"}),
    "pr-ready": ({"number"}, {**COMMON, "number": "number"}),
    "pr-close": ({"number"}, {**COMMON, "number": "number"}),
    "issue-reopen": ({"number"}, {**COMMON, "number": "number"}),
    "run-rerun": ({"number"}, {**COMMON, "number": "number"}),
    "workflow-run": (
        {"workflow", "ref"},
        {**COMMON, "workflow": "workflow", "ref": "ref", "inputs": "workflow_inputs"},
    ),
    "pr-disarm": ({"number"}, {**COMMON, "number": "number"}),
    "pr-dequeue": ({"node_id"}, {**COMMON, "node_id": "node"}),
    "release-create": (
        {"tag"},
        {
            **COMMON,
            "tag": "text",
            "title": "text",
            "notes": "text",
            "notes_file": "file",
            "target": "text",
            "draft": "bool",
            "prerelease": "bool",
            **ASSETS,
        },
    ),
    "release-edit": (
        {"tag"},
        {
            **COMMON,
            "tag": "text",
            "title": "text",
            "notes": "text",
            "notes_file": "file",
            "draft": "bool",
            "prerelease": "bool",
        },
    ),
    "release-upload": ({"tag", "assets"}, {**COMMON, "tag": "text", **ASSETS, "clobber": "bool"}),
    "gist-create": ({"files"}, {"files": "assets", "description": "text", "public": "bool"}),
    "label-create": (
        {"name", "color"},
        {**COMMON, "name": "text", "color": "color", "description": "text", "force": "bool"},
    ),
    "label-edit": ({"name"}, {**COMMON, "name": "text", "new_name": "text", "color": "color", "description": "text"}),
    "milestone-create": ({"title"}, {**COMMON, "title": "text", "description": "text", "state": "state"}),
    "milestone-edit": (
        {"number"},
        {**COMMON, "number": "number", "title": "text", "description": "text", "state": "state"},
    ),
    "commit-status": (
        {"sha", "state", "context", "description"},
        {**COMMON, "sha": "sha", "state": "status", "context": "text", "description": "text"},
    ),
    "issue-link": (
        {"parent_id", "child_id"},
        {**COMMON, "parent_id": "node", "child_id": "node", "replace_parent": "bool"},
    ),
    "issue-unlink": ({"parent_id", "child_id"}, {**COMMON, "parent_id": "node", "child_id": "node"}),
}
WORKFLOWS = {"ci.yml": {}, "deploy-pages.yml": {}}

ENUMS = {
    "workflow": set(WORKFLOWS),
    "reason": {"completed", "not planned"},
    "verdict": {"approve", "comment", "request-changes"},
    "state": {"open", "closed"},
    "status": {"success", "failure", "error", "pending"},
}
PATTERNS = {
    "repo": r"(?:[A-Za-z0-9.-]+/)?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
    "ref": r"[A-Za-z0-9_][A-Za-z0-9_./-]*",
    "sha": r"[0-9a-fA-F]{40}",
    "node": r"[A-Za-z0-9_=-]+",
    "color": r"[0-9a-fA-F]{6}",
}


def _validated_environment(env) -> dict[str, str]:
    """Copy the environment and refuse malformed GH_HOST even without a repo."""
    environment = dict(os.environ if env is None else env)
    if "GH_HOST" in environment:
        hostname = gate.normalize_hostname(environment["GH_HOST"])
        if hostname is None:
            raise gate.PublishBlocked("OPSEC: invalid publisher hostname.")
        environment["GH_HOST"] = hostname
    return environment


def _hostname_flag(dest: str) -> list[str]:
    """Select an API host from a destination already validated by the resolver."""
    if dest == "unknown":
        return []
    host = dest.split("/", 1)[0]
    return [] if host == "github.com" else ["--hostname", host]


def _validate(verb, fields):
    if verb not in SCHEMAS:
        raise gate.PublishBlocked("OPSEC: unknown publisher verb.")
    required, schema = SCHEMAS[verb]
    if set(fields) - set(schema):
        raise gate.PublishBlocked("OPSEC: unknown publisher field.")
    effective = (
        set(fields) | ({"body"} if "body_file" in fields else set()) | ({"notes"} if "notes_file" in fields else set())
    )
    if required - effective:
        raise gate.PublishBlocked("OPSEC: required publisher field missing.")
    for key, value in fields.items():
        kind = schema[key]
        valid = True
        if kind == "bool":
            valid = type(value) is bool
        elif kind == "number":
            valid = type(value) is int and value > 0
        elif kind == "file":
            valid = isinstance(value, (str, Path))
        elif kind == "texts":
            valid = isinstance(value, (list, tuple)) and all(isinstance(x, str) for x in value)
        elif kind == "workflow_inputs":
            valid = isinstance(value, dict) and not value  # admitted workflows have no inputs
        elif kind == "assets":
            valid = isinstance(value, (list, tuple)) and bool(value) and all(isinstance(x, Asset) for x in value)
        elif kind in ENUMS:
            valid = isinstance(value, str) and value in ENUMS[kind]
        elif kind in PATTERNS:
            valid = isinstance(value, str) and re.fullmatch(PATTERNS[kind], value) is not None
        else:
            valid = isinstance(value, str) and "\0" not in value
        if not valid:
            raise gate.PublishBlocked(f"OPSEC: invalid publisher field {key}.")
    if verb == "pr-create" and any(not fields.get(key) for key in ("base", "head")):
        raise gate.PublishBlocked("OPSEC: PR creation requires explicit base and head names.")
    for name in ("body", "notes"):
        if name in fields and name + "_file" in fields:
            raise gate.PublishBlocked("OPSEC: use one text input per field.")


class Asset:
    """An explicit artifact source and public name; local paths are never public text."""

    def __init__(self, path: str | Path, name: str | None = None):
        self.path = Path(path)
        self.name = name if name is not None else self.path.name
        if (
            not isinstance(self.name, str)
            or not re.fullmatch(r"[^/\\\x00-\x1f\x7f#]+", self.name)
            or self.name in {".", ".."}
        ):
            raise gate.PublishBlocked("OPSEC: invalid artifact name.")


def _read_file(path, cwd, stdin):
    try:
        if str(path) == "-":
            value = stdin if stdin is not None else sys.stdin.buffer.read()
            return value.encode("utf-8") if isinstance(value, str) else bytes(value)
        resolved = Path(path)
        if not resolved.is_absolute():
            resolved = cwd / resolved
        return resolved.read_bytes()
    except Exception:
        raise gate.PublishBlocked("OPSEC: publisher file input unreadable.") from None


def _send(argv, *, environment, runner, cwd, **kwargs):
    """Send already-admitted bytes through the shared GitHub client."""
    environment = gate.internal_environment(environment)
    if runner is None:
        environment["AGENT_REAL_GH"] = gate.real_gh(environment)
    if runner is not None:
        return github_client.command(argv, runner=runner, env=environment, cwd=cwd, **kwargs)
    return _run_transport(argv, env=environment, cwd=cwd, **kwargs)


def _run_transport(command, **kwargs):
    return github_client.run(command, **kwargs)


SQUASH_TEXT_QUERY = (
    "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){"
    "pullRequest(number:$number){headRefOid isMergeQueueEnabled "
    "viewerMergeHeadlineText(mergeType:SQUASH) viewerMergeBodyText(mergeType:SQUASH)}}}"
)


def _squash_text(gh_repo, fields, dest, temp, runner, cwd, environment):
    """Read GitHub's default squash subject and body for the pinned head."""
    owner, name = gh_repo.split("/", 1)
    query = temp / "squash-text.json"
    variables = {"owner": owner, "name": name, "number": fields["number"]}
    query.write_bytes(json.dumps({"query": SQUASH_TEXT_QUERY, "variables": variables}).encode("utf-8"))
    try:
        result = runner(
            ["gh", "api", "--method", "POST", "graphql", "--input", str(query), *_hostname_flag(dest)],
            cwd=cwd,
            env=dict(environment),
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        pull = json.loads(result.stdout)["data"]["repository"]["pullRequest"] if result.returncode == 0 else None
        subject, body = pull["viewerMergeHeadlineText"], pull["viewerMergeBodyText"]
        if not (
            isinstance(subject, str)
            and isinstance(body, str)
            and type(pull["isMergeQueueEnabled"]) is bool
            and isinstance(pull["headRefOid"], str)
            and pull["headRefOid"].lower() == fields["match_head"].lower()
        ):
            raise ValueError
    except github_client.GitHubRateLimited:
        raise
    except Exception:
        raise gate.PublishBlocked("OPSEC: merge refused: squash text unverifiable.") from None
    return {"subject": subject, "body": body, "queue": pull["isMergeQueueEnabled"]}


@github_client.rate_limited_command
def publish(
    verb: str,
    *,
    runner=None,
    cwd=None,
    env=None,
    stdin=None,
    capture_output=False,
    text=False,
    check=False,
    timeout=None,
    stdout=None,
    stderr=None,
    **fields,
):
    """Validate closed fields, freeze source bytes, scan, then send the same bytes.

    Transport options do not carry payloads. Injected runners exercise exactly
    the same validation, scanning and snapshots as the real gh transport.
    """
    _validate(verb, fields)
    fields = {
        key: tuple(value) if SCHEMAS[verb][1][key] in {"texts", "assets"} else value for key, value in fields.items()
    }
    if verb in {"issue-edit", "pr-edit", "release-edit"} and not (set(fields) - {"number", "tag", "repo"}):
        raise gate.PublishBlocked("OPSEC: edit requires explicit fields; interactive publishing refused.")
    environment = _validated_environment(env)
    cwd = Path(cwd or Path.cwd())
    dest = "unknown" if verb == "gist-create" else repository(cwd, environment, fields.get("repo"))
    if dest == "unknown" and verb != "gist-create":
        raise gate.PublishBlocked("OPSEC: publisher repository unresolved; provide --repo.")
    # Pin the proven destination in argv; never let gh resolve it differently.
    if dest != "unknown":
        environment["GH_HOST"] = dest.split("/", 1)[0]
    gh_repo = dest.split("/", 1)[1] if dest != "unknown" else ""
    texts, names = [], []

    def scan(name, value):
        texts.append(value)
        names.append(name)

    with tempfile.TemporaryDirectory(prefix="lu-publish-") as directory:
        temp = Path(directory)
        for field in ("body", "notes"):
            if field + "_file" in fields:
                raw = _read_file(fields.pop(field + "_file"), cwd, stdin)
                try:
                    fields[field] = raw.decode("utf-8")
                except UnicodeError:
                    raise gate.PublishBlocked("OPSEC: publisher text is not UTF-8.") from None
        if verb == "pr-merge":
            from scripts.publish.merge_guard import ensure_merge_ready

            def readiness_runner(args, **kwargs):
                if runner is None:
                    kwargs["fresh"] = True
                result = _send(args, environment=kwargs.pop("env"), runner=runner, cwd=kwargs.pop("cwd"), **kwargs)
                observation = getattr(result, "github_result", None)
                if observation is not None and (observation.stale or observation.error == "github_rate_limited"):
                    raise github_client.GitHubRateLimited(observation.reset_at)
                return result

            fields["match_head"] = ensure_merge_ready(
                gh_repo,
                fields["number"],
                runner=readiness_runner,
                cwd=cwd,
                environment=environment,
                match_head=fields.get("match_head"),
            )
            # GitHub's default squash text carries the PR title and commit messages.
            # Omitted fields are sent explicitly so the scanned text is the sent text;
            # a merge queue ignores explicit text, so its defaults are scanned too.
            default = _squash_text(gh_repo, fields, dest, temp, readiness_runner, cwd, environment)
            for key in ("subject", "body"):
                if key not in fields:
                    fields[key] = default[key]
                elif default["queue"]:
                    scan("default_" + key, default[key])
        schema = SCHEMAS[verb][1]
        for key, value in fields.items():
            if schema[key] == "text":
                scan(key, value)
            elif schema[key] == "texts":
                for index, item in enumerate(value):
                    scan(f"{key}[{index}]", item)
        assets = []
        for index, asset in enumerate(fields.get("assets", fields.get("files", []))):
            public_name, source_path = asset.name, asset.path
            Asset(source_path, public_name)  # Revalidate mutable caller objects before writing a snapshot.
            scan(f"asset[{index}].name", public_name)
            raw = _read_file(source_path, cwd, None)
            try:
                decoded = raw.decode("utf-8")
            except UnicodeError:
                if verb == "gist-create":
                    raise gate.PublishBlocked("OPSEC: gist content must be UTF-8.") from None
            else:
                scan(f"asset[{index}].content", decoded)
            folder = temp / str(index)
            folder.mkdir()
            frozen = folder / public_name
            frozen.write_bytes(raw)
            assets.append(str(frozen))
        try:
            gate.check_texts(dest, texts, environment=environment, field_names=names)
        except gate.PublishBlocked:
            raise
        except Exception:
            raise gate.PublishBlocked("OPSEC: checker unavailable; write refused.") from None
        if verb in {"release-create", "release-edit"} and "notes" not in fields and verb == "release-create":
            fields["notes"] = ""
        if verb == "pr-review" and "body" not in fields:
            fields["body"] = ""
        argv = ["gh", *verb.split("-", 1)]
        if verb != "gist-create":
            argv += ["--repo", gh_repo]
        if "number" in fields:
            # Keep control operands positional; text fields are always =values.
            argv.insert(3, str(fields["number"]))

        def option(key, flag=None):
            if key in fields:
                argv.append((flag or "--" + key.replace("_", "-")) + "=" + str(fields[key]))

        def body_file(key):
            if key in fields:
                frozen = temp / (key + ".txt")
                frozen.write_bytes(fields[key].encode("utf-8"))
                argv.extend(["--" + key + "-file", str(frozen)])

        if verb in {"issue-create", "issue-edit", "pr-create", "pr-edit", "issue-comment", "pr-comment", "pr-review"}:
            option("title")
            body_file("body")
            for key, flag in (
                ("labels", "--label"),
                ("add_labels", "--add-label"),
                ("remove_labels", "--remove-label"),
            ):
                for item in fields.get(key, []):
                    argv.append(flag + "=" + item)
            option("milestone")
            if fields.get("remove_milestone"):
                argv.append("--remove-milestone")
            for key in ("base", "head"):
                option(key)
            if fields.get("draft"):
                argv.append("--draft")
            if verb == "pr-review":
                argv.append("--" + fields["verdict"])
        elif verb == "issue-close":
            option("comment")
            option("reason")
        elif verb == "pr-merge":
            argv.append("--squash")
            option("subject")
            option("match_head", "--match-head-commit")
            body_file("body")
        elif verb in {"pr-update-branch", "pr-ready", "pr-close", "issue-reopen"}:
            pass
        elif verb == "run-rerun":
            argv.append("--failed")
        elif verb == "workflow-run":
            argv.insert(3, fields["workflow"])
            option("ref")
        elif verb == "pr-disarm":
            argv = ["gh", "pr", "merge", str(fields["number"]), "--repo", gh_repo, "--disable-auto"]
        elif verb.startswith("release-"):
            # Tag after -- prevents it being interpreted as a flag.
            for key in ("title", "target"):
                option(key)
            body_file("notes")
            for key in ("draft", "prerelease"):
                if key in fields:
                    argv.append(f"--{key}={str(fields[key]).lower()}")
            if fields.get("clobber"):
                argv.append("--clobber")
            argv += ["--", fields["tag"], *assets]
        elif verb == "gist-create":
            option("description")
            if fields.get("public"):
                argv.append("--public")
            argv += ["--", *assets]
        elif verb in {"label-create", "label-edit"}:
            option("color")
            option("description")
            option("new_name", "--name")
            if fields.get("force"):
                argv.append("--force")
            argv += ["--", fields["name"]]
        else:
            payload = {}
            if verb == "commit-status":
                endpoint = f"repos/{gh_repo}/statuses/{fields['sha']}"
                payload = {key: fields[key] for key in ("state", "context", "description")}
                method = "POST"
            elif verb == "issue-comment-json":
                endpoint = f"repos/{gh_repo}/issues/{fields['number']}/comments"
                payload, method = {"body": fields["body"]}, "POST"
            elif verb.startswith("milestone-"):
                endpoint = f"repos/{gh_repo}/milestones" + (f"/{fields['number']}" if verb.endswith("edit") else "")
                payload = {key: fields[key] for key in ("title", "description", "state") if key in fields}
                method = "PATCH" if verb.endswith("edit") else "POST"
            else:
                endpoint, method = "graphql", "POST"
                if verb == "issue-link" and fields.get("replace_parent"):
                    # Moving an issue between epics needs GitHub's explicit replaceParent.
                    payload = {
                        "query": "mutation($p:ID!,$c:ID!,$r:Boolean!){addSubIssue(input:{issueId:$p,subIssueId:$c,replaceParent:$r}){issue{number}}}",
                        "variables": {"p": fields["parent_id"], "c": fields["child_id"], "r": True},
                    }
                elif verb == "issue-link":
                    payload = {
                        "query": "mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){issue{number}}}",
                        "variables": {"p": fields["parent_id"], "c": fields["child_id"]},
                    }
                elif verb == "issue-unlink":
                    payload = {
                        "query": "mutation($p:ID!,$c:ID!){removeSubIssue(input:{issueId:$p,subIssueId:$c}){issue{number}}}",
                        "variables": {"p": fields["parent_id"], "c": fields["child_id"]},
                    }
                elif verb == "pr-dequeue":
                    payload = {
                        "query": "mutation($id:ID!){dequeuePullRequest(input:{id:$id}){clientMutationId}}",
                        "variables": {"id": fields["node_id"]},
                    }
            frozen = temp / "request.json"
            frozen.write_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            argv = ["gh", "api", "--method", method, endpoint, "--input", str(frozen)]
            if endpoint == "graphql":
                argv += _hostname_flag(dest)
        return _send(
            argv,
            environment=environment,
            runner=runner,
            cwd=cwd,
            capture_output=capture_output,
            text=text,
            check=check,
            timeout=timeout,
            stdout=stdout,
            stderr=stderr,
        )


class PublisherParser(argparse.ArgumentParser):
    """Invalid CLI input never echoes user values or transport paths."""

    def error(self, message):
        self.exit(2, "OPSEC: invalid publisher arguments; use --help.\n")


def main(argv=None, *, runner=None):
    parser = PublisherParser(
        description="Publish GitHub changes through closed, scanned fields.\nUse for public writes; raw gh is reserved for allowlisted reads.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.publish issue-comment --repo unit/public --number 1 --body-file reply.md\n  .venv/bin/python -m scripts.publish read code-scanning-alerts --number 9781\n  .venv/bin/python -m scripts.publish read check-annotations --number 112001533549\nOutputs: GitHub mutation for write verbs; JSON on stdout for reads; temporary snapshots removed on exit.\nExit codes: 0 success; 1 gh failure; 2 schema or publishing refusal.\nRelated: docs/dev/agent-public-text.md; #9297; #9792",
        allow_abbrev=False,
    )
    verbs = parser.add_subparsers(dest="verb", required=True)
    for verb, (_, schema) in SCHEMAS.items():
        sub = verbs.add_parser(verb, help=f"Publish {verb} with scanned fields", allow_abbrev=False)
        for key, kind in schema.items():
            kwargs = {"default": argparse.SUPPRESS, "help": f"{key.replace('_', ' ')} ({kind}); omitted by default"}
            if kind == "bool":
                kwargs["action"] = argparse.BooleanOptionalAction
            elif kind in {"texts", "assets"}:
                kwargs["action"] = "append"
                if kind == "assets":

                    def asset_arg(value):
                        try:
                            return Asset(value)
                        except gate.PublishBlocked:
                            raise argparse.ArgumentTypeError("invalid artifact") from None

                    kwargs["type"] = asset_arg
            elif kind == "number":
                kwargs["type"] = int
            if kind == "workflow_inputs":
                kwargs["type"] = json.loads
            if kind in ENUMS:
                kwargs["choices"] = sorted(ENUMS[kind])
            sub.add_argument("--" + key.replace("_", "-"), **kwargs)
    read_parser = verbs.add_parser(
        "read",
        help="Named REST and GraphQL reads",
        allow_abbrev=False,
        description="Read named GitHub resources. Diagnostic reads return JSON arrays per page; code-scanning-alerts lists open alerts for a PR (--number) or Git ref (--ref).",
    )
    read_parser.add_argument(
        "name",
        choices=sorted(
            set(REST_READS) | set(GQL_READS) | REST_COMPAT_READS | {"queue-snapshot", "subissue-batch", "issue-states", "merge-facts"}
        ),
    )
    read_parser.add_argument(
        "--repo",
        help=(
            "Repository owner/name (e.g. unit/public); defaults to GH_REPO or Git origin. "
            "For code-scanning-alerts and check-annotations, admission allows only the checkout's origin repository."
        ),
    )
    for key in ("number",):
        read_parser.add_argument(
            "--" + key,
            type=int,
            default=argparse.SUPPRESS,
            help="Positive issue, PR, run or check-run ID; omitted by default",
        )
    for key in ("sha", "start", "end", "branch", "cursor", "ref"):
        read_parser.add_argument(
            "--" + key,
            default=argparse.SUPPRESS,
            help=(
                "Git ref for code-scanning-alerts (e.g. refs/heads/main); use either --ref or --number"
                if key == "ref"
                else f"{key} selector; omitted by default"
            ),
        )
    for key in ("branches", "cursors", "body_roots", "numbers", "batch"):
        read_parser.add_argument(
            "--" + key.replace("_", "-"),
            type=json.loads,
            default=argparse.SUPPRESS,
            help=f"{key} as JSON; omitted by default",
        )
    read_parser.add_argument(
        "--paginate", action="store_true", help="Read all pages (default off; diagnostic reads always paginate)"
    )
    read_parser.add_argument(
        "--slurp",
        action="store_true",
        help="Wrap paginated pages in an array (default off; unsupported for shaped diagnostic reads)",
    )
    args = vars(parser.parse_args(argv))
    verb = args.pop("verb")
    try:
        if verb == "read":
            return read(args.pop("name"), runner=runner, **args).returncode
        return publish(verb, runner=runner, **args).returncode
    except gate.PublishBlocked as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        print("OPSEC: publisher transport unavailable.", file=sys.stderr)
        return 2


class Request:
    """A named closed operation for existing adapters with injected transports."""

    def __init__(self, verb, **fields):
        self.verb, self.fields = verb, fields


def request_run(request, *, runner=None, input=None, **kwargs):
    """Adapt typed requests; raw argv is admitted only by the raw read guard."""
    if not isinstance(request, Request):
        return gate.checked_run(request, runner=runner, input=input, **kwargs)
    if input is not None:
        raise gate.PublishBlocked("OPSEC: typed requests cannot take arbitrary transport input.")
    if request.verb.startswith("read-"):
        return read(request.verb[5:], runner=runner, **kwargs, **request.fields)
    return publish(request.verb, runner=runner, **kwargs, **request.fields)


REST_READS = {
    "identity": ("user", {}),
    "issue": ("repos/{repo}/issues/{number}", {"number": "number"}),
    "comments": ("repos/{repo}/issues/{number}/comments", {"number": "number"}),
    "labels": ("repos/{repo}/issues/{number}/labels", {"number": "number"}),
    "timeline": ("repos/{repo}/issues/{number}/timeline", {"number": "number"}),
    "reviews": ("repos/{repo}/pulls/{number}/reviews", {"number": "number"}),
    "commits": ("repos/{repo}/pulls/{number}/commits", {"number": "number"}),
    "comment": ("repos/{repo}/issues/comments/{number}", {"number": "number"}),
    "checks": ("repos/{repo}/commits/{sha}/check-runs", {"sha": "sha"}),
    "code-scanning-alerts": ("repos/{repo}/code-scanning/alerts?state=open&ref={ref}", {"ref": "ref"}),
    "check-annotations": ("repos/{repo}/check-runs/{number}/annotations", {"number": "number"}),
    "jobs": ("repos/{repo}/actions/runs/{number}/jobs", {"number": "number"}),
    "issues": ("repos/{repo}/issues?state=open&labels=infra", {}),
    "runs": ("repos/{repo}/actions/runs?event=merge_group&created={start}..{end}", {"start": "date", "end": "date"}),
    "deployments": ("repos/{repo}/deployments?sha={sha}", {"sha": "sha"}),
    "deployment-statuses": ("repos/{repo}/deployments/{number}/statuses", {"number": "number"}),
}
# Fixed projections omit account/host metadata and refuse non-relative file paths.
# gh applies --jq to each page; diagnostic reads emit one JSON array per page.
_RELATIVE_PATH_JQ = r"""def relative_path:
    if type == "string" and length > 0
       and (test("(^/|[\\\\:\\x00-\\x1f\\x7f]|(^|/)\\.\\.?(/|$)|//)") | not)
    then . else error("OPSEC: diagnostic file path is not repository-relative") end;
"""
DIAGNOSTIC_READS = {
    "code-scanning-alerts": _RELATIVE_PATH_JQ
    + """
        map({rule_id: .rule.id,
            severity: (.rule.security_severity_level // .rule.severity),
            state: (.most_recent_instance.state // .state),
            file: (.most_recent_instance.location.path | relative_path),
            start_line: .most_recent_instance.location.start_line,
            message: .most_recent_instance.message.text,
            html_path: (.html_url |
                if test("^https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(security/)?code-scanning/[0-9]+$")
                then split("/")[5:] | join("/") | relative_path
                else error("OPSEC: invalid diagnostic html path") end)})""",
    "check-annotations": _RELATIVE_PATH_JQ
    + """
        map({path: (.path | relative_path), line: .start_line,
            level: .annotation_level, message: .message})""",
}
REST_COMPAT_READS = {'budget', 'issue-scope', 'subissues', 'subissues-next', 'default-head', 'pr-bases', 'issue-parent'}
GQL_READS = {
    "queue-status": "\nquery($owner: String!, $name: String!, $number: Int!, $branch: String!) {\n  repository(owner: $owner, name: $name) {\n    pullRequest(number: $number) {\n      number\n      title\n      state\n      merged\n      mergeable\n      mergeStateStatus\n      isInMergeQueue\n      isMergeQueueEnabled\n      headRefName\n      headRefOid\n      baseRefName\n      mergeQueueEntry {\n        id\n        position\n        state\n        enqueuedAt\n        estimatedTimeToMerge\n        jump\n        solo\n        headCommit {\n          oid\n          checkSuites(first: 20) {\n            nodes {\n              status\n              conclusion\n              createdAt\n              updatedAt\n              workflowRun {\n                id\n                url\n                event\n                createdAt\n                updatedAt\n                workflow {\n                  name\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n    mergeQueue(branch: $branch) {\n      url\n      nextEntryEstimatedTimeToMerge\n      entries(first: 50) {\n        totalCount\n        nodes {\n          position\n          state\n          enqueuedAt\n          estimatedTimeToMerge\n          pullRequest {\n            number\n          }\n        }\n      }\n    }\n  }\n}\n",
    "membership-head": "query($owner:String!,$name:String!,$number:Int!,$branch:String!){repository(owner:$owner,name:$name){pullRequest(number:$number){headRefOid isInMergeQueue} mergeQueue(branch:$branch){url}}}",
    "membership": "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){isInMergeQueue}}}",
    "squash-text": "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){headRefOid viewerMergeHeadlineText(mergeType:SQUASH) viewerMergeBodyText(mergeType:SQUASH) mergeQueueEntry{headCommit{oid message}}}}}",
}


def read(
    operation,
    *,
    repo=None,
    runner=None,
    cwd=None,
    env=None,
    paginate=False,
    slurp=False,
    capture_output=False,
    text=False,
    check=False,
    timeout=None,
    stdout=None,
    stderr=None,
    **fields,
):
    """Specific API reads with fixed GET endpoints or internally built query documents."""
    environment = _validated_environment(env)
    cwd = Path(cwd or Path.cwd())
    dest = "unknown" if operation == "budget" else repository(cwd, environment, repo)
    if dest == "unknown" and operation not in {"identity", "budget", "merge-facts"}:
        raise gate.PublishBlocked("OPSEC: read repository unresolved.")
    if dest != "unknown":
        environment["GH_HOST"] = dest.split("/", 1)[0]
    gh_repo = dest.split("/", 1)[-1]
    for key in ("number",):
        if key in fields and (type(fields[key]) is not int or fields[key] <= 0):
            raise gate.PublishBlocked("OPSEC: invalid read identifier.")
    if operation in {"budget", "default-head", "pr-bases", "issue-states", "merge-facts", "issue-parent", "issue-scope", "subissues", "subissues-next", "subissue-batch"}:
        expected = {"budget":set(), "default-head":set(), "pr-bases":{"cursor"}, "issue-states":{"numbers"}, "merge-facts":{"batch"}, "issue-parent":{"number"}, "issue-scope":{"number"}, "subissues":{"number"}, "subissues-next":{"number","cursor"}, "subissue-batch":{"cursors","body_roots"}}[operation]
        if set(fields) != expected:
            raise gate.PublishBlocked("OPSEC: invalid read fields.")
        if operation == "issue-states" and (not isinstance(fields["numbers"], (list, tuple)) or not 1 <= len(fields["numbers"]) <= 100 or any(type(n) is not int or n <= 0 for n in fields["numbers"])):
            raise gate.PublishBlocked("OPSEC: invalid issue batch.")
        if operation == "merge-facts" and (not isinstance(fields["batch"], (list, tuple)) or not 1 <= len(fields["batch"]) <= 50 or any(not isinstance(item, (list, tuple)) or len(item) != 2 or not isinstance(item[0], str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", item[0]) or type(item[1]) is not int or item[1] <= 0 for item in fields["batch"])):
            raise gate.PublishBlocked("OPSEC: invalid merge batch.")
        if operation == "subissues-next" and not isinstance(fields["cursor"], str):
            raise gate.PublishBlocked("OPSEC: invalid read cursor.")
        if operation == "subissue-batch":
            cursors, roots = fields["cursors"], fields["body_roots"]
            if not isinstance(cursors, dict) or not 1 <= len(cursors) <= 20 or not isinstance(roots, (set,list,tuple)) or any(type(n) is not int or n <= 0 or (c is not None and not isinstance(c,str)) for n,c in cursors.items()):
                raise gate.PublishBlocked("OPSEC: invalid read batch.")
        return github_client.rest_read(operation, gh_repo, fields, runner=runner, env=environment, cwd=cwd, capture_output=capture_output, text=text, check=check, timeout=timeout, stdout=stdout, stderr=stderr)
    if operation in {"queue-snapshot", "queue-status"} and runner is None:
        expected = {"branches"} if operation == "queue-snapshot" else {"number", "branch"}
        if set(fields) != expected or (operation == "queue-snapshot" and (not isinstance(fields["branches"], (list, set, tuple)) or not all(isinstance(b, str) for b in fields["branches"]))):
            raise gate.PublishBlocked("OPSEC: invalid queue fields.")
        return github_client.queue_read(operation, gh_repo, fields, env=environment, cwd=cwd, capture_output=capture_output, text=text, check=check, timeout=timeout, stdout=stdout, stderr=stderr)
    if operation in REST_READS:
        endpoint, schema = REST_READS[operation]
        if operation == "code-scanning-alerts" and set(fields) == {"number"}:
            # PR filtering covers analyses uploaded to either head or merge refs.
            endpoint = "repos/{repo}/code-scanning/alerts?state=open&pr={number}"
            schema = {"number": "number"}
        if set(fields) != set(schema):
            raise gate.PublishBlocked("OPSEC: invalid read fields.")
        for key, kind in schema.items():
            pattern = r"\d{4}-\d{2}-\d{2}" if kind == "date" else PATTERNS.get(kind)
            if pattern and (not isinstance(fields[key], str) or not re.fullmatch(pattern, fields[key])):
                raise gate.PublishBlocked("OPSEC: invalid read selector.")
        if operation == "code-scanning-alerts" and "ref" in fields:
            if any(segment in {"", ".", ".."} for segment in fields["ref"].split("/")):
                raise gate.PublishBlocked("OPSEC: invalid read selector.")
            fields = {"ref": quote(fields["ref"], safe="")}
        endpoint = endpoint.format(repo=gh_repo, **fields)
        endpoint += ("&" if "?" in endpoint else "?") + "per_page=100"
        argv = ["gh", "api", "--method", "GET", endpoint]
        if operation in DIAGNOSTIC_READS:
            if slurp:
                raise gate.PublishBlocked("OPSEC: diagnostic reads return JSON arrays per page; slurp is unsupported.")
            argv += ["--paginate", "--jq", DIAGNOSTIC_READS[operation]]
        elif paginate:
            argv.append("--paginate")
        if slurp and operation not in DIAGNOSTIC_READS:
            if not paginate:
                raise gate.PublishBlocked("OPSEC: slurp requires pagination.")
            argv.append("--slurp")
    else:
        variables = dict(zip(("owner", "name"), gh_repo.split("/", 1), strict=True)) if "/" in gh_repo else {}
        if operation in GQL_READS:
            expected = (
                set()
                if operation in {"budget", "default-head"}
                else {"cursor"}
                if operation == "pr-bases"
                else {"number", "branch"}
                if operation == "queue-status"
                else {"number", "cursor"}
                if operation == "subissues-next"
                else {"number", "branch"}
                if operation == "membership-head"
                else {"number"}
            )
            if (
                set(fields) != expected
                or (
                    "cursor" in fields
                    and not isinstance(fields["cursor"], str)
                    and not (operation == "pr-bases" and fields["cursor"] is None)
                )
                or ("branch" in fields and not isinstance(fields["branch"], str))
            ):
                raise gate.PublishBlocked("OPSEC: invalid query fields.")
            query = GQL_READS[operation]
            variables.update(fields)
        elif operation == "queue-snapshot" and set(fields) == {"branches"}:
            branches = fields["branches"]
            if not isinstance(branches, (list, tuple, set)) or not all(isinstance(b, str) for b in branches):
                raise gate.PublishBlocked("OPSEC: invalid query branches.")
            aliases = "\n".join(
                f"q{i}: mergeQueue(branch: {json.dumps(branch)}) {{ url }}" for i, branch in enumerate(sorted(branches))
            )
            query = (
                "query($owner:String!,$name:String!){ rateLimit { remaining cost } repository(owner:$owner,name:$name){ pullRequests(first:100,states:OPEN){ totalCount pageInfo{hasNextPage} nodes{ id number title isDraft headRefOid baseRefName isInMergeQueue mergeStateStatus autoMergeRequest{ enabledAt } labels(first:100){totalCount pageInfo{hasNextPage} nodes{name}} } } "
                + aliases
                + "\n}}"
            )
        else:
            raise gate.PublishBlocked("OPSEC: unknown typed read.")
        # Only our query documents reach the API. Variable values are JSON data.
        with tempfile.TemporaryDirectory(prefix="lu-read-") as directory:
            frozen = Path(directory) / "query.json"
            frozen.write_bytes(json.dumps({"query": query, "variables": variables}).encode("utf-8"))
            argv = ["gh", "api", "--method", "POST", "graphql", "--input", str(frozen)]
            argv += _hostname_flag(dest)
            return _send(
                argv,
                environment=environment,
                runner=runner,
                cwd=cwd,
                capture_output=capture_output,
                text=text,
                check=check,
                timeout=timeout,
                stdout=stdout,
                stderr=stderr,
            )
    argv += _hostname_flag(dest)
    return _send(
        argv,
        environment=environment,
        runner=runner,
        cwd=cwd,
        capture_output=capture_output,
        text=text,
        check=check,
        timeout=timeout,
        stdout=stdout,
        stderr=stderr,
    )
