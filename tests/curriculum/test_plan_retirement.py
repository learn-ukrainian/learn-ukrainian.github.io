"""Exact-byte retirement refuses old plans without exempting replacements (#10108)."""

import hashlib
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.validate import codes, cross, validate
from scripts.curriculum.validate.loader import (
    PlanError,
    active_plan_paths,
    load_plan,
    retired_plan_paths,
    retirement_record,
)


@pytest.fixture
def retired(tmp_path):
    directory = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1"
    directory.mkdir(parents=True)
    path = directory / "old.yaml"
    path.write_text("plan_schema: 2\nslug: old\narc_ref: {position: 1}\nlessons: []\n")
    record = {
        "retirement_schema": 1,
        "plans": [{"slug": "old", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "old_position": 1}],
        "routes": [{"slug": "old", "old_position": 1}],
    }
    (directory / "_retired.yaml").write_text(yaml.safe_dump(record))
    return path, record


def test_retired_refusal_precedes_yaml_and_schema(retired):
    path, record = retired
    raw = b"invalid: [\n"
    path.write_bytes(raw)
    record["plans"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
    (path.parent / "_retired.yaml").write_text(yaml.safe_dump(record))
    for text in (None, raw.decode()):
        with pytest.raises(PlanError) as error:
            load_plan(path, text=text)
        assert error.value.code == codes.PLAN_RETIRED
    assert active_plan_paths(path.parent) == []
    assert retired_plan_paths(path.parent) == [path]


def test_replacement_bytes_use_ordinary_gates(retired):
    path, _ = retired
    path.write_bytes(path.read_bytes() + b"\n")
    assert active_plan_paths(path.parent) == [path]
    assert retired_plan_paths(path.parent) == []
    assert load_plan(path)["slug"] == "old"
    report = validate.validate_plan("a1", "old", plan_path=path)
    assert report.failures
    assert codes.PLAN_RETIRED not in {failure.code for failure in report.failures}
    path.write_text("plan_schema: 1\n")
    with pytest.raises(PlanError) as error:
        load_plan(path)
    assert error.value.code == codes.V1_PLAN


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(extra=1),
        lambda r: r.update(retirement_schema=True),
        lambda r: r.update(plans={}),
        lambda r: r["plans"][0].update(extra=1),
        lambda r: r["plans"][0].update(sha256="0"),
        lambda r: r["plans"][0].update(old_position=True),
        lambda r: r["plans"][0].update(old_position=0),
        lambda r: r["plans"][0].update(slug="../old"),
        lambda r: r["plans"].append(r["plans"][0].copy()),
        lambda r: r["routes"].append(r["routes"][0].copy()),
        lambda r: r["routes"][0].update(sha256="a" * 64),
    ],
)
def test_malformed_record_fails_closed(retired, mutate):
    path, record = retired
    mutate(record)
    (path.parent / "_retired.yaml").write_text(yaml.safe_dump(record))
    for operation in (lambda: load_plan(path), lambda: active_plan_paths(path.parent)):
        with pytest.raises(PlanError) as error:
            operation()
        assert error.value.code == codes.RETIREMENT_RECORD_INVALID
    assert cross.load_level_plans(path.parent).failures[0].code == codes.RETIREMENT_RECORD_INVALID


@pytest.mark.parametrize(
    "raw",
    ["plans: [", "[]", "plans: []\nplans: []\n", "retirement_schema: 1\nplans: [{slug: old, slug: new}]\nroutes: []\n"],
)
def test_invalid_yaml_and_duplicate_keys(retired, raw):
    path, _ = retired
    (path.parent / "_retired.yaml").write_text(raw)
    with pytest.raises(PlanError, match="retirement_record_invalid"):
        retirement_record(path.parent)


def test_underscore_inventory_is_never_a_plan(retired):
    path, _ = retired
    with pytest.raises(PlanError, match="not_a_plan"):
        load_plan(path.parent / "_retired.yaml")


def test_discovery_without_record_and_cross_checks_remain_strict(tmp_path):
    (tmp_path / "ordinary.yaml").write_text("slug: ordinary\narc_ref: {position: 1}\n")
    (tmp_path / "_scope.yaml").write_text("ignored: true")
    assert retirement_record(tmp_path)["plans"] == []
    assert [path.stem for path in active_plan_paths(tmp_path)] == ["ordinary"]
    assert cross.load_level_plans(tmp_path).by_position[1][0] == "ordinary"


def test_all_names_exclusions_and_zero_active_is_no_proof(retired, capsys):
    path, _ = retired
    assert cross.load_level_plans(path.parent).by_position == {}
    assert validate.main(["a1", "--all", "--strict", "--level-dir", str(path.parent)]) == 0
    output = capsys.readouterr().out
    assert "retired exclusions: old" in output
    assert "zero active plans" in output and "no plan-state proof" in output
    (path.parent / "_retired.yaml").write_text("bad: true")
    assert validate.main(["a1", "--all", "--level-dir", str(path.parent)]) == 1


def test_real_three_exact_plan_hashes_are_retired():
    directory = Path(__file__).resolve().parents[2] / "curriculum/l2-uk-en/lesson-plans/a1"
    record = retirement_record(directory)
    assert [(entry["slug"], entry["old_position"]) for entry in record["plans"]] == [
        ("sounds-letters-and-hello", 1),
        ("reading-ukrainian", 2),
        ("special-signs", 3),
    ]
    assert active_plan_paths(directory) == []
    for entry in record["plans"]:
        path = directory / f"{entry['slug']}.yaml"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        with pytest.raises(PlanError, match="plan_retired"):
            load_plan(path)


def produced_retirement_codes(root):
    """Exercise both registered first-gate failures for the registry's exact audit."""
    directory = root / "curriculum/l2-uk-en/lesson-plans/a1"
    directory.mkdir(parents=True)
    path = directory / "old.yaml"
    path.write_text("invalid: [\n")
    record = {
        "retirement_schema": 1,
        "plans": [{"slug": "old", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "old_position": 1}],
        "routes": [],
    }
    (directory / "_retired.yaml").write_text(yaml.safe_dump(record))
    codes_seen = validate.validate_plan("a1", "old", plan_path=path).codes()
    (directory / "_retired.yaml").write_text("invalid: true")
    codes_seen |= validate.validate_plan("a1", "old", plan_path=path).codes()
    assert {codes.PLAN_RETIRED, codes.RETIREMENT_RECORD_INVALID} <= codes_seen
    return codes_seen


PROTECTED_INPUT_SHA256 = {
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/lessons.lock.yaml": "f54156c716bf0657759ac40305e4843a951c63a98bc7fb22ef8f0e5301d2c1b0",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/lessons.lock.yaml.lock": "9c029bd58ed9064e3638d9adc0c22ee4eae81cf9b5dd360ebe646d2b0ea419e1",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/04c9d62ce9d531ad500655c298430dde61621a6aa6312ecf787055ec46822fe0.yaml": "04c9d62ce9d531ad500655c298430dde61621a6aa6312ecf787055ec46822fe0",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/217c19ca26cde45cf340e624d8b422df5b92d029d29ffbc706e6f5f9a2da94d9.yaml": "217c19ca26cde45cf340e624d8b422df5b92d029d29ffbc706e6f5f9a2da94d9",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/2d7833af151c3d6260f3de91f2e0bee8f2e0776f400f8cd92753d5bbbde28631.yaml": "2d7833af151c3d6260f3de91f2e0bee8f2e0776f400f8cd92753d5bbbde28631",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/360b2f2eb4728efb7df6b287cd3028065685031a138860800af6e62fd745bd4c.yaml": "360b2f2eb4728efb7df6b287cd3028065685031a138860800af6e62fd745bd4c",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/5094aeb488b1819ae3822d7db7c0c25b27315d2dc58be9fa6b88f9d8858d1335.yaml": "5094aeb488b1819ae3822d7db7c0c25b27315d2dc58be9fa6b88f9d8858d1335",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/564c179361e8742ddc6f16bc8c25570d740bcdddee41cac49365bab692ed1a90.yaml": "564c179361e8742ddc6f16bc8c25570d740bcdddee41cac49365bab692ed1a90",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/7d230f70e025fe602a66e803ac0420e946d4c7649642aa54d0209afcdcc164b8.yaml": "7d230f70e025fe602a66e803ac0420e946d4c7649642aa54d0209afcdcc164b8",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/ad4d7af6852c5cfd453eb663d37c078a5ece41fa8f78d5b5413e246c63a38055.yaml": "ad4d7af6852c5cfd453eb663d37c078a5ece41fa8f78d5b5413e246c63a38055",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/b09666f9ed5a004eea01fa4e0a4afcc06184165fc915644cfb919ca14e20bd0a.yaml": "b09666f9ed5a004eea01fa4e0a4afcc06184165fc915644cfb919ca14e20bd0a",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/b99c63c4c8e89bb7ceb64fcac9796e0fb7cc7732a679ee98ec03f30c9b8f8a79.yaml": "b99c63c4c8e89bb7ceb64fcac9796e0fb7cc7732a679ee98ec03f30c9b8f8a79",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/c298055284d815ba561a42cb9ba9f076ac2efe34f5d2a88fe385572ace1ac1ba.yaml": "c298055284d815ba561a42cb9ba9f076ac2efe34f5d2a88fe385572ace1ac1ba",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/manifests/plan/ea42b1a02a08eb379ad1528e7cc67f5e403cd884ace6f6f8d39255a39a3fccff.yaml": "ea42b1a02a08eb379ad1528e7cc67f5e403cd884ace6f6f8d39255a39a3fccff",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/pack-verify.report.json": "69188f7ffe16b226194d9533ded64f1f94ddddd2bf30672d13e6e5694c7d2dc6",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-promotion.yaml": "b8164da7b539b09e366d1cd83fa5ba5291db775771330a497eff7d45181e86be",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.agy-att-7.yaml": "76d44a5ec11b53e58aff2edb23aef5cca59e7ca6d3125367ef0d05d6bb6c429e",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.claude-full-att-1.yaml": "11a0e10a8b159c96c12a94d16260c4ee05406399070aa17825c08587bdaea154",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.claude-full-att-2.yaml": "f793b0d64f6326d8d708e33d17a96b0c89385f2348240dacd09631dcf5054ff5",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.claude-full-att-3.yaml": "8d01f6f66679b5822f38534d6eabe3486831ffc9d519ee84f39e3b2828c97123",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.claude-full-att-4.yaml": "47c018f26bf538ed88ea43e997a555288c92cafbce7c265c1d6f07bbe2921027",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.claude-full-att-5.yaml": "b4312d31ac5f29481bcc904551ee69cade1b92429f3c7ac2b0b4949a43e39f19",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.claude-full-att-6.yaml": "197b0714a69b38100658a79f92245a126db088467c946ca7842a86a2aa4e49cb",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.learner-state.yaml": "6bfcaf585064f0bb081b933489fc892c3659b0925164733290655a507c4403b4",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.learner-state.yaml.lock": "15f4cb56bd6fa0e9986c2e5851fed46c98635c17f7eef98ba13adb521bde2e6d",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.manifest.sha256": "43e17dae2e3add4020eb8f8a358009075299ef0c163e0bfcce852d8f202687fa",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.manifest.yaml": "ad4d7af6852c5cfd453eb663d37c078a5ece41fa8f78d5b5413e246c63a38055",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.v1-totals.yaml": "1d302580ee29f3c02ce1457740d1edd0e1f8514790658a7eadb12aac77e9ec2f",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.v1-totals.yaml.lock": "4ae44fee0ab738688f22f9dc29afd34d8adeef5123449f4605d1b71532ca3d3d",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-review.yaml": "a39842f8673ef94b97d288224e4f1adb52a777da6981e762431ca336665b9e9d",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-reviewed.3b12728c103f6fe941ead28f3b00c6514d5c3424d0e504f8669b918863b1565e.yaml": "3b12728c103f6fe941ead28f3b00c6514d5c3424d0e504f8669b918863b1565e",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-reviewed.e85078ff74306ad85e42d2a0db191513a9b8883e13b2a0c9dc1568bf4662efe7.yaml": "e85078ff74306ad85e42d2a0db191513a9b8883e13b2a0c9dc1568bf4662efe7",
    "curriculum/l2-uk-en/evidence/a1/_state/reading-ukrainian/plan-validate.report.json": "9532b142348f0698cf56ab771fe164b3c3f4ea3bc693a21908d05e6bf31e55f2",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/lessons.lock.yaml": "b6824eb167850cc654e6a8c9afee81ca3e34ed388a07920ec60ae717a9186dfc",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/lessons.lock.yaml.lock": "7d1cb227da798acf6f78c5c81fb5a3320126e3f46dfba03146877017da236353",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/03bf9e3e73f6c9be72fde6530b1078eb7453dc294934c036485a220bcece4477.yaml": "03bf9e3e73f6c9be72fde6530b1078eb7453dc294934c036485a220bcece4477",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/03f8910ceb574d4f32928bedc81ff96fbddf7ad99bd782909a0910c96a7eea78.yaml": "03f8910ceb574d4f32928bedc81ff96fbddf7ad99bd782909a0910c96a7eea78",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/1f04ea3a45a34201ff475c1c0f9461b31eccd2384b45ecb2a3a980cc21e8de3a.yaml": "1f04ea3a45a34201ff475c1c0f9461b31eccd2384b45ecb2a3a980cc21e8de3a",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/27a4880dda77317774b6bc6d2a7e35b61bd403842929bee5bbf365086d6fa2c5.yaml": "27a4880dda77317774b6bc6d2a7e35b61bd403842929bee5bbf365086d6fa2c5",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/2993fb3d753b72913cd6a42a15bcf1daeae82ad340e0788c313cd6dd24e18b92.yaml": "2993fb3d753b72913cd6a42a15bcf1daeae82ad340e0788c313cd6dd24e18b92",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/45286920a4e48b41bf7f24d95b96f123df5ca4bfa6fb791c39178d31b04a9123.yaml": "45286920a4e48b41bf7f24d95b96f123df5ca4bfa6fb791c39178d31b04a9123",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/65c4da691884317296da228c7baeec838c4d39ebe79b9f4c4e42edb6c104741c.yaml": "65c4da691884317296da228c7baeec838c4d39ebe79b9f4c4e42edb6c104741c",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/8591d48151704f4cf6443b52df56e47b4cc295f0975cd69ec69fedf83c3ccce8.yaml": "8591d48151704f4cf6443b52df56e47b4cc295f0975cd69ec69fedf83c3ccce8",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/c14b18e42a2b0895b519461d4a0afab278a29554ef7bd8b941446fa45691a553.yaml": "c14b18e42a2b0895b519461d4a0afab278a29554ef7bd8b941446fa45691a553",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/cb29a001f4f073fcb7ff117391cab61ca09c4ae1a02878db7bdc4631fa9694e3.yaml": "cb29a001f4f073fcb7ff117391cab61ca09c4ae1a02878db7bdc4631fa9694e3",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/manifests/plan/ea374d74991a27029ae5500a101e9afada2ae94f468f219c024a75f597787418.yaml": "ea374d74991a27029ae5500a101e9afada2ae94f468f219c024a75f597787418",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/pack-verify.report.json": "25f38d4217dc7e491f34987bba8644895d3ec5480df32682b909f91854d3496a",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-promotion.yaml": "95dc4c6e5a6f8f6db82b0422486584c57fcde584c8a5d0125803bc3bb1c17b1d",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.claude-att-7.yaml": "6f44fba4d6aa271a74d5b1259fe926b3c32b3996172220592c80f96bcdb9a636",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.claude-full-att-2.yaml": "57e47a13a2b187e796f3dda9551e4d7adb356975071a0d8fdbe642c00f8be35a",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.claude-full-att-3.yaml": "e55e1a932030fa886de0d2d7f14887d7a22d90f0dd1f0ae4c9a093d8ffef100d",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.claude-full-att-4.yaml": "b636482fb9ab28bf6b8d7f861eb2652643642e4a6ecd70ae837d8dc8f3af3ccf",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.claude-full-att-5.yaml": "f70854b76dcb75c3935644e7c4600cde629d5baa5040e9e5747ff73d51f084c5",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.claude-full-att-6.yaml": "d9413b0967371d0f0ac992a585b679b61e1f59ba5522aa1659502e02975efcbd",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.claude-full-att-7.yaml": "9497d619d3850f517d5f08221396eeb1d5e3a7b0a45c045c15f4d56e0584ec2a",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.learner-state.yaml": "18b03829e85dd5534ae9113be6924c96d3ff4f3a08db037bf1e97595507da4e1",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.learner-state.yaml.lock": "8d52766e293af36e38167aec76f2ba6f265b097fda9eade388d4a6a3491f3796",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.manifest.sha256": "a3ee31cb18a402cbf71011ffb5891b524a3f8d3c2eb5c5f80580048281721d29",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.manifest.yaml": "45286920a4e48b41bf7f24d95b96f123df5ca4bfa6fb791c39178d31b04a9123",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.v1-totals.yaml": "ce21f46eb70afc1065182264f86918c8e453984f1da3f4bbc0b7bb2e9a126824",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.v1-totals.yaml.lock": "d35b5e074c737cbd450bd1612797b3d908e8e53e8112da01d1a85fe86eefe6aa",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-review.yaml": "f11da6474fffa39583dea5bbd0e4282bb8ffededc862285271fdfe6be8fb1f57",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-reviewed.2edb695b8b8c5978f34d35b0ab71f1773cfaccf711a60a30e750a796a9fdf9c1.yaml": "2edb695b8b8c5978f34d35b0ab71f1773cfaccf711a60a30e750a796a9fdf9c1",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-reviewed.6397a2eef6ed23f2f2b381925b7d282fda3d7b70bd9d34ef8bbd63fa5edad832.yaml": "6397a2eef6ed23f2f2b381925b7d282fda3d7b70bd9d34ef8bbd63fa5edad832",
    "curriculum/l2-uk-en/evidence/a1/_state/sounds-letters-and-hello/plan-validate.report.json": "2281b806d99faab625d6e1aab610e5d5dcebb9bba24952216bc07d79144bb97c",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/lessons.lock.yaml": "126f76094f1044d4c281af2d25c1987d563323b8d8eedfdac9453f80c1c62fbc",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/lessons.lock.yaml.lock": "70eba4dacf72c58f44dd3f10375b7f1b196ad6ceaeb8ce7e8dc41203217d706d",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/0e35c96d7287920ddaaafaaef7d7969a9d1bec9f46778f1b19b9d50e4499ea5c.yaml": "0e35c96d7287920ddaaafaaef7d7969a9d1bec9f46778f1b19b9d50e4499ea5c",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/2fe92c9ad9f2fa1a0d5ea0647de5441e45e376f4b762a596228d6160cd2bb12f.yaml": "2fe92c9ad9f2fa1a0d5ea0647de5441e45e376f4b762a596228d6160cd2bb12f",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/3eda90ee26d25e30253729158639787eb4cdf9a41857ad50521a88c16745083e.yaml": "3eda90ee26d25e30253729158639787eb4cdf9a41857ad50521a88c16745083e",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/46d73712950cd8ab3349e3b54bdf089bfc45529c12f0eae55bf9203dd33de88b.yaml": "46d73712950cd8ab3349e3b54bdf089bfc45529c12f0eae55bf9203dd33de88b",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/5bba4e128a0c687fbf1247ab4dc48ea8c3052127038f18a9b15775eb8d4781f6.yaml": "5bba4e128a0c687fbf1247ab4dc48ea8c3052127038f18a9b15775eb8d4781f6",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/ab238071911c12e78b0d7b9973be76482d762837de8f8a5381acf64d3f71f02e.yaml": "ab238071911c12e78b0d7b9973be76482d762837de8f8a5381acf64d3f71f02e",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/c3c58ab331b5b49c82d2cc5740bbbf4d7a52383283aa5c4ffb057b0f2fad8d8d.yaml": "c3c58ab331b5b49c82d2cc5740bbbf4d7a52383283aa5c4ffb057b0f2fad8d8d",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/db619776b2c86847e583410a68780f4ed57c20810013a29a9cb9ecd25c9a9e78.yaml": "db619776b2c86847e583410a68780f4ed57c20810013a29a9cb9ecd25c9a9e78",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/e04db3a17780342fd401a248d23885c10bd98c38d0d3251030274616f182fd3a.yaml": "e04db3a17780342fd401a248d23885c10bd98c38d0d3251030274616f182fd3a",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/manifests/plan/f49730f6e16d43a125681a060374d07c810bdc4f15192300f5ea85c4c589eddd.yaml": "f49730f6e16d43a125681a060374d07c810bdc4f15192300f5ea85c4c589eddd",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/pack-verify.report.json": "77d58688ae7172e6d350fb76bf3ffb5294dfac1b8d03e077df9df95a9ab12541",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-promotion.yaml": "f4c3949b0de69144ae3665b1ded720933c6e70573072320391497335b4973bc1",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.agy-att-4.yaml": "da246dd8c7888f08932f2c0b1e65c8b106a55c0a829b7ecf10d8d8620251da5c",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.claude-full-att-1.yaml": "67d5d3e2c151bb421be105b2c025fb114339fe9f293d7ebc332d3c5fa0737df1",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.claude-full-att-2.yaml": "9ffef68089b881bea9fb84b963c7f9fe0d8263af8ac8f6908d01478bda5ddcd8",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.claude-full-att-3.yaml": "04e66f74f438371b40649406bd3f27dcdb5bdb90d974264d388c2a1ad96d607a",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.claude-full-att-4.yaml": "a1d8a10798cbd82f428983c2e40f2b34e8cc76e37647bfa135db44bf517386f8",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.claude-full-att-5.yaml": "68b46e9be9b674625375a09f6c6b08dd05a16dd63324ff74fa89b105e6317134",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.claude-full-att-6.yaml": "95a20c9602c09889dbd716181c01671e2541fe578dc9144a2b25661049f3811e",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.learner-state.yaml": "cae73ecd8a559b41da9bbf8c08892ed282f2ba03036feccd6122c92f33a2e5fe",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.learner-state.yaml.lock": "aeb974d7bce49e9a1c9db3f86637f430cbf3e2be293260660cbb3435bc116773",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.manifest.sha256": "0383dbf1bb702f69eed12dc2998e47624f5bc89ce90652d301b7c1f744e7df48",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.manifest.yaml": "ab238071911c12e78b0d7b9973be76482d762837de8f8a5381acf64d3f71f02e",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.v1-totals.yaml": "ff5578ef71a7bd248cd73a017053301b2148b26ef5d6c456ad9c0986b2ee317b",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.v1-totals.yaml.lock": "a24442b7e42cb92846da36bd600c45c7826078644b0e97e10e33736a89935466",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-review.yaml": "1f373527ae796f21fa29f2253e6508011bf117fb0041c6bd4ed0e757b5d88273",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-reviewed.9526417c496b4ac2e1439ee60c1b54af9e3c79281b5e2888b2a7ab3b4c44ccc0.yaml": "9526417c496b4ac2e1439ee60c1b54af9e3c79281b5e2888b2a7ab3b4c44ccc0",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-reviewed.d681cdf794325c92c75da01bcf1fc102df6011d0c1d21110eb7201a6f2067898.yaml": "d681cdf794325c92c75da01bcf1fc102df6011d0c1d21110eb7201a6f2067898",
    "curriculum/l2-uk-en/evidence/a1/_state/special-signs/plan-validate.report.json": "64cfb6950d3424284608320d318646badd32c621f62383587c54a04dd0cdd825",
    "curriculum/l2-uk-en/evidence/a1/reading-ukrainian.yaml": "ecdee196660cea92a45863dc3f5d0030f5e6b9dd960f3de5342405ff53c972cc",
    "curriculum/l2-uk-en/evidence/a1/sounds-letters-and-hello.yaml": "30cec03eb07df59b7dfca13cc53e8fd115d9e27b6a872acd250b367cccc1cd46",
    "curriculum/l2-uk-en/evidence/a1/special-signs.yaml": "bd896925b2a8f4f09fb0d9f6206be87f2b326ce321dde08bd9638ffea83e7f54",
    "curriculum/l2-uk-en/lesson-plans/a1/_scope/reading-ukrainian.yaml": "1b46ecf105e05dbbdac324abb563529420f5daeddb6e061bfdad6b0e0a73d5c7",
    "curriculum/l2-uk-en/lesson-plans/a1/_scope/sounds-letters-and-hello.yaml": "84e7dcdc47f03ceea16a51811d2c327b1b84a57e0df6d88f57a751e1efeb8455",
    "curriculum/l2-uk-en/lesson-plans/a1/_scope/special-signs.yaml": "5d45796b0a6fb52afb6c62c27ef9b47abede7c4e9bade3037a7a1e4e17331b5a",
    "curriculum/l2-uk-en/lesson-plans/a1/reading-ukrainian.yaml": "d7561a1505d84ad0646574c25999442e95a4657318350a61d77726a298269309",
    "curriculum/l2-uk-en/lesson-plans/a1/sounds-letters-and-hello.yaml": "23fd9608a2ef84c23001b05768ebf9aa0360302e05dbf99f34857452f2700e75",
    "curriculum/l2-uk-en/lesson-plans/a1/special-signs.yaml": "74f2fca8de73eecf402c0795b19c93bbb8a9f59d9b1cad431cc389ffcfdcf373",
}


def test_preserved_original_blobs():
    root = Path(__file__).resolve().parents[2]
    for relative, digest in PROTECTED_INPUT_SHA256.items():
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative


@pytest.mark.parametrize(
    "slug,closing_lesson,old_position",
    [("sounds-letters-and-hello", 6, 1), ("reading-ukrainian", 6, 2), ("special-signs", 8, 3)],
)
def test_legacy_closures_require_complete_exact_byte_retirement(tmp_path, slug, closing_lesson, old_position):
    """Reproduce the three CI shapes using only generated public fixture data."""
    from tests.build.test_fresh_recap_contract import gate_world

    gates, closure = gate_world()
    gates.plan.update(plan_schema=2, slug=slug)
    gates.plan["lessons"][0]["n"] = closing_lesson
    closure.pop("task")
    gates.check_practical_recaps()
    assert codes.A1_RECAP_MIGRATION_REQUIRED in gates.report.codes()
    assert "A1 closing lesson lacks an approved practical task; disposition #10108" in gates.report.render_text()

    directory = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1"
    directory.mkdir(parents=True)
    path = directory / f"{slug}.yaml"
    path.write_text(yaml.safe_dump(gates.plan))
    before = path.read_bytes()
    assert active_plan_paths(directory) == [path]
    (directory / "_retired.yaml").write_text(yaml.safe_dump({
        "retirement_schema": 1,
        "plans": [{"slug": slug, "sha256": hashlib.sha256(before).hexdigest(), "old_position": old_position}],
        "routes": [],
    }))
    assert active_plan_paths(directory) == []
    with pytest.raises(PlanError, match="plan_retired"):
        load_plan(path)
    assert path.read_bytes() == before

    # Changed replacement bytes regain ordinary admission, including the strict recap gate.
    path.write_bytes(before + b"\n")
    assert active_plan_paths(directory) == [path]
    gates.plan = load_plan(path)
    gates.check_practical_recaps()
    assert codes.A1_RECAP_MIGRATION_REQUIRED in gates.report.codes()
