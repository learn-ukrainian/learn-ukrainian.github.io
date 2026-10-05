"""Exact raw-gh read admission regressions for #9358; synthetic inputs only."""

import pytest

from scripts.opsec.gh_snapshot import admit
from scripts.opsec.prepublish import PublishBlocked


def read_api(*args):
    return admit(["api", *args], cwd=".", environment={})


@pytest.mark.parametrize("flag", ["-H", "--header"])
@pytest.mark.parametrize(
    "header",
    [
        "Authorization: fixture",
        "X-HTTP-Method-Override: POST",
        "Accept",
        ": fixture",
        " Accept: application/json",
        "Accept : application/json",
        "Accept: application/json\rX-Extra: fixture",
        "Accept: application/json\nX-Extra: fixture",
        "Accept: application/json\x00",
        "Accept: application/json\x1b[31m",
        "Accept: application/json\x7f",
    ],
)
def test_unapproved_or_malformed_headers_are_refused(flag, header):
    with pytest.raises(PublishBlocked):
        read_api("repos/unit/public/issues/1", flag, header)


@pytest.mark.parametrize("flag", ["-H", "--header", "--header="])
@pytest.mark.parametrize(
    "header", ["aCcEpT: application/json", 'If-None-Match: "fixture"', "X-GitHub-Api-Version: 2022-11-28"]
)
def test_allowed_header_names_are_case_insensitive(flag, header):
    args = [flag + header] if flag.endswith("=") else [flag, header]
    assert not read_api("repos/unit/public/issues/1", *args).write


@pytest.mark.parametrize("flag", ["--hostname", "--hostname="])
def test_api_hostname_is_refused(flag):
    args = [flag + "example.invalid"] if flag.endswith("=") else [flag, "example.invalid"]
    with pytest.raises(PublishBlocked):
        read_api("repos/unit/public/issues/1", *args)


@pytest.mark.parametrize("segment", ["unit%2Fextra", "unit%2fextra", "%2e", "%2E%2e", ".", "..", "..."])
@pytest.mark.parametrize("position", ["owner", "repo"])
def test_encoded_separators_and_dot_only_repository_segments_are_refused(segment, position):
    owner, repo = (segment, "public") if position == "owner" else ("unit", segment)
    with pytest.raises(PublishBlocked):
        read_api(f"repos/{owner}/{repo}/issues/1")


@pytest.mark.parametrize(
    "path", ["repos/unit/public/branches/feature%2Fextra", "repos/unit/public/commits/ref%2eextra"]
)
def test_encoded_dot_or_slash_in_suffix_is_refused(path):
    with pytest.raises(PublishBlocked):
        read_api(path)


@pytest.mark.parametrize(
    "path",
    [
        "repos/{owner}/{repo}/issues/1",
        "repos/unit.name/public.repo/compare/base...head",
        "repos/unit/public/branches/feature%20name",
        "repos/unit/public/pulls?head=unit%3Afeature%2Fextra",
    ],
)
def test_valid_segments_and_query_encoding_remain_allowed(path):
    assert not read_api(path).write


@pytest.mark.parametrize(
    "cmd",
    [
        ["api", "repos/unit/public/issues/1"],
        ["issue", "list"],
        ["pr", "view", "1"],
        ["pr", "checks", "1"],
        ["repo", "view"],
    ],
)
def test_gh_host_is_refused_for_reads(cmd):
    with pytest.raises(PublishBlocked, match="GH_HOST refused for reads"):
        admit(cmd, cwd=".", environment={"GH_HOST": "ghe.example.com"})


@pytest.mark.parametrize(
    "cmd",
    [
        ["issue", "list", "--repo", "ghe.example.com/unit/public"],
        ["issue", "list", "-R", "ghe.example.com/unit/public"],
        ["pr", "view", "1", "--repo", "https://gitlab.com/unit/public"],
        ["pr", "checks", "1", "-R", "other.invalid/unit/public"],
        ["repo", "view", "ghe.example.com/unit/public"],
        ["repo", "list", "ghe.example.com/unit"],
    ],
)
def test_non_github_repo_host_is_refused_for_reads(cmd):
    with pytest.raises(PublishBlocked, match=r"non-github\.com repository host refused"):
        admit(cmd, cwd=".", environment={})


@pytest.mark.parametrize(
    "cmd",
    [
        ["issue", "list", "--repo", "github.com/unit/public"],
        ["issue", "list", "--repo", "unit/public"],
        ["pr", "view", "1", "-R", "github.com/unit/public"],
        ["pr", "view", "1", "-R", "unit/public"],
        ["repo", "view", "github.com/unit/public"],
        ["repo", "view", "unit/public"],
    ],
)
def test_github_repo_host_remains_allowed_for_reads(cmd):
    cmd_admitted = admit(cmd, cwd=".", environment={})
    assert not cmd_admitted.write


@pytest.mark.parametrize(
    "path",
    [
        "repos/unit/public/releases/tags/..",
        "repos/unit/public/releases/tags/.",
        "repos/unit/public/branches/..",
        "repos/unit/public/branches/.",
        "repos/unit/public/commits/..",
        "repos/unit/public/actions/workflows/..",
        "repos/unit/public/compare/..",
    ],
)
def test_dot_only_segments_in_read_api_paths_are_refused(path):
    with pytest.raises(PublishBlocked):
        read_api(path)


@pytest.mark.parametrize(
    "cmd",
    [
        ["release", "view", ".."],
        ["release", "download", ".."],
        ["issue", "list", "--repo", "unit/.."],
        ["issue", "list", "--repo", "../public"],
        ["issue", "list", "--repo", ".."],
        ["pr", "view", ".."],
        ["pr", "diff", ".."],
        ["pr", "checks", ".."],
        ["workflow", "view", ".."],
    ],
)
def test_dot_only_segments_in_read_commands_are_refused(cmd):
    with pytest.raises(PublishBlocked, match="dot-only segments refused"):
        admit(cmd, cwd=".", environment={})


@pytest.mark.parametrize(
    "cmd",
    [
        ["issue", "list"],
        ["pr", "view", "1"],
    ],
)
def test_gh_repo_in_environment_refuses_non_github_host(cmd):
    with pytest.raises(PublishBlocked, match=r"non-github\.com repository host refused"):
        admit(cmd, cwd=".", environment={"GH_REPO": "ghe.example.com/unit/public"})


def test_gh_host_github_com_remains_allowed_for_reads():
    cmd = admit(["issue", "list"], cwd=".", environment={"GH_HOST": "github.com"})
    assert not cmd.write


@pytest.mark.parametrize(
    "cmd",
    [
        ["pr", "view", "https://ghe.example.com/unit/public/pull/1"],
        ["pr", "diff", "https://ghe.example.com/unit/public/pull/1"],
        ["pr", "checks", "https://ghe.example.com/unit/public/pull/1"],
        ["issue", "view", "https://ghe.example.com/unit/public/issues/1"],
    ],
)
def test_url_positional_arguments_refuse_non_github_hosts(cmd):
    with pytest.raises(PublishBlocked, match=r"non-github\.com repository host refused"):
        admit(cmd, cwd=".", environment={})


@pytest.mark.parametrize(
    "cmd",
    [
        ["pr", "view", "https://github.com/unit/public/pull/1"],
        ["issue", "view", "https://github.com/unit/public/issues/1"],
    ],
)
def test_url_positional_arguments_allow_github_com(cmd):
    cmd_admitted = admit(cmd, cwd=".", environment={})
    assert not cmd_admitted.write


@pytest.mark.parametrize(
    "cmd",
    [
        ["run", "view", "--job", ".."],
        ["run", "view", "--job", "../../../../user"],
        ["run", "view", "-j", ".."],
    ],
)
def test_dot_only_segments_in_job_flag_are_refused(cmd):
    with pytest.raises(PublishBlocked, match="dot-only segments refused"):
        admit(cmd, cwd=".", environment={})


DIAGNOSTIC_PATHS = [
    "code-scanning/alerts",
    "code-scanning/alerts?pr=1&ref=refs%2Fpull%2F1%2Fmerge",
    "code-scanning/alerts/1",
    "code-scanning/alerts/1/instances",
    "code-scanning/alerts/1/instances?ref=refs%2Fpull%2F1%2Fmerge",
    "check-runs/123/annotations",
    "check-runs/123/annotations?per_page=100&page=2",
]


def origin_reader(*args, **kwargs):
    from subprocess import CompletedProcess

    return CompletedProcess(args, 0, "https://github.com/unit/public.git\n", "")


@pytest.mark.parametrize("suffix", DIAGNOSTIC_PATHS)
@pytest.mark.parametrize("prefix", ["repos/unit/public/", "https://api.github.com/repos/unit/public/"])
@pytest.mark.parametrize("method", [[], ["--method", "GET"], ["-X", "GET"]])
def test_diagnostic_get_paths_are_admitted(suffix, prefix, method):
    result = admit(["api", prefix + suffix, *method], cwd=".", environment={}, reader=origin_reader)
    assert not result.write


@pytest.mark.parametrize("suffix", DIAGNOSTIC_PATHS)
@pytest.mark.parametrize("method", ["POST", "PATCH", "DELETE", "PUT", "HEAD", "OPTIONS"])
@pytest.mark.parametrize("flag", ["--method", "-X"])
def test_diagnostic_non_get_methods_are_refused(suffix, method, flag):
    with pytest.raises(PublishBlocked):
        admit(["api", "repos/unit/public/" + suffix, flag, method], cwd=".", environment={}, reader=origin_reader)


@pytest.mark.parametrize(
    "suffix",
    [
        "code-scanning",
        "code-scanning/alerts/",
        "code-scanning/alerts/1/../x",
        "code-scanning/alerts/1/instances/extra",
        "code-scanning/alerts/1/extra",
        "code-scanning/alerts/abc",
        "code-scanning/alerts/../instances",
        "code-scanning/alerts/%31",
        "code-scanning/alerts/1/%2e%2e/x",
        "check-runs/123",
        "check-runs/123/annotations/extra",
        "check-runs/../annotations",
        "check-runs/abc/annotations",
        "check-runs/123/rerequest",
    ],
)
def test_out_of_pattern_diagnostic_paths_are_refused(suffix):
    with pytest.raises(PublishBlocked):
        admit(["api", "repos/unit/public/" + suffix], cwd=".", environment={}, reader=origin_reader)


@pytest.mark.parametrize("suffix", DIAGNOSTIC_PATHS)
@pytest.mark.parametrize(
    "prefix", ["repos/other/public/", "repos/unit/other/", "https://other.invalid/repos/unit/public/"]
)
def test_diagnostic_other_repository_or_host_is_refused(suffix, prefix):
    with pytest.raises(PublishBlocked):
        admit(["api", prefix + suffix], cwd=".", environment={}, reader=origin_reader)


@pytest.mark.parametrize("suffix", DIAGNOSTIC_PATHS)
def test_diagnostic_gh_repo_cannot_override_origin(suffix):
    with pytest.raises(PublishBlocked):
        admit(
            ["api", "repos/other/public/" + suffix],
            cwd=".",
            environment={"GH_REPO": "other/public"},
            reader=origin_reader,
        )


def test_diagnostic_unknown_origin_fails_closed():
    with pytest.raises(PublishBlocked, match="repository refused"):
        admit(["api", "repos/unit/public/code-scanning/alerts"], cwd=".", environment={}, reader=lambda *a, **k: None)
