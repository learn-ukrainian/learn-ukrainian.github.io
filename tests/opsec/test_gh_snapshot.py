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
