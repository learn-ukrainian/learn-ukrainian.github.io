"""Product entry for the installed lu-machinery publisher: ``python -m scripts.publish <verb>``.

Importing the ``scripts`` package (``-m scripts.publish`` does) names this checkout as the product
and its primary as the shared-state anchor in the environment. The publisher itself then runs in a
fresh interpreter under ``-I`` (which implies ``-E``, ``-P`` and ``-s``), so no publisher module can
come from ``PYTHONPATH``, the user site or the current directory: it is the installed release's.
"""

import os
import sys

if __name__ == "__main__":
    # A fixed program in an argv list; this file's argv[0] is passed through so usage text keeps it.
    code = "import sys; sys.argv[0] = sys.argv.pop(1); from lu_machinery.publish.github import main; raise SystemExit(main())"
    argv = [sys.executable, "-I", "-c", code, sys.argv[0], *sys.argv[1:]]
    os.execv(sys.executable, argv)  # nosemgrep: python.lang.security.audit.dangerous-os-exec-audit
