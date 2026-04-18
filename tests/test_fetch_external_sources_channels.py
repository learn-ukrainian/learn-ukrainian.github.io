"""Tests for YouTube channel ingestion helpers in fetch_external_sources.py."""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))


@pytest.fixture()
def fetcher_module(tmp_path, monkeypatch):
    import wiki.fetch_external_sources as fetcher

    cache_dir = tmp_path / "external_articles"
    cache_dir.mkdir()
    resources_path = tmp_path / "external_resources.yaml"
    resources_path.write_text(
        """
resources:
  sample:
    articles:
      - url: https://example.test/ulp
      - url: https://example.test/other
    youtube:
      - url: https://www.youtube.com/watch?v=video123
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(fetcher, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(fetcher, "EXT_RESOURCES", resources_path)
    return fetcher


@pytest.fixture()
def fake_video_fixture():
    return {
        "metadata": {
            "id": "abc123xyz99",
            "title": "Sample lesson",
            "description": "A fake YouTube payload for testing.",
            "duration": 542,
            "upload_date": "20240411",
            "webpage_url": "https://www.youtube.com/watch?v=abc123xyz99",
        },
        "subtitles": "Привіт світ. Це тестовий субтитр без мережевих запитів.",
    }


def test_registry_lookup_by_channel_name(fetcher_module) -> None:
    channel = fetcher_module.resolve_named_channel("realna-istoria")

    assert channel.key == "realna-istoria"
    assert channel.output_filename == "realna_istoria.jsonl"
    assert channel.speaker == "Akím Galímov"


def test_unknown_channel_name_raises_clear_error(fetcher_module) -> None:
    with pytest.raises(ValueError, match="Unknown channel-name 'missing-channel'"):
        fetcher_module.resolve_named_channel("missing-channel")


def test_fake_subtitles_record_matches_expected_schema(fetcher_module, fake_video_fixture) -> None:
    channel = fetcher_module.resolve_named_channel("ukrainian-lessons")
    record = fetcher_module.build_youtube_record(
        channel=channel,
        video_url="https://www.youtube.com/watch?v=abc123xyz99",
        metadata=fake_video_fixture["metadata"],
        subtitles=fake_video_fixture["subtitles"],
    )

    for field in fetcher_module.YOUTUBE_RECORD_FIELDS:
        assert field in record

    assert record["video_id"] == "abc123xyz99"
    assert record["channel_id"] == "ukrainian-lessons"
    assert record["speaker"] == "Anna Ohoiko"
    assert record["publish_date"] == "2024-04-11"
    assert record["duration_s"] == 542
    assert record["description"] == "A fake YouTube payload for testing."
    assert record["subtitles"] == fake_video_fixture["subtitles"]
    assert record["text"] == fake_video_fixture["subtitles"]
    assert record["char_count"] == len(fake_video_fixture["subtitles"])


def test_resume_logic_skips_existing_video_ids(fetcher_module, fake_video_fixture, tmp_path) -> None:
    channel = fetcher_module.resolve_named_channel("realna-istoria")
    output_file = tmp_path / "resume.jsonl"
    existing = fetcher_module.build_youtube_record(
        channel=channel,
        video_url="https://www.youtube.com/watch?v=alreadydone1",
        metadata={
            **fake_video_fixture["metadata"],
            "id": "alreadydone1",
            "webpage_url": "https://www.youtube.com/watch?v=alreadydone1",
        },
        subtitles="Existing subtitles",
    )
    output_file.write_text(json.dumps(existing, ensure_ascii=False) + "\n", encoding="utf-8")

    calls: list[str] = []

    def fake_fetcher(video_url: str, *, channel, limiter):
        calls.append(video_url)
        video_id = fetcher_module._extract_video_id(video_url)
        return fetcher_module.build_youtube_record(
            channel=channel,
            video_url=video_url,
            metadata={
                **fake_video_fixture["metadata"],
                "id": video_id,
                "webpage_url": video_url,
            },
            subtitles=f"subtitles for {video_id}",
        )

    limiter = fetcher_module.YouTubeRequestLimiter(sleep_fn=lambda _seconds: None)
    fetcher_module.fetch_youtube_subtitles(
        [
            "https://www.youtube.com/watch?v=alreadydone1",
            "https://www.youtube.com/watch?v=newvideo2222",
        ],
        channel=channel,
        output_file=output_file,
        limiter=limiter,
        fetcher=fake_fetcher,
    )

    assert calls == ["https://www.youtube.com/watch?v=newvideo2222"]

    lines = [json.loads(line) for line in output_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [entry["video_id"] for entry in lines] == ["alreadydone1", "newvideo2222"]


def test_status_output_includes_all_registered_channels(fetcher_module) -> None:
    status = fetcher_module.render_status(fetcher_module.CACHE_DIR)

    for key, channel in fetcher_module.YOUTUBE_CHANNELS.items():
        assert key in status
        assert channel.output_filename in status
        assert f"{channel.output_filename} | present=no" in status
