"""The blog builder is a local catalog, not an external fetcher."""
import socket

from scripts.crawl import crawl_ulp_blog as blog


def test_blog_catalog_remains_local_and_preserves_provenance(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("local catalog attempted HTTP")
    monkeypatch.setattr(socket, "socket", no_network)
    result = blog.build_blog_db()
    assert result["version"] == "2.0"
    assert result["total_articles"] == len(blog.ARTICLES)
    assert result["sitemap_source"] == f"{blog.BASE_URL}/post-sitemap.xml"
    first = result["articles"][0]
    assert first["id"] == "ulp-blog-000"
    assert first["url"] == f"{blog.BASE_URL}/{blog.ARTICLES[0][0]}/"
    assert first["title"] == blog.ARTICLES[0][1]
