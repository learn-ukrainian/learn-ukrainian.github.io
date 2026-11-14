"""Product entry for the installed lu-machinery publisher: ``python -m scripts.publish <verb>``.

Importing the ``scripts`` package (``-m scripts.publish`` does) names this checkout as the product
and its primary as the shared-state anchor; the publisher itself is the release's.
"""

from lu_machinery.publish.github import main

if __name__ == "__main__":
    raise SystemExit(main())
