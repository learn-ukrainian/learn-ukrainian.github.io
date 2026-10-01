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
