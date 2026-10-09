"""Reject new literal system-temp paths in scripts and tests (#8755)."""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import posixpath
import re
import shlex
import sys
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LITERAL_TEMP = re.compile(
    r"(?<![\w./~])[/](?:(?:private[/]|var[/])?tmp|dev[/]shm)"
    r"(?=$|[/$\s'\";,:)}\]])(?:[/][^\s'\";,:)}\]]*)?"
)
TEMP_CALLS = {
    "mkdtemp",
    "mkstemp",
    "mktemp",
    "TemporaryDirectory",
    "TemporaryFile",
    "NamedTemporaryFile",
    "SpooledTemporaryFile",
}
SCRATCH_NAMES = {"TMPDIR", "LU_TASK_SCRATCH_DIR", "LU_RUNTIME_TMP_ROOT", "tmp_path"}
SCRATCH_HELPERS = {"ensure_scratch_root", "resolve_scratch_root"}
ENV_NAMES = SCRATCH_NAMES - {"tmp_path"}
MANAGED_ROOT = "/" + "var/tmp/lu"

# Content fingerprints and maximum occurrence counts, never whole-file exemptions.
# Legacy entries are residuals, not evidence that their producers are safe.
# Remote job hosts have their own exit/signal traps and no local TMPDIR lease.
ALLOWLIST: tuple[tuple[str, str, str], ...] = (
    (
        "scripts/agent_runtime/_smoke_pty_agents.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "bbde142ffb6490869b6843635b499c5891e9209299d5b86c4b000489023caa09:1",
    ),
    (
        "scripts/agent_runtime/adapters/_template.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "2d478c815c365293b10ec511e722c6a22f7736d8cc6be2b3985b1a24ba65e77a:1",
    ),
    (
        "scripts/agent_runtime/adapters/agy.py",
        "Existing path detection/privacy rule; not a temp directory producer. Expanded checks retain exact legacy fingerprints (#9702).",
        "070742859e9c156f98a28b760fad19ead849323a2ee4d7cb08e2594d990a6930:1 379b0e61e2c2edde93dea6849b152d61faf80670f394b5716d8f0838a4e09282:1 71791fb958d7ff89af03c3548cc42d32b77e66d590797219239c1fc48d693ede:1",
    ),
    (
        "scripts/agent_runtime/adapters/codex.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "ff4085b6369840dac94f3275a55ea3987a1a7fbacb4453523484672c26d88a60:1",
    ),
    (
        "scripts/agent_runtime/adapters/gemini.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "d61cf614a1d4563709473adf907ddaf1d4b91ef2978797f5c6894aabd4d1fbef:1",
    ),
    (
        "scripts/agent_runtime/adapters/grok_build.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "b6a7c1fde00f37263daa88693e024719330654bdd4bce86d64f2b39cf7c51c1d:1 fdaa98fa634600e424c36c799d3ccf0160a78cf5674541f590662ce2c289489b:1",
    ),
    (
        "scripts/agent_runtime/attempt_boundary.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "336a91794a2dd6fc26badabeae0558935c18b7072f9e4aaa73566a0f1d4b85ce:1",
    ),
    (
        "scripts/agent_runtime/codex_hook_probe.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "31fcb0ce94467070940aa78ebd4b9696d631c621282b0d2b90385855feb4f801:1 3d65f55d5f0db0ee06d2b17b472f8ada4aec9ba3dd133e7dbc978bd84345a5f8:1 66d6c5cf9813f10c85a1059019205fdf60a501d17bc4c59baf6e734f895cd951:1 a7689df548cbda2b2cf3449fb5a0ea6381755a4b33d98d7152b45b5aaaef23cf:1 bb9fdcd5f0ab4744f878a64288b5a377792450e7aef59663a9af5cfb7b927f74:1",
    ),
    (
        "scripts/agent_runtime/env_sanitize.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "df609e52aff528177c6d4cda7725564ea25af9a2d765f2de916d35d64c00d39f:1",
    ),
    (
        "scripts/agent_runtime/probe_fallback.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "4011a53ed8820d21fd8086a91827ed8cb250f8d5f02a2a4ea76601f4f8af2213:1 db01cca994b6ba71b665bd75596a2491438cef55fa6da3bba4b170f269095bc5:1",
    ),
    (
        "scripts/agent_runtime/runner.py",
        "Existing path detection/privacy rule; not a temp directory producer. Expanded checks retain exact legacy fingerprints (#9702).",
        "157c5504e246d91fc39c7a97000388fbb49ded2a1e940ab30d4a92310a851018:1 27e2a870d20bcd60a938424c008e9548500d4fdf66554af3ef7e89d14db9e54e:1 5626cf9c36f6c39aa27b49c3c3a28c37bd827034ba92e47f0e39bb9f8b0cf4d9:1 62727a005096ecac61c899e122a56d6728b1ea730538ef7070f6a36f78924ed1:1 a09bdb0bbd6dd2c2efc822b650fd74694f00d2234214ff99883dce2c68b26383:1",
    ),
    (
        "scripts/agent_runtime/trail_isolation.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "01703b3d21d72b6e41b5099d9488db2b7694f1c74d5014049431c6ef16bd837b:1",
    ),
    (
        "scripts/ai_agent_bridge/_acp_execution.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "bea382265465ea02401846d25d95ec489f7027dea9f66e84c2b577b74cc0fcee:1",
    ),
    (
        "scripts/ai_agent_bridge/_agy.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "aa58c8f3fac55b6716c1f17725ea574b98c1740d94fd59e3e0e472a6c32cfdd8:1 eb8a73e39f847acdd103c7e40afa373eea3483b0cd5261a32d9556d4e199134c:1",
    ),
    (
        "scripts/ai_agent_bridge/_job_host_forward.py",
        "Remote context; existing exit/signal cleanup traps own these files.",
        "66f0b828ce73cfa521a936ddc20086f876b0339568006cb5c280cad2c7d909df:1 bd9d67583ba97d091f3b3ae74e469afcda27b7119795018bc4f0b456c76a8d6d:1",
    ),
    (
        "scripts/ai_agent_bridge/_monitor_cache.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "ceff49eeeeabf6388b91f671c47980f648800645c0776ad9db6677928480627e:1",
    ),
    (
        "scripts/ai_agent_bridge/_review_safety.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8c3853ebd61587ba05f106d99f2ad8ebd3904140aa53da1a394913b7d53067c6:1",
    ),
    (
        "scripts/ai_agent_bridge/_review_worktree.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "40b071e6b3f317c938fd82f2e4b3af9d79a7d093110da33ea1271fdfaad92e87:1 d0003d8c19baf7ef0a880863275f9f688e694a54b98fca61e830a23a42356b91:1",
    ),
    (
        "scripts/ai_agent_bridge/_ui_agy.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "21e5a1283de9be881a0d3d4336d1515e78903f155af63effe5a69b6837475f17:1 b4701c89aaedd849e3fa95cd0528de301ec06a6a62b67a8e117ff38ec1240819:1",
    ),
    (
        "scripts/ai_agent_bridge/_ui_codex.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2f0039b6f6f39973b850edc9ae3e5d44e97e867b3100e389e38c31b38ec09fe4:1 86bbaca3bd72d7dce324066bc7911fe0ad32c21af44191bc6e6a6180820c6ed1:1",
    ),
    (
        "scripts/ai_agent_bridge/openai_proxy.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "dc055b00bb74f1636fd2dad29dd5ea4a465530e2f2922d1b73b41b346e797916:1",
    ),
    (
        "scripts/ai_llm/fallback.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "d61cf614a1d4563709473adf907ddaf1d4b91ef2978797f5c6894aabd4d1fbef:1",
    ),
    (
        "scripts/api/dashboard_router.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "ceff49eeeeabf6388b91f671c47980f648800645c0776ad9db6677928480627e:1",
    ),
    (
        "scripts/api/main.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "493e9ddc5b962f5aa0af552de2391e379476588e4edda19d063a3da3b48ad127:1",
    ),
    (
        "scripts/api/opsec_scan.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "50f5927d6114b6c3db54f70bb61068dfd94692452ba74b8cb3d67f071b8ba19f:1",
    ),
    (
        "scripts/api/release_snapshot.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2219963a5a1e72c8db05c5b74e488322d39619ce816c3876439418c1c4901d25:1",
    ),
    (
        "scripts/atlas/lexical_projection.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "f6fa18b31dc8ff11a5bd0bf8d266b1b5ca915933efa77eb84183808b8b6ee644:1",
    ),
    (
        "scripts/atlas/measure_fill_enrich_divergence.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "2686bd31b8f840e6c156a11c6886cc10937ec896e1efef8bc50dc95efa5f90ad:1 938bc3e20fb5588f9c28647e414f4c9e9be0e93fa156e26e4a9b0f7e8a845031:1 d4120aa8f29f60dada5210e6852163639909b6632adc5ba1fa252265ac1e7a59:1",
    ),
    (
        "scripts/atlas/rebuild_teacher_curated_seed.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "26d32b03a6df240391a69a7e6cc8650b835a433194bfac000f7085c99997b234:1 33905d95192c3bb95359c8ac0628235391c5df60b6a7d8dc0e27aad88e3e7dc0:1 d8ec4d638f8d1bc90c9a2b02ef24d0b0863b2102267b7737cf47fb178ca59a8b:1",
    ),
    (
        "scripts/audio/batch_synthesize_opus.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "52af38f6251f9e39cb674f363f5e0652ead9f8bb8f24b4079121eaf28b686d80:1 a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "scripts/audio/generate_pronunciation.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2a5acefa283b4719db0f655dc6cddc8f4535eafeb56cbe512695eeccbffefdd7:1 52af38f6251f9e39cb674f363f5e0652ead9f8bb8f24b4079121eaf28b686d80:1",
    ),
    (
        "scripts/audit/atlas_source_census.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0eefcf416f8a597f19725d30f5d0cd7e073358c015b657bc9e2d4ff3819d8bb1:1",
    ),
    (
        "scripts/audit/check_mdx_forward_parity.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "865df4e5f9756ba62761bbe360fb2ce08b54baf4fa1db439487f5fd7f445169d:1",
    ),
    (
        "scripts/audit/check_teacher_deck.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "b49d0c597a2d26febf8fad108c8cfa7e897b9305406322f86fcd21219fa5f7fd:1 bb84f6a9a5b2631e60e5c1fadc95095e7fc757834e84a003427c5f52d4ca91fd:1",
    ),
    (
        "scripts/audit/check_tmp_usability.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "68879d7367a938c34b0396a745974e853a597e2f89258e57cfefcfb97ce5db65:1 68ea47e29cd51c13df5b21d939e71e98ac2fb884722139765f33fd12d668d454:1 90fb6be782315eaedfd593db7baf663eb9c2322e8da931b4ede84609316533b9:1",
    ),
    (
        "scripts/audit/check_workflows.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c56cfefbf063a967029718ef699daba75bc10766c62bdf4bde8f1b09e00d62cc:1",
    ),
    (
        "scripts/audit/checks/content_gaming.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "57263571c98d6f8c2feb059aa054908a253d803c595f2eea9c0db1156d61b610:1",
    ),
    (
        "scripts/audit/content_surface_gates.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "d415891a4b3ba96f81f5beecb5647595a9ed895a909431274fab123231470c33:1",
    ),
    (
        "scripts/audit/curriculum_qg_harness.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "9402a9d0ec644bc8fc1cbaecaccdd6190b2776df88ef96c6e8a947cdce21bb15:1",
    ),
    (
        "scripts/audit/hramatka_qg_rules.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "35d64543902fa5c68f0806ab181ec81d7778125c6fdf5cb07270ff448c8425aa:1 38cd45ef5b6125491f59bc527fc4ac08c5e75fd35849c463d19d97f20a8072bb:1",
    ),
    (
        "scripts/audit/layerb_judge_bridge.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "f2524c16ae25254ba42344002c0c22dfbc15dfcb1e818b3684d6b24bb581dd93:1",
    ),
    (
        "scripts/audit/llm_qg_canaries.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "a939a6675fa5496c893bda2351817d67ad44c4c5e604bd17a54819691882de17:1",
    ),
    (
        "scripts/audit/llm_reviewer.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "fd1d85875e5f7906b665232216af8a909b36a935c3785d0cb9fbc8c5b96e0f14:1",
    ),
    (
        "scripts/audit/llm_reviewer_dispatch.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "49911dbff23a89f1632b0c2efcb9b3903605aaa2982d3fe9b97153dc7b1b85f5:1 6286c86454a4389d65b5159a0736749c962b4fd8b62a0112f67e636595206671:1",
    ),
    (
        "scripts/audit/measure_russicism_recall.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "547197605237a25fb85383eade35b889f7201271e397345306bf205f832f083f:1 61684fe365d1dc2985819bb098dce28fc2a4f354be970581ae1ed86ae51b615d:1 cf37a7acd5cedb9c675e41f1c7486f5f8be30563167426492dbfce730d76cb0a:1",
    ),
    (
        "scripts/audit/post_build_review.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "62bd73232dffe537e2e399362ddccfb27b5bd346aaacb6047de556d658b0837f:1",
    ),
    (
        "scripts/audit/qg_bakeoff.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "00aed037e863991ecd1415d1f9083e37ab17691e13c1ae5cf837b9293c7dca23:1 56a43455b691abcbb7fa293a62a0e857dc119194c7c7c41f629a6d643688f600:1 7d4d8e733e7b6eefee81b4184479c2c7247d496b9061dc6a146a54c5bccd8cb2:1",
    ),
    (
        "scripts/audit/secret_scan_local.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "038fc20226f549c076cc74e1bcf6e7f6bdf7c302953073dcb3b14ca8b65ec71d:1 1a0f36d9b700795ec85ea44bc02a3fe13cc63b1737bf94dec9ad3dd17c2537c8:1 54b47c5d90987cef554d14ffbeaa7cbd310dbef03c925b192ae061e89b71d217:1 902faa5d8a487bb0783fc4edf6744b87e265064e263fa7535c9ed1b84af09542:1 d91cba4d15e94a3b6125598916bef30583be8cfb7739c6b7fc26ee4ddcd995a4:1",
    ),
    (
        "scripts/audit/sum11_sovietization_scan.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "1c57c0f6ac43dd4fc0b4f4baba7647ce4221086b52f0e6b4700ff406bee6dcb6:1 8e756caf7dc8d194a6469f8a6ddc616f8842bb1c4a045a283175af69c1e2ef17:1",
    ),
    (
        "scripts/audit/test_deploy_extensions.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c91d3c8d2d4ad32906b7565c00fa61faccf0ebec5abc6364b0609e3c87faf43b:1 d6703f7c067222863f3ac30400dd113b2bb4f7f98124e85afbaff2efc261bb3b:1",
    ),
    (
        "scripts/audit/test_handoff_identity.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c56cfefbf063a967029718ef699daba75bc10766c62bdf4bde8f1b09e00d62cc:1",
    ),
    (
        "scripts/audit/test_session_setup_hook.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c56cfefbf063a967029718ef699daba75bc10766c62bdf4bde8f1b09e00d62cc:1",
    ),
    (
        "scripts/audit/test_thread_lease_hooks.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c56cfefbf063a967029718ef699daba75bc10766c62bdf4bde8f1b09e00d62cc:1",
    ),
    (
        "scripts/backup-data.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0edeb3ce1bd445cd16d89434ba41aedc818f7cb3170c1d14445d68bdfad6d597:1 49c6d40642d698c2220cc73d6de4541e02573cf01ee6d3fd1757e764e83b0809:1 6cfe1bfb2382413cd9e03c81a7fec3bb3c18f74b450eb004f7fc505dc47c890e:1 a2c31804b5481240afd8190574e473eb1219e2218060d2effc6bf9e6331c1e84:1 ce79491850f4dd9f295c47e4e40baab9d9a83d78a3325e1b366fc0e4e2e1f4da:1",
    ),
    (
        "scripts/bakeoff/score_b1_writer_output.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "7e4dae9e05d91e209210e7d12286a64aa57328d5f6bd745818f2ad381923f982:1",
    ),
    (
        "scripts/batch/batch_fix_review.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "902cde533da07c17bb24fb75bc65f39b83f2ae06d657c3c41e6e32eb3153bfd0:2",
    ),
    (
        "scripts/benchmarks/generate_synthetic_atlas.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "2f0e8c054e2a84517de7ddce7afa16aeea9fbf4cc962fbd73b4f0d37e28d015c:1 885534990de496ee26901de2db9459b6fc33f52def6afbef7e51611bad07cad4:1 a307339e6f3d7aa212bcc53123f14835d1a0354054ad25957bc0650a5c91617a:1",
    ),
    (
        "scripts/build/fresh/cli.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "1c57c0f6ac43dd4fc0b4f4baba7647ce4221086b52f0e6b4700ff406bee6dcb6:1 eae1df22874edeea214c15b4d2b3076b4107b01f0058e4bf22925d9104b934f5:1",
    ),
    (
        "scripts/build/fresh/manifest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "e5a2995275c751fb2d5bd2ff0998115b99025af508cf007732cc130ba862fdf3:1",
    ),
    (
        "scripts/build/generate_lesson_schema.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "2be206aec2189d58644ea43acb0569de5669cdbabf004d8964ff27d50160aa26:1 ea6c0a70ff1a361bbad41f3659f4948e96474196633eb7112344bc3412862b85:1",
    ),
    (
        "scripts/build/io_utils.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a3e4e0d4e3b5c70a594577b9f23179a35dd5a01a32eee1f8d18a77dc382225d8:1",
    ),
    (
        "scripts/build/learner_immersion.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "bfbca8519ccc8a77cd0f11681e04f8b28fe97191de7bfa3813c7b7836229047b:1",
    ),
    (
        "scripts/build/mdx_render_gate.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "ad8a2391ab09053ad717b7ee7e2ce7589fc5dd236c1bdec3e20b3fc876d291bc:1",
    ),
    (
        "scripts/build/post_processors/_migrations.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "eb655356478f8161e45546f923ebb0acde3b45aa2b5a47c54c1e38cd758d2dea:1",
    ),
    (
        "scripts/build/v7_build.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "1c57c0f6ac43dd4fc0b4f4baba7647ce4221086b52f0e6b4700ff406bee6dcb6:1 708ff4eba09689b1d580a868b6afbda31a48f51fa0ab4f7d49373936c1a9aa45:1",
    ),
    (
        "scripts/build/verify_shippable.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "567d1a2ce94560555e9c9d48358ee767614a812487e939051f188416967ac4f2:1 a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "scripts/ci/components.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "b2b6de688b012b416c9798b4fcb3a0557a8c4817750ba5c4b2155f8134050fc1:1",
    ),
    (
        "scripts/ci/cursor_cloud_full_pytest.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "afa3da731cde6c7643e80f802690aaa2b564113125b1fc3c4e9b45ee570bb7bf:1",
    ),
    (
        "scripts/ci/data_tier.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "775208f8feb1fc5c7f37b3bc5e78a7170b870f112c25ed1ba44bf1d4d3234e17:1",
    ),
    (
        "scripts/ci/flake_ledger.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "85f11b303a50dcd9aac967a500d1f85731477fac5e094cc53dec22ef5bb4af79:1",
    ),
    (
        "scripts/ci/reuse_green_run.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "scripts/ci/split_tests.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2219963a5a1e72c8db05c5b74e488322d39619ce816c3876439418c1c4901d25:1",
    ),
    (
        "scripts/common/github_client.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2219963a5a1e72c8db05c5b74e488322d39619ce816c3876439418c1c4901d25:2",
    ),
    (
        "scripts/common/scratch.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "734d70dd80103658a3af0240c447c005c3a42aaba07220515eebba41e0b00cee:1 b839113a6d989306201fbcf9450dc67ebf118a950c7b8f5e6976dfe548f3f229:1",
    ),
    (
        "scripts/common/task_scratch.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "89b2ddf4ee70bdcd40872ec1807535fb3941fcbf3d7ff8dc30b557e44716a963:1",
    ),
    (
        "scripts/content/video_discovery.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "scripts/crawl/crawl_saint_sophia.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "33e063025e24878556efa0694b1265d99e860651bb2cc741531d4141aa27a963:1",
    ),
    (
        "scripts/crawl/download_textbooks.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "b56882052f535f8693dcf8f7374bd80d14b8b6521650d208f4a8b2b4d7d40cb1:1",
    ),
    (
        "scripts/curriculum/arc/generate_arc.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "031559c9efbea89f04d62485eee39ce666a433dbc843e6bdd84584c61105d1eb:1 37ecbbc98d582bcbae860f8a013cd515b1eaa9d76d763ce0eb70a190339d2477:1",
    ),
    (
        "scripts/curriculum/arc/generate_decisions.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "4186984cbd5c5a1c34a5eb0b9d9adf286883d0403855214161966ae7ecba21fb:1 e4b73a36c32f613b517ef8f6ffa912546059cc691a27486e8ef98ed222122674:1",
    ),
    (
        "scripts/curriculum/evidence/lock.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1",
    ),
    (
        "scripts/curriculum/evidence/sense_cli.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "463896cf52010bb03278ce5931e7bc372678af953d9f2d42def060aed8fd0233:1",
    ),
    (
        "scripts/delegate.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "ff6e6a522074d377b94513a605dcf02cef3bd105dc90cfb168337039cd124528:1",
    ),
    (
        "scripts/deploy/vendor_atlas_tree.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "3e5ac5ff259db1b3a45b6b8a6e7f84c45befc97735a9e9ccdb5fdf422516ba07:1 52ccec40c03ecc9d1cb4496aff26984b804654b3354e3b26ed667fc9a3ad47e6:1 683bc12f9222df18c0caf3302ebeff8f35778ff07374307eceedf5dad19e291a:1",
    ),
    (
        "scripts/deploy_codex_home.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8fa4be117c429a9cce308b0e6e13d918871de83e437d699c8d68b154ed95e23a:1",
    ),
    (
        "scripts/deploy_prompts.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3c5471bf57ce54b688cc0d43fe7eb378f6cab5d98f4ba088a634e81f41b0e877:1",
    ),
    (
        "scripts/entire/install_fleet_external_agent.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c56cfefbf063a967029718ef699daba75bc10766c62bdf4bde8f1b09e00d62cc:1",
    ),
    (
        "scripts/entire/install_kimi_external_agent.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c56cfefbf063a967029718ef699daba75bc10766c62bdf4bde8f1b09e00d62cc:1",
    ),
    (
        "scripts/entire_context/provider.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "4cc7b902cc415dd61c3d74ba553e504f7cf6a74eab02e6016a34917382dd894d:1",
    ),
    (
        "scripts/eval/uk_preamble/common.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0d2fbd2aae689e4f994289f6bd8ca3358fd2bd1719c528d7a9220ed2b18c4917:1",
    ),
    (
        "scripts/eval/zno_nmt/adapters.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "f468a21d19528114d762d72ca95814a9a4f6c36b0056bd34b2d1b5147a0663ef:1",
    ),
    (
        "scripts/fleet/ignored_task_output.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "07cf0a83874fe534719152f1a60cfd070ffda392d9c49b2b1ffeb4c31d03e314:1",
    ),
    (
        "scripts/fleet/sibling_git.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "026eadbac42cb1f329a6c3801ab70634ae52edf4f5b1eb648fd000e5e47713de:1 aee6946c6a992d9451a6b5c5a42cd42c4c5a25a3f3b50ddfd147690b58b09e62:1",
    ),
    (
        "scripts/fleet_comms/artifacts.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "d2890a23d18c5e0e8a4e48c1f15eb999b4f633191b82bf7ae1cb0d56b9f0bd58:1",
    ),
    (
        "scripts/fleet_comms/cli.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "5caaa57aef52cbd95255244af892939f3ab92dad4e07eca0bc94a5584c4f8a17:1",
    ),
    (
        "scripts/generate_mdx/generate_plan_markdown.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "4c64dcfc00853598399469b30d558cf6365d315319f9cc68898b81b5ba9cf17d:1",
    ),
    (
        "scripts/hygiene/tmp_sweep.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "62994ee11e00aedb27e76607a22fc811aff6008d382f7dbb1aafd4b53d6510a4:1 68782b0f7a4aebb35242cb39273aad586a90a9a8d31b656c94cc747028f90ec8:1 71270c137767b302f78cffaac26b75d61fbf6997cd0a39a78b043f0f52ac4e89:1 f04e9756d512b56fe969cc26bb7c4b6215728d3491dc1eb7af534b9322ec92f6:1",
    ),
    (
        "scripts/ingest/build_a1_closed_class.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "71f0b2ca8821c07d1f66672bbebbe448c39f17bff860ec153a72b28fd94caa3d:1 e249bd0b8c9ceda07c8ed13b1ddf49247235038b2773a31a90afc68bd9c4a815:1",
    ),
    (
        "scripts/ingest/esum_abbyy_parser.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "6543462d80bc52af22ed2c7340f51bae15a7215c51dddc1f775065b3eae2b078:1 9bf9f282d8ca365bfca7daf6d02e19dcdb21cf871fbae3e4ffbd8d2760eeef50:1 b49d0c597a2d26febf8fad108c8cfa7e897b9305406322f86fcd21219fa5f7fd:1",
    ),
    (
        "scripts/ingest/incremental_historical_source_ingest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0d2fbd2aae689e4f994289f6bd8ca3358fd2bd1719c528d7a9220ed2b18c4917:1",
    ),
    (
        "scripts/ingest/pohribnyi_pronunciation_ingest.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "4783b661b001e6d9df7537eaec1de108c40f1788c4f34f0dae4b3e4c544cc5fa:1 487da5ed3028eb10825fdd6f740b5e69d7d6518985c947aaf1afff72d657f8b5:1",
    ),
    (
        "scripts/ingest/pravopys_2019_ingest.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "2a69975d0abad50dafbea682027ff86a697713e62d6cd726e05eae1d5d45e591:1 8ee8cf52f49ea79206622a855311c022d2359e5a1c70dbace5d14219120732d5:1 b49d0c597a2d26febf8fad108c8cfa7e897b9305406322f86fcd21219fa5f7fd:1",
    ),
    (
        "scripts/lexicon/admit_teacher_table.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "1a566799bc6a162364389184fbd8284bcecc6c1e17b9f7901ddc913af8de3ad2:1",
    ),
    (
        "scripts/lexicon/admit_textbook_book_glossary.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "1f6833611a28f2c3f29397b43dfc7d91256f01a93c3109882eaa9e2670de9af5:1 46e1d19fe80db38e675e33b0a3bf5d811c3b9969d38ee32bc2ba286621eaa0e8:1",
    ),
    (
        "scripts/lexicon/apply_anchor_worksheet.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "b49d0c597a2d26febf8fad108c8cfa7e897b9305406322f86fcd21219fa5f7fd:1 f74b23c4e494751935f713cdbc649a527ce14b2f041801aeececa75529ef2430:1",
    ),
    (
        "scripts/lexicon/enrich_manifest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "be231209161d5fc0b8edb27b369af52a2287a00f3d8e2f2e2cfa94595f16ab65:1",
    ),
    (
        "scripts/lexicon/extract_book_headword_inventory.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "0df2deb0036ea9439840f24337351d8a2357f4c903595c91ca407c6e16b228eb:1 bcf8650e90181f4b0c7d63ca7dfa8830243e755ce3c216e5da11e243e20fd603:1 df09136de0c30670206399e46b01a9599b2164c35a1addc6aad788ec5cab0b0a:1",
    ),
    (
        "scripts/lexicon/extract_textbook_chunk_headword_inventory.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "5a729a3ec5062cb6e6a9156bbe64b817b12c4d834310d949cffa39a5af94cf26:1 fdc3fe37d51eb1a92cdda104e4d99c6d36e1f8528eee54ea42f21c0f567d74fc:1",
    ),
    (
        "scripts/lexicon/generate_vesum_form_shards.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "d6a22b7661417f1311f461c66c47d149862e8a7b3aba5eb78cfc796040bf6bef:1 fd8e76e61e5994b2ac1f99c693f8fd59311ceb0ed4811ff6f71c43f7b2247ae1:1",
    ),
    (
        "scripts/lexicon/grow_lexicon_from_content.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "52af38f6251f9e39cb674f363f5e0652ead9f8bb8f24b4079121eaf28b686d80:1",
    ),
    (
        "scripts/lexicon/obvious_noise_classifier.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "4bbef4334498b18af7c08162e18350575dbcc59224a6ef62e4d658bb4883726c:1",
    ),
    (
        "scripts/lexicon/promote_atlas_6370_named_multiword_residual.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "054d59e237d54dcedef9a9ad2fb93c3cebd1f34d9057b0c8af82376b00bbe97c:1",
    ),
    (
        "scripts/lexicon/promote_grow_candidates.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "781448f9f47780e3fb232ded04a56ad7a04513996344a06107ddd4e0dc1bf845:2",
    ),
    (
        "scripts/lexicon/promote_teacher_lesson_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a304282e85c66a2047edf63c41cee96940cd9060b3f12a875ef37e3c56e8eb39:1",
    ),
    (
        "scripts/lexicon/runner/finalize.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "18670bb3d7ab8671d585437dea0fee23bc58b8ff35658831ec01d1488cf9aa0d:1",
    ),
    (
        "scripts/lexicon/runner/generate_pr1_fixture.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "4011a53ed8820d21fd8086a91827ed8cb250f8d5f02a2a4ea76601f4f8af2213:1 9b28f3356b6134a0fc4d29b60f56af56018e770880e1f0fd27c5dde1f380716e:1 c7bd115fed859bcca389d8a75dc6fc2b54f67b487b6d3636b87022fa433a08d5:1 e59ef69954459d3ba43425a9599c1fe476569496ce8da9077acc1237d93cf2c6:1 f011ac1de68497952e5d0058678691e02e870566db58c15a68572d1802bcd668:1 f9dd4345cd75f160f7ace84674b0a0cac101826bc82c8afc475e2e5528349e4a:1",
    ),
    (
        "scripts/lexicon/runner/memory.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "43b35eab55c8be78fa1eef3d9847dc25eaaade4f1ee9e190c32355ff0cda8d0f:1 d51c1d46130ee820317f98e648c94e3e2ac6f353a2e7f4b69b7b120e3524a670:1",
    ),
    (
        "scripts/lexicon/runner/memory_probe.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "scripts/lexicon/runner/transport.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "ba4fd40a56dde711250d1d1dce0ee1a92a04fde8b9076b8860aa5dfb2198f336:1",
    ),
    (
        "scripts/lexicon/teacher_deck.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "051ace0daa3e81b7d63750ad007e107f06d953587576cf0a06efd1c25c5eea9f:1 6d136162d8c8fae3a4570fe3816b6c36e711802089e2d3471351ac43ade309ca:1 a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1 a8190a50c68b9d999578fb04aca3d6d662d8e50b888e10b6a2f4a0970d30ffd1:1 b49d0c597a2d26febf8fad108c8cfa7e897b9305406322f86fcd21219fa5f7fd:1 cb52ae3afb7cad96a96d189f1cde7891307b1b2e29f68dbc9598720f18fabeae:1 e673d1f726041628aab49907d4fd2923557df950f68059b996b71a202383d101:1",
    ),
    (
        "scripts/lexicon/thin_page_report.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "15b74063857626b6999f5c31494e0c58d053773ed30c039d615276a99869f109:1 1c57c0f6ac43dd4fc0b4f4baba7647ce4221086b52f0e6b4700ff406bee6dcb6:1 47665105f277df7bf89515cf27d28719e03ab749bbc8495d78f2a27ba0dc921a:1 90ceaa68e89230e057ee91ba763cb83cb34fd94808ab4b22e325d8ebf0ad6978:1",
    ),
    (
        "scripts/lib/deploy_extensions.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "1a078f1e92aa553b0c8551e1504e20c7763848768e2d30c1849299358a2c39f0:1 28435ee717f4fec4b3eb74041537f3c4b0e3e57bf75e8923f9b87d09d3850578:1",
    ),
    (
        "scripts/lib/driver_scope.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3a551725531996d814535301069877e169a7e0f9c86164341e602d1f2efa1b43:1",
    ),
    (
        "scripts/lib/kimi_coding_oauth.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3a92568d336a6660762078817766d04a8bfda2a366d3eba2ebf0a3120d1e9dc0:1 e16020d500f2e1ce9c24902d87f88dc43af3a93da51c578d58863650071e7432:1",
    ),
    (
        "scripts/lib/launcher_core.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "d0f7f69348d794fbcb1386a7000fda2078482a089ebabc1790809c4bbe398ee2:3",
    ),
    (
        "scripts/lib/profile_resolver.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2e76b29fcf264565d28db8b51deb4e973a9784a416c3ffbd1644456c38350b5d:1 b7bef2fe62310b810aad578634836b08a09f128cd5b46c82f7a6ac3badb0f824:1",
    ),
    (
        "scripts/lib/rules_core.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "fffd60be46c1718004db9e44356b17be805e39cdcde98323a3b50b0239638d2e:1",
    ),
    (
        "scripts/lib/session_supervisor.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3a551725531996d814535301069877e169a7e0f9c86164341e602d1f2efa1b43:2",
    ),
    (
        "scripts/maintenance/claude_session_scratch.py",
        "Existing temp inventory/cleanup tooling; migration tracked in #9702.",
        "7f2d2173e4933e843a43a0d57cbf3a2ee3933a11be752269752428cc02552b1d:1 c649da8e164c7a8b68f692304b79d5ac74bcc3db2258511744721e904522d49d:1",
    ),
    (
        "scripts/migrate/migrate_v6_plan_hashes.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8ccd4b03740135caed462ac6093c479d25de554ecadc975c5d9b6c8b96e54179:1",
    ),
    (
        "scripts/migrations/2026-05-13-add-plan-targets.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "5ecb3be0f0bd0b487c9a078f0a13a31b9e03b367b0e07a735ab6a9386ea9b802:1",
    ),
    (
        "scripts/ops/smoketest_bridge_stdout_only.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "74102d52c8618aa51f6c938599b82c72d49e9ad44ddbba1e56811d78b64d1352:1 9584123907dfa5d3d51e321bd88a09011133916fa8085cfa4c5130de96e3cf9f:1",
    ),
    (
        "scripts/opsec/git_push.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2219963a5a1e72c8db05c5b74e488322d39619ce816c3876439418c1c4901d25:1",
    ),
    (
        "scripts/orchestration/claudex_supervisor.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "e482bf84ac2d965f49751eaaa8e73e974e0f141ce6fcd9d43773b12716fa70a9:2",
    ),
    (
        "scripts/orchestration/codex_transport_health.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "72d31d3e0b8eee72b268dd5163f03f775de89bdb8f2ed40fab3c5325ce30b71b:1",
    ),
    (
        "scripts/orchestration/dispatch_isolation.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2219963a5a1e72c8db05c5b74e488322d39619ce816c3876439418c1c4901d25:1",
    ),
    (
        "scripts/orchestration/install_backup_timer.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "da47170feba9b27f39517670475e7ac18cbd19d899099dac53904f3bc2bd6575:1",
    ),
    (
        "scripts/orchestration/install_data_tier_timer.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "160032b82aedcb2e4da07d504500f6e23fa3fe1cd7b040e941ab79de0af3360c:1",
    ),
    (
        "scripts/orchestration/issue_stream_audit.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "190bf8f61e9cdcfae7b5495b37b89ef5dcee3c2ba1e12ed4aa6faf8f4f250465:1",
    ),
    (
        "scripts/orchestration/job_host_exec.py",
        "Remote context; existing exit/signal cleanup traps own these files. Expanded checks retain exact legacy fingerprints (#9702).",
        "1c57c0f6ac43dd4fc0b4f4baba7647ce4221086b52f0e6b4700ff406bee6dcb6:1 27aa61ac8f66a6b34cfed0dd8cf8e12e93aeb31cdea4813f6f09c6062576c8fa:1 3569f08b00e9114418242100f1b22462198be378022613efeef593b3ff6fd02e:1",
    ),
    (
        "scripts/orchestration/reap_worktrees.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0dcce25a917de4c2c234ba2ec7fa119d1bb494c4609c1d60ae2b809d2aa99a7f:1 1c645b1bad7e40942972c88ee9e6651705e7fbaa0630e1dca853591282c76717:1 8f174b2012420c05fdf6b5be01655955a3931731bd4619272f3f06424f5536e8:1",
    ),
    (
        "scripts/orchestration/red_ci_known_failures.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "6fc1251070848cb64ab73fce1f4d6fbe71bda1e8ace49bd1d5c2d933895f9f64:1",
    ),
    (
        "scripts/orchestration/run_scheduled_backup.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "118d177d0ada209f9a9ddcfa00ebb99bfd900c07c176472d151ddc55615c246b:1 18fccc03f78bdd2232d842266ac496c5f8d25cf5b6427a8a2047bcaba19bb394:1 38cc41a12e748996c6eaa46fbf21404aa86957e9f05a3187d0a7b8bae6b7054a:1 7bf902c111b2ba180154459ba20e3e48d4ba892fb4f4cfc837af6bed6bac932d:1",
    ),
    (
        "scripts/orchestration/safe_git_context.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c7f063a156b2bbdaf8c2b495fbcd710fa830943229aefac0374f0c5ae1ddf081:1",
    ),
    (
        "scripts/orchestration/scheduled_worktree_cleanup.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1",
    ),
    (
        "scripts/orchestration/session_markers.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "bdc12da7c1a1cacb60552bd2d04a868c7b6bd05260b38b3e1bb18b1aba442143:1",
    ),
    (
        "scripts/orchestration/task_family/git_safety.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "e482bf84ac2d965f49751eaaa8e73e974e0f141ce6fcd9d43773b12716fa70a9:1",
    ),
    (
        "scripts/orchestration/task_family/storage.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "e482bf84ac2d965f49751eaaa8e73e974e0f141ce6fcd9d43773b12716fa70a9:2",
    ),
    (
        "scripts/orchestration/task_lifecycle.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0da86b958be6edc6c52b22b808308b79e953eb50667247079c3957349c6ee252:1",
    ),
    (
        "scripts/orchestration/tmp_leak_sweep.py",
        "Existing temp inventory/cleanup tooling; migration tracked in #9702. Expanded checks retain exact legacy fingerprints (#9702).",
        "599560e7b81b3cf50ff1dd25e273f5e6bb4350f5ee283a230971326dc28d442e:1 8ed7036da011b956010e72215eaf8552127d32872e66a4a73871a41ba1744245:1 a7ed122ad42ceb013420dcde9f53af08e03d42fac049f375bc62a5d05fb39ada:1 f18c6c9fec60b901e4149456bdaebeeb7651baeee96f8df7b177c198ef96e839:1",
    ),
    (
        "scripts/orchestration/worktree_artifacts.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "4c3503ba9ca216639ef3a294976dfcee2b8daabcb3249fca813b087ef39194ce:1",
    ),
    (
        "scripts/pipeline/state.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0e4b1de953467de63e9c0d9f3c99d445e8468ea478c0b9233b56c4d9877130dc:1",
    ),
    (
        "scripts/practice/extract_textbook_error_corrections.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "46b80f25e3ef598a7706683af7a2bf7c361af050f0b794f18f69533fa3e669c4:1 bb115b6abfa59fac9044b3c143dbac50ed82b0b016e70cd6f96da858aca885c5:1",
    ),
    (
        "scripts/practice/thin_mode_source_inventory.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "40179d544690d5a1ff061c882848d9363c86508095674e063e00ee7197b439c6:1 659970c73fdcf8a1a37692f98776276bb4be61b276081d42abd09e5f209d6177:1",
    ),
    (
        "scripts/projects/open_model_data/admit_existing_corpus.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "34e5c13bd54a9e70b380356501f25c964eaaff8067a5bcc5969233c464a82b82:1 7e81cb67920908bd2ae3d14e6c65ed7a0d1c09a3e48bae08baf49950383ee7c3:1 da011a907a8101a5811871839d08492e3f564655485453e48b73ecb7f8cb0ac0:1",
    ),
    (
        "scripts/projects/open_model_data/adoption_cli.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "7212778ad12b225414beb9bdf3f0f09c24bee812d9d528ae252289b5231bcf22:1",
    ),
    (
        "scripts/projects/open_model_data/audit_corpus_training_usability.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "7e81cb67920908bd2ae3d14e6c65ed7a0d1c09a3e48bae08baf49950383ee7c3:1",
    ),
    (
        "scripts/projects/open_model_data/audit_dataset_acceptance.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "87852c7c42c1d3282028d87d1f859a2d396af802301633456c55ffb6cb57ad49:1",
    ),
    (
        "scripts/projects/open_model_data/build_decolonization_cases.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "1c57c0f6ac43dd4fc0b4f4baba7647ce4221086b52f0e6b4700ff406bee6dcb6:1 9c8f7fdc58ed64143a902d9b9f64aac9cc160b58ddd32f760994e7702538b88f:1",
    ),
    (
        "scripts/projects/open_model_data/build_grammar_component_8342.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "1c57c0f6ac43dd4fc0b4f4baba7647ce4221086b52f0e6b4700ff406bee6dcb6:1 43cafe21f889387aaea06226e5a7146adf83e7be30fd1a80d88cd5bf56f3ae65:1 46cbe8a42acef477318044eb5f89b1afe3cf12e318f520858ae73d91740e9e98:1",
    ),
    (
        "scripts/projects/open_model_data/build_phase3_p4_pilot.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/correction_factory.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "595db3c7f83ddd56563e927cd8d016d71946937d6422f835451a5d9985b73e38:1",
    ),
    (
        "scripts/projects/open_model_data/correction_protection_consumer.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "65fcad9301acb09b063a7603d52575e012cd9726b5f5cf7ab54719f72ed63bb7:1 983cc79b9424e425c104d2931d4609822e9250fd65a3c6f25203f9b0790a26bd:1",
    ),
    (
        "scripts/projects/open_model_data/correction_protection_factory.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "92489a0a4912f709366f2614a836c862f4920daefdeffec9dfa3dceeb13edd25:1 f49b197ecedd27943df2709be6af9cebd8fa8675890e22717f71ba2f72ebb35d:1",
    ),
    (
        "scripts/projects/open_model_data/document_signal_manifest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "4a9a87da4114545d5930d02b855324fb23d2ff98fb8682b2f2936436414fa907:1 7e81cb67920908bd2ae3d14e6c65ed7a0d1c09a3e48bae08baf49950383ee7c3:1 bd67b0068e1197f3d9cbbb9b04f968bea517e3e5fb3189c28061f39b2ad927d0:1 dee9a4d4bd95989d6276200cd40172bf371c910f8c2783007cfd7fe72d8b1066:1",
    ),
    (
        "scripts/projects/open_model_data/evidence_cache_canaries.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "47b04f41e2ae85e6610a63c4720d96a8d73dd296fff5863db8aee77ff25510eb:1",
    ),
    (
        "scripts/projects/open_model_data/foundry_cli.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "7212778ad12b225414beb9bdf3f0f09c24bee812d9d528ae252289b5231bcf22:1",
    ),
    (
        "scripts/projects/open_model_data/freeze_phase3_scope_circularity_firewall.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3b5056f53c10dbbe01cac107833f6137ed4d958d151ec9528e074bfd01331462:1 8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1",
    ),
    (
        "scripts/projects/open_model_data/frozen_k_outputs.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "aeece4866f08f7e1a604ea384a261f6e11317e7130ca1e0f2e13620eeb496114:1",
    ),
    (
        "scripts/projects/open_model_data/gemma_hardware_probe.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1 c3c022544e848512ee2e8ac166cc97389c03e772a9ec7d9945adaafdc0e99206:1",
    ),
    (
        "scripts/projects/open_model_data/language_contact_adjudication.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "b072f0f638364859d54d9818815c2aa09929584d94755423331b8383b7839daa:1",
    ),
    (
        "scripts/projects/open_model_data/language_contact_detector.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "338f4271c8b3972b2591eb2bf58f42033efa78dfc32b56cd959b62184e502e61:1 34e5c13bd54a9e70b380356501f25c964eaaff8067a5bcc5969233c464a82b82:1 9d2973b9462d2b813eebbaaaec1c7bb1156a3b058038985c82e7c25fb6ef76bc:1",
    ),
    (
        "scripts/projects/open_model_data/model_view_exporter.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "26efed68126f7b63bddeadfd5f04872387a4f92e15ab7bd4a81253a69910b7aa:1 595db3c7f83ddd56563e927cd8d016d71946937d6422f835451a5d9985b73e38:1 5b7f78199810816bb04c6476a5fa04fdde831102daed551866d64a4462c8efcc:1 d42fa2f41bed0157b464c2c9f4cc1f6391969a361a2db2c649eaec8ecbda54ae:1",
    ),
    (
        "scripts/projects/open_model_data/package_unified_dataset.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "487116ece65c02a87594e950040ad7f02bf6bb00ffd1ac3c9b1aa5b58073d22c:1 c5104e9eeac83dd9938de462dd05c879fa70c18ea22d7ab8da4f375afa3c99d8:1 cd222ec08b8ecc752640976c249a000a3051bcd56802cdc23971ec5162715483:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_babych_acoustic_excerpt_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_cycle007_evidence_compile_throughput.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "ac417d9c74a7aaed41b844e56ed249b1a7d6e8e7903f076d6439ba1ada46c88c:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_cycle007_evidence_compiler.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1 b5b658bdb8e60fd3ae35c674c8444b29e55393821653cd7265becc78920f05e7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_cycle007_labeling_guardian.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "6a5f68d55ae512c875f57eca75b7c803eb63e1c83124dff2e842b04d5b27d6b4:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_cycle007_materializer.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2b2b902f34152cc0a589ddb332aa0f1bb5939ef96810c86c8c75b1349c676765:1 8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_cycle007_storage_custody.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0db93827e907c0ef758bec0f0a56ddcef3af685dcd8a6d5d72081489bd5e8479:2 330c744385c605079fad0ef8ed540d148d02d1fc1a5ce9cbb956897a2eeac856:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_decolonization_partition.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "6b0e943f9dfc16e72a3fdfee8cc273ccc9818d6674df6ff8d25d54688cc003de:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_donnu_2023_morphemics_word_formation_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_evaluation_context_manifest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1 b31846973e112507c7ff445ed748f4e536f571c612a45fc737480f3768b0b4cc:1 e482bf84ac2d965f49751eaaa8e73e974e0f141ce6fcd9d43773b12716fa70a9:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_evaluation_freeze.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "e482bf84ac2d965f49751eaaa8e73e974e0f141ce6fcd9d43773b12716fa70a9:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_fixed_release.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_heldout_label_transport.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:2",
    ),
    (
        "scripts/projects/open_model_data/phase3_heldout_partition.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "507f52dc2009a5127b89b34570f4d994ebdc8e7085b880ca7bc37b9fee033f6e:2",
    ),
    (
        "scripts/projects/open_model_data/phase3_historical_document_chronology.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "b5b658bdb8e60fd3ae35c674c8444b29e55393821653cd7265becc78920f05e7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_historical_document_chronology_source_dates.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "b5b658bdb8e60fd3ae35c674c8444b29e55393821653cd7265becc78920f05e7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_historical_full_materialization.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "1b7f5c529fce44e1d2a9da73e3d3c68f59ebebfbddd0d010d0da56510278d7f8:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_historical_materialization.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "71581b7ad37c801b9ac6f7ce6e13d1a503e1e2a6acbe85fd34f0564c660138f4:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_lavra_near_caves_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "963e3cfafc88b179ded8145f508262c3769dd6cdcb01d88314cca329b5b633d4:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_live_ingest_gate.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "6fc1251070848cb64ab73fce1f4d6fbe71bda1e8ace49bd1d5c2d933895f9f64:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_lnu_2024_phonetics_phonology_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_middle_ukrainian_act_book_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "5906dc82ca782d17e591c85b9e40700cefea270789de168014e49b3446d63a34:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_middle_ukrainian_lexis_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "5906dc82ca782d17e591c85b9e40700cefea270789de168014e49b3446d63a34:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_middle_ukrainian_page_sample.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "5906dc82ca782d17e591c85b9e40700cefea270789de168014e49b3446d63a34:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_middle_ukrainian_text_extraction.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "5906dc82ca782d17e591c85b9e40700cefea270789de168014e49b3446d63a34:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_minchak_phonetics_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_mined_candidate_guards.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "17bb82946c1c51994d0c9c5d07826263cfebd9faa976e9fd132abd7e225ccacb:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_modern_contact_channels.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "d1324ab784ab2e60d34d657505250f66db8882c6be210b33695c18a6997f62c9:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_pliush_2005_canonical_grammar_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_pravopys_evaluation_context.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "21c8425a805b0f099bdd82bea4f79dd16226e61ac5489eb2aa9f67dca355eef8:1 3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1 e482bf84ac2d965f49751eaaa8e73e974e0f141ce6fcd9d43773b12716fa70a9:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_prior_exposure_manifest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "4cc7b902cc415dd61c3d74ba553e504f7cf6a74eab02e6016a34917382dd894d:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_rule_author_packets.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "06300863a0139851704273088a937b90ccfb22dfb424d195ede2e53fce7f45db:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_rule_author_runner.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1 774f4a3e06d2a6eecdb40031c8557b5a37d6ea0e3b4d7c767d010eb5b9a49e79:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_rule_author_source_rows.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "101198311ac69990c56c501318fed09967a80b79362a271ee59a1be6ed18f920:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_saint_sophia_db_reconciliation.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "4528058f3e727743fde1ed029298eddd8207d5bb77d70fccd3785c9a388b00ad:1 c8591af17b84ff2a650f5155a550c8bc690da6a0f9337f6f46cecad925d36d4b:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_school_context_negative_recovery.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "01eba6defe382aab4efba9e211516d51c541e9fe7c1f4e91d8ada8ac4a03cdc1:1 314c2db51a184cc350c6265b14b85774a54bcc545e79a6a46e7dc3c8a66ed31d:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_school_parent_section_context.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "01eba6defe382aab4efba9e211516d51c541e9fe7c1f4e91d8ada8ac4a03cdc1:1 314c2db51a184cc350c6265b14b85774a54bcc545e79a6a46e7dc3c8a66ed31d:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_source_dispositions.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "101198311ac69990c56c501318fed09967a80b79362a271ee59a1be6ed18f920:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_source_policy_v4.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "6fc1251070848cb64ab73fce1f4d6fbe71bda1e8ace49bd1d5c2d933895f9f64:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_source_production_transport.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_source_unit_materialization.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "101198311ac69990c56c501318fed09967a80b79362a271ee59a1be6ed18f920:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_source_universe.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "101198311ac69990c56c501318fed09967a80b79362a271ee59a1be6ed18f920:1 da5742aeb5b536a51cd197bf8f27accbcff36fce939a658fd13f3ad5b46901de:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_spas_catalog_materialization.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "1b7f5c529fce44e1d2a9da73e3d3c68f59ebebfbddd0d010d0da56510278d7f8:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_spas_glyph_adapter.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "1b7f5c529fce44e1d2a9da73e3d3c68f59ebebfbddd0d010d0da56510278d7f8:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_spas_layout_candidates.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "1b7f5c529fce44e1d2a9da73e3d3c68f59ebebfbddd0d010d0da56510278d7f8:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_spas_source_attribution.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "1b7f5c529fce44e1d2a9da73e3d3c68f59ebebfbddd0d010d0da56510278d7f8:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_textbook_nonhit.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "f8b0f02a5485d6cd9c1a30e6b09fd04a17c16bda99764b267ef861f91785a082:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_ua_gec_complete_context.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_university_content_audit_freeze.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "bb75868e6b546aacfb52b572ad28a400d50def0d1c03870beef11d08072988b7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_university_source_admission.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "6fc1251070848cb64ab73fce1f4d6fbe71bda1e8ace49bd1d5c2d933895f9f64:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_uzhnu_2023_morphemology_derivatology_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_uzhnu_2023_phonetics_orthoepy_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_v3_prefreeze_readiness.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c8591af17b84ff2a650f5155a550c8bc690da6a0f9337f6f46cecad925d36d4b:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_vspu_2025_morphemics_word_formation_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "01eba6defe382aab4efba9e211516d51c541e9fe7c1f4e91d8ada8ac4a03cdc1:1 3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:2",
    ),
    (
        "scripts/projects/open_model_data/phase3_vspu_db_cutover.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "9b332c5d7cdf4e4c716ac38d92ed1cbbc5c492e41de128032660209bfa62c892:1 b31e8ab8d8d71366f25c6f39b5b1afd3f48127400f30d3cccf4d09f8a8fcff47:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_vspu_modern_theory_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_vspu_post_ingest_audit.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "da5742aeb5b536a51cd197bf8f27accbcff36fce939a658fd13f3ad5b46901de:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_vspu_source_materialization.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:2",
    ),
    (
        "scripts/projects/open_model_data/phase3_wave_l_modern_phonetics_reviewed_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1 b31e8ab8d8d71366f25c6f39b5b1afd3f48127400f30d3cccf4d09f8a8fcff47:1",
    ),
    (
        "scripts/projects/open_model_data/phase3_zhdu_2026_lexicology_phraseology_intake.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "01eba6defe382aab4efba9e211516d51c541e9fe7c1f4e91d8ada8ac4a03cdc1:1 3904ffd84161e33e4ce4bad841653162f414c9ed3e5fdbc6a38774660efaa9c7:1",
    ),
    (
        "scripts/projects/open_model_data/prepare_treatment.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1",
    ),
    (
        "scripts/projects/open_model_data/profile_corpus.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "029031d8b19fdad276614900ad2ef53feec2c7c0027a7718b65d347097586b3c:1 7e81cb67920908bd2ae3d14e6c65ed7a0d1c09a3e48bae08baf49950383ee7c3:1",
    ),
    (
        "scripts/projects/open_model_data/reference_build.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "6ceb98c8d65c394505fdaa99bca090c878ddddbc788f5329759745a9e2331c13:1",
    ),
    (
        "scripts/projects/open_model_data/silver_evidence_factory.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "50ad81c7de31850fd6d868770f985bb2912ec10886b081456acdba58e87fa73b:1 8320c4b71abb045f7d6df48829b04a6d0e2cb6bd5ffa4c8b224e1ec004310343:1",
    ),
    (
        "scripts/projects/open_model_data/source_capability_complements.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "56590cfbc7b79f5a53b6e1ad04bd71c90015130cd34214269db580a08c730ea4:1 da5742aeb5b536a51cd197bf8f27accbcff36fce939a658fd13f3ad5b46901de:1",
    ),
    (
        "scripts/projects/open_model_data/source_work_locator_index.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "da5742aeb5b536a51cd197bf8f27accbcff36fce939a658fd13f3ad5b46901de:1",
    ),
    (
        "scripts/projects/open_model_data/textbook_corpus_readiness.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0b9fc522c120a00a76dd0d9a2b8341c2715c5f49d870b258091d9d56d3357acf:1",
    ),
    (
        "scripts/projects/open_model_data/textbook_native_exactness.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "e482bf84ac2d965f49751eaaa8e73e974e0f141ce6fcd9d43773b12716fa70a9:1",
    ),
    (
        "scripts/projects/open_model_data/upload_to_huggingface.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "35f512e89d45d97b853c3a99363dac434eab977a7881748828c5dd3e741386f0:1 cd222ec08b8ecc752640976c249a000a3051bcd56802cdc23971ec5162715483:1",
    ),
    (
        "scripts/projects/open_model_data/v4_dataset_quality_evaluation.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "3d201e7701d7de84e782633a137a6abe74506ca0fe3b60ef5274263096b24ed4:1",
    ),
    (
        "scripts/projects/open_model_data/v4_human_source_dataset.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "594a04b1e04d233cf379d703f970d55498b1870ae4345f101a5e0dd92a830ae2:1",
    ),
    (
        "scripts/projects/open_model_data/v4_human_source_pilot.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "2ce02a78804e0f653d1c246f7af0915633877d64122160e4cdb0ca7fd493d89a:1",
    ),
    (
        "scripts/projects/open_model_data/v4_language_usage_separation.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "2ce02a78804e0f653d1c246f7af0915633877d64122160e4cdb0ca7fd493d89a:1",
    ),
    (
        "scripts/projects/open_model_data/v4_native_extraction_validation.py",
        "Legacy persistent cache producer; follow-up outside this bounded packet (#9702).",
        "a0d729591d304503954d2be13948b1efd382cb29d88c1b845667c8fd0b711f40:1",
    ),
    (
        "scripts/projects/open_model_data/v4_open_weight_learning_study.py",
        "Existing path detection/privacy rule; not a temp directory producer. Expanded checks retain exact legacy fingerprints (#9702).",
        "3d201e7701d7de84e782633a137a6abe74506ca0fe3b60ef5274263096b24ed4:1 6ada32d00995404287fb6a4a9286240fdb3a117cbc9010d767018770758086b8:4 6ef205e5df4397a51ae168cf81efd532300415afc9bb743e8d7cfad7f2e45d71:1 a7b86d4bfb576e0cdb3f5c4ffa879487c3c3795d95b064acfd2ce03917def5e5:1",
    ),
    (
        "scripts/projects/open_model_data/v4_provenance_restoration.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "da5742aeb5b536a51cd197bf8f27accbcff36fce939a658fd13f3ad5b46901de:1",
    ),
    (
        "scripts/projects/open_model_data/v4_reproduce_deliverables.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "594a04b1e04d233cf379d703f970d55498b1870ae4345f101a5e0dd92a830ae2:1",
    ),
    (
        "scripts/projects/open_model_data/v4_work_grouping_split.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "2ce02a78804e0f653d1c246f7af0915633877d64122160e4cdb0ca7fd493d89a:1",
    ),
    (
        "scripts/projects/open_model_data/v5_mine_dialect_corpus.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "139e4bf8342c54c844c8715bc732bd7967a22cc4623aabd59496cac2faee2efa:1",
    ),
    (
        "scripts/projects/open_model_data/verify_phase3_source_universe_freeze.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "b467c3852e869c464f37ea6b8347c82c799e6063cbd53600378f4f44911f3307:1",
    ),
    (
        "scripts/projects/open_model_data/vesum_unattested_sample.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "da5742aeb5b536a51cd197bf8f27accbcff36fce939a658fd13f3ad5b46901de:1",
    ),
    (
        "scripts/projects/ua_eval_harness/compare_treatment_runs.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1",
    ),
    (
        "scripts/projects/ua_eval_harness/run_codex_baseline.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "aba6a35792e17acd4ac1796e36e9d6c6a345dcb72f6bf7f508fe099001c09a0c:1",
    ),
    (
        "scripts/projects/ua_eval_harness/run_model_batch.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "7ab1db5703680cc8c1e4fe86f353af03ff5cdf5ca40fd04773f77596c70740e3:1 e4e86391bff543e24c0544794161ed11a63579a1bc7a8ef36dee745808f53d5e:1",
    ),
    (
        "scripts/projects/ua_open_weight_eval/hf_jobs_baseline.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "1bc1d14ace5a1117442bb3c0eb426e61b65cd15451a420c4c790cde405608ab1:1",
    ),
    (
        "scripts/projects/ua_open_weight_eval/hf_jobs_worker.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "db25448c4b9d1e16f78a9ca6998674ef77ac330e64bc9ecc868c57d5f8ac6a32:1",
    ),
    (
        "scripts/publish/github.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "dbaab3a0aaf4b0a051af47bab8ab694314213bad42497d182de9ac3964655760:1 fb991a7e78a72dd5b15e04f358c2dfd36240f012aa15761c12cde7daf16ad059:1",
    ),
    (
        "scripts/rag/annotate_images.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "33258e54986578c43f4f25cceb26855617c4b2c9168b556826ecbdd138cf197c:1",
    ),
    (
        "scripts/rag/benchmark_embeddings.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "e63af24144e98010a67b597989717f58f46fed472398a4182090e739e2800454:1",
    ),
    (
        "scripts/rag/benchmark_rerankers.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "fa11e5d86b17257803976932b8f31a817db4354bd10322a8d5bac4fc34b670f0:1",
    ),
    (
        "scripts/rag/extract_text.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "7d69d781e443faa2f16f58a16596bafc7114d6101781c29f7781a1ef5bf2e483:1",
    ),
    (
        "scripts/rag/migrate_add_literary_source_url.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "13f19d3f985a1ed7bf2f1bea5f235dc8c9bfa107a2a0dbafd02cb0ee67aec7ac:1 7657ce1f6d17244a67136ad136d2731ed93e8772de2c901a8f9ec80ec683f182:1",
    ),
    (
        "scripts/rag/poc_pair_page.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "3f2bdb5c6e3ed5f284c52a05c2b64922b54fbdcb80932330ddc0ba402dd68082:1 cdfd105f2f6940e93413b3bffb0d758ce591d7ba8dcd2110ded089c1de6857f1:1",
    ),
    (
        "scripts/rag/scrape_diasporiana.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2bd2d3047b7aa680292a7aa281a35adc29fcd922f4e0be6f9fe40cdb1a279ff0:1 e69ba050bbdd5a22259af52a0419890b6372b54bfc3fe5f2c55a5765ca3b46dd:1",
    ),
    (
        "scripts/rag/scrape_ukrlib.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8dfb989f71ade525c8668dc953586e985b960c8555cbe404040dfb8973b722c4:1 a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "scripts/rag/vesum_reingest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "19885884b91924ff86ca0793c946ea8cffffdbade930b20ae0bad38c2e317a42:1",
    ),
    (
        "scripts/review/closeout_cli.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "b3aa9a5d42617c0b68719c98f3fb48d2bf30b2aebbc3b71ba0ae3b0746329db8:1",
    ),
    (
        "scripts/review/isolation.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "0c4a24a5b2217cc910dd3a8f10d2885b296c5057b1d9f7ee569ad8d7c9c126c8:2 1399a12817031f99c9e5baf31b8ec41de26895f8775004dffb7cca51e19e8ed5:1 50f5927d6114b6c3db54f70bb61068dfd94692452ba74b8cb3d67f071b8ba19f:1 7adf98a094d640e98a114fbecaf18d76685206b5b43a1c57ba7bdf54601af8d7:1 80bcc2b818fbf35f7701fc734548e4b25b33100a670ad437dd02b0a5bfc5f2f1:1 b6e8214926c174fc8840f66ddf361629ae9c5f419f1ff7d506632af5c6956d75:1 c3e429c871ac7222790902c626bc5e793892258e58d37d19eb454233e062a785:1 d5fc1eb24e8bbab559bafaf7ac43f736a99350fb3734e2f51aaa8c46f1146113:1 de34243d9b85056a2d8d885f11d4970101fe6fe6fb75baffd2a26625b0c25e3e:1",
    ),
    (
        "scripts/review/record.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "36248c4de2a67026e213c4b9c9467ec5e62a7410f9fde1054d0cae98c046afd2:1 69fd712f2a2715265a9f6d8b775c4bc8cd79887e4ed238960ec00d9ace05baf6:1",
    ),
    (
        "scripts/review/record_cf_verdict.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "080c9905699287f19da9efeddb4554ac15a67d1da6550a5a8f670aa951ddf735:1",
    ),
    (
        "scripts/review/seeds/manifest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1",
    ),
    (
        "scripts/review/settle.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "51280e7b85ce3602ad9f74ff35902664ac5c419e5970309331dd90bcf18c33b5:1 8a49e7f855f6235992a2b3f7987f233d29ec00a16be2c1d9524ec46172db1b0b:1",
    ),
    (
        "scripts/review/snapshot.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2219963a5a1e72c8db05c5b74e488322d39619ce816c3876439418c1c4901d25:1 28aed85a91948e6dd80f12190d70504ca4184939f8340da27a27e0b4550641fc:1",
    ),
    (
        "scripts/storage/artifacts.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "5463af4fb2b73991e76b5e211403bdaf04d97813e1f3db8ab01853459c3e6dae:1 6872c6f40a0d28e1e45ac21457f6f8cb21877564cbbeb4571d6300fdbcfe9000:1 6db0dc5cb067379ddf46e6e671b0c1156648bc2fc0b14c2d60e8623cbe6d8caa:2 7c04326230eb9f14f45d886e4c20be927c2a43dd057153afafa96777ad76ff3c:1 8876f45fa2c4ca7c3b980c4434d042d6826637cc6ebf9b1ec0299911ab23aa6e:1 bedf9f2066a6c83a44aad2e8351953b0dc5795afcf0e5c90d343919a7518da86:2 cf16324e1d49563de02f3f93814b70da371b6174ec5edd79d4d0d51ecfc24fe6:1 dacc78f94ff3dea2b3218c26a80de645b748551b2b997781ca845839bde854cb:2 f70dbcd33477f87413a5a6c7ea47859602ac1f65a2bf9c48eec4439a8007dc10:1",
    ),
    (
        "scripts/storage/build_classification_table.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "1c57c0f6ac43dd4fc0b4f4baba7647ce4221086b52f0e6b4700ff406bee6dcb6:1 6d5be74edda0bef1c874b37524180a9d00e74786df83c224eeb3f0886d1eddb0:1 de38a4b3d27869748216e8d8b2b660b8a1fab17ddb59a80dc44d7689f7f26715:1",
    ),
    (
        "scripts/storage/install_data_volume_dropins.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "555147d6feaab79ab3052f2cc60928944aa8adfd6f9a30beff6b67a8fee2da8f:1",
    ),
    (
        "scripts/storage/paths.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "32a439e034e2413660306849879079698906485d55b251cee04fdaa6288b5f87:1",
    ),
    (
        "scripts/sync/promote_module.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "52af38f6251f9e39cb674f363f5e0652ead9f8bb8f24b4079121eaf28b686d80:1",
    ),
    (
        "scripts/tools/analyze_dead_code.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "52652b6d0a20d65322c20815f487b7b711c635229463d4251d6a7b8a9f1e2f03:1",
    ),
    (
        "scripts/tools/analyze_textbook_pages.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "c5a34065e28c708b3a82f5dc06a894600feed4833a04fae2b126166246943b43:1",
    ),
    (
        "scripts/tools/coverage_report.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "scripts/tools/detach_session_task.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "7757667a47ea473867ae48f130b8db264eb7f91b334a4bf1b72a680db1eb0ff1:1",
    ),
    (
        "scripts/tools/migrate_legacy_state_to_v6.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a3e4e0d4e3b5c70a594577b9f23179a35dd5a01a32eee1f8d18a77dc382225d8:1 a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "scripts/wiki/build_sources_db.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "f24942af7f45cca6e26c0a5f808e67d0821eafa8cc6fecb040d9a1ee92be5982:1",
    ),
    (
        "scripts/wiki/compiler.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "01eba6defe382aab4efba9e211516d51c541e9fe7c1f4e91d8ada8ac4a03cdc1:1",
    ),
    (
        "scripts/wiki/diagnostics/corpus_gaps/audit.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "901d817c42ccaa0d529cf8d4707e6bc417429e8a151b3a388077bb501ff2a676:1",
    ),
    (
        "scripts/wiki/diagnostics/retrieval_bakeoff_9233.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "29ce450404659d2c4d1df0ce1649be48612a465f53f3923394298e3fb74b40dc:1 7bc08c8d30e970d8bbe1217b4e37d4dab5c878e79128bcb835c546734b98f739:1 82a768536ff19763a3a840931416dcad693f9aeb3a65fea84cf3c8f60bc7ab6c:1 b49d0c597a2d26febf8fad108c8cfa7e897b9305406322f86fcd21219fa5f7fd:1 e6198f137697a713787cd1c15b304550eecdf915d9e32fbdb6425ffac3e6225b:1",
    ),
    (
        "scripts/wiki/diagnostics/retrieval_probe_9233.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "5c57ae8c3c303c87898731fcf251dfe15d0ce68058763ff5defe2e12f5172665:1",
    ),
    (
        "scripts/wiki/fetch_external_sources.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "80128fd83446f42bfe156195837deec081c7272d09b0af60820626abf70f497b:1 a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "scripts/wiki/run_chunk_policy_bakeoff.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "7a0d1af525b57c1b0471b2e22b2b2e4e99b6400c66a586557d118dd49c4f5bc7:1",
    ),
    (
        "tests/agent_runtime/adapters/test_cursor_adapter.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "0b98abe8dccf8f19c998a0be2c2bca04d07cd9ae2e9d068f40fa2d28d6c82311:1 657dc2626b67c1273e614f714108d0c0667bac91572a3d328f3347b15a1b4cb2:1 77d5a6187f89959d00459396c5de94c61380634257541ce8eaf97fb8862c2d2a:2",
    ),
    (
        "tests/agent_runtime/test_acpx_adapter.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "0385e78aa5507980ea5b629d5c9a0505f8c2293d247217edafbc7ccde34f87b0:2 2676821ad57d4157817c761ab81441d836bc80524815d710d1a80e0a5a4a145e:2 641a23093a89388944d4c1865bea0dd57f7abb91263e540f4105c0bb3d05463c:1 8072c92a8781b6cb5db1c141473861173e683bc39e8c2147ed840ad176f948b5:1 f95316e83c3ccee9f6fd4998a9de78a167dd4280adb5d63a27a6a1b190fa9d1b:2",
    ),
    (
        "tests/agent_runtime/test_attempt_boundary.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "037c6bf4d09abedf670f51b6d2349d84b588266c99dd9911b54d55ca878725e7:1 ba97e9ec4b958f513dffc90defe1c9efebfe3467bb35daf07a2e637edd0b9437:1",
    ),
    (
        "tests/agent_runtime/test_attempt_network.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "63a06ebb07c098eff2937c5c56ef33a4f0e21d6975b0ad72d421e2211cfac2ad:1 ed1bb72831b49a1d3a84ac957a07038e3b2e29e6ed8a998e55840acd4bc38eff:1",
    ),
    (
        "tests/agent_runtime/test_claude_permissions.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "97dfa412105444729b179ef986be6cb807e9de3e31f8f4118b0271cc015cd303:1",
    ),
    (
        "tests/agent_runtime/test_grok_reviewer_tools.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "20cf39be5272210ecf3f88f168d64d807b8d2c508e0d552d7bc8cd72a980b197:1 7ee84c26316c410898f53ddc3d4d4b8f6257be35e288603aa4faef00016f2d6e:1 e6da05fd4bcc084aee0ddedc5bcc99ad41913552c1fd75ece4a431aa71d950fc:1",
    ),
    (
        "tests/agent_runtime/test_grok_stop_reasons.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "14148263b724ecdad8ad1832cd7c5e120345d6c0a93d78197b15081dbc583be4:1",
    ),
    (
        "tests/agent_runtime/test_review_mcp.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "a0515e9d9d82b47b2e22950ff6a53e16e01799649d6d2075d710231dd2e81bba:1",
    ),
    (
        "tests/ai_agent_bridge/test_review_worktree.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "d809bad843a66853377c4c5b3a6cb6d74e1028fdd41ed71119ace869827d0079:1",
    ),
    (
        "tests/ai_agent_bridge/test_ui_agy.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "2770de9a110012ac566c97c7984b1f70c814d7a374603d25b26508e479ce56ef:1 b0da86495d047d4ae0b5cf082f3fab2d43da778b21d8c16e94fd46613cb7f6da:1 c50482896c26790e72a87599d113fd550fb5f6034c75cadb4422b3354811691a:1",
    ),
    (
        "tests/api/opsec_sweep/test_opsec_route_sweep.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "ab88d4d1da7a82c6e641ba9a69e41677bceece895281f2dd5d4889a4e14afbe4:1 ad8d8584c67b9117388ca226a8b99815acdc7ea7fbac61c3bf0d609ee06a46f2:1 c3dbcd1207e1835f554d4d7fceca78c84ee60f6f8c9ee054c32e11d53cc43260:1",
    ),
    (
        "tests/api/opsec_sweep/test_opsec_sanitize.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "a3bc6f039b958ad0c9e2b4532d58759c3622d18f162adfed4697282362197409:2 fc7c3103cba39a68640d5b2667ab17dba2467c3bdb0d72ca420ec5f34e92f224:1",
    ),
    (
        "tests/api/opsec_sweep/test_opsec_scan.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "ce42f946689608c583dac2f1d10a8e3b1c711e08b2b995be003abcda55acc9a8:1 ed526f21b1c9ba360a4a48a24fbbedfe97cbb3601418dfe718d9889531a8b8b1:1",
    ),
    (
        "tests/api/test_atlas_jobs_router.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "5dd5fc216d5d873543123517e57dc53346e05c0f83da6de407f28477ed0a8e30:1 e2e6c1a4a55873b91ca0ff95b4dad4511982d562665c20cfe48d35eb7c3d632e:1 ea8c2c285b4106c1b154f412391fc0e20b40c23097d88aac63e3c11af584dd29:1",
    ),
    (
        "tests/audit/test_check_mdx_source_parity.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "e7cf38a7d98688f51c749993fcc205a4446d87368dbe464d8755f2a3915e4531:1",
    ),
    (
        "tests/audit/test_check_tmp_usability.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "23f292b63e60765f0d23bd61bc2e26a3a802f2b6affb4ee8cc88ec89ae5d12b1:1 aa8d587d9c870facc14a95580c7a42597147eb09db4a1b2d04bf0a578a80d89e:1 bfa1a3ea130a51a45a681a66db33a0e30e19126864beec97f727778ac03436a8:1",
    ),
    (
        "tests/audit/test_lint_agent_trailer.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "0502ea1bf78419862de04f2126c265e5efe00419c66a68d2b87d0724e284f6f3:1 970a8f9e04f29e15a2aa2a7af69a39791cc89cdaa917bdd00b7b21ea757ce341:2",
    ),
    (
        "tests/audit/test_qg_bakeoff.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "01a293307cc1064ca1ca99d5b9bd7a26756602c2d9e174a196da22164cf6885d:1",
    ),
    (
        "tests/audit/test_qg_shadow_run.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "b1ca26c0d64e0ee4ae93ed4c70e48fdd94e3a9c605cd40539017da3c7006cdf1:1",
    ),
    (
        "tests/audit/test_secret_scan_local.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8527103b115287bb6aa28598c1e003e056be9c35c56536115dd5af368d43c8d9:1",
    ),
    (
        "tests/build/test_fresh_cli.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "4b1299fdc76adcba7dbf842ced2d5995f2055b74506448badc7f7711a15f0be5:1",
    ),
    (
        "tests/build/test_fresh_path_guard.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "7ba29ff00a51c6345994c175216930f1441a1f3e526e4cadbf7fd236db653329:1 974e64d68784c105870036fcbcc4a13cb95cbd594fcfc30968f85df59aa7f50b:1 987d5f2071ad8fee27ebb657646d6b2b250e6110f173b1f6ce7c6600671d6130:1 a8d7f83ee51e9f4c3c3e0163b4dbb8896611d082d76a387833ef20f292e81b58:1 e564f3201ef219053dd8b6b8c163c46042ab6e4dbe2484c131179c197568724b:1",
    ),
    (
        "tests/build/test_v7_build_resume.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "22e89f225ad0a570d4bf45c6d9811f3f18373390b7b1cfbaac11d48d1a7fbf98:1",
    ),
    (
        "tests/conftest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "1b17f851871203e4e6c09dafe5943914264bb6b9c91ee11bd532174b5f781f19:1 e065cf96877cc574f3320f85a481bc4d39e408a72e7db9c40d8c5a90958a9024:1",
    ),
    (
        "tests/control_plane/test_authority_health_postgres.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "18c3fc621a64a86860aaf5c901d050f63a60b6e9c4394b09a438e35e8c613bd5:1 f9e65008ad67575f185dd6b60d1816ab37f7660ada38182db9731abc8067666d:1",
    ),
    (
        "tests/eval/conftest.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2cee5061b643682bf29c4d17ef12d47d2126ab68e3171a7beeafe51b646485b2:1 55f124b87287da321fd2829dbd502655235cafee78c963f982d2fd61280960a3:1",
    ),
    (
        "tests/fixtures/atlas/build_runtime_shards_fixture.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "5d8c58293985efa4c738390837085d9880d64baaaac1a2eda2492db9219e6f9c:1 a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "tests/maintenance/test_claude_session_scratch.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "a73144ec31e1e70a566534e56044cba6207bf4b5c171e2daf7ce655e7dca111a:1",
    ),
    (
        "tests/orchestration/test_job_host_exec.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "169d4511743538b9be608c16cfd4a86ccd75de5d018d4cffc3f6bca40b8eda67:1 35eef957e7ac6dfb323982b5acdb0d4c5ac6bc3e41dba5a3f06a0d4ed8ad76c5:1 3cac3970d6434c27592340c8750dfe8c885f88ad6d33a46e20e461d810482bb5:1 6d0a3a07137da113db85eadf897776f58b8104244fa38a91b62e2d6e12fb9290:1 78a2828693382f4e53c60d70ea534f892706f2cdc6a74b1e3ff1f4a888c3f0af:1 9668994dd3e78910e686248664fb372b4ceb8c3b3c73f7394d646d27ca2e5199:3",
    ),
    (
        "tests/orchestration/test_reap_worktrees.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "f4e010fa5c91d855fc50abbc07ceaa32713537e3dc4db75bdc6b6c240d198a3a:1",
    ),
    (
        "tests/orchestration/test_scheduled_worktree_cleanup.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "34728b6332c2fce647620c515fe606044efdce7e22c3f35a317a9b25d3f49625:1",
    ),
    (
        "tests/orchestration/test_tmp_leak_sweep.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "92442fd8c2eaa8c895b85d180c8e41a42fb42f8f5e24e3d1362f084660dc01ae:1",
    ),
    (
        "tests/pre_commit/test_check_no_bare_python.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "9e80994f0b439e05f3880132a31e13fa097d3ea4cf8314ff55c688599dbe5ab1:1 cb9cdc313f79967100f6a3e49f923f4f18a947ae207ba12941bd493b9b0f2e65:1",
    ),
    (
        "tests/projects/open_model_data/_v4_a7_real_slot_fixture.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "cb65ee3b978cd4c04e730b5448355d4039bde893bb12a66bd00c8190f2539e5b:1",
    ),
    (
        "tests/projects/open_model_data/_v4_packaged_runtime_fixture.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "42ca6352f956c0ddc6e49d2175d88445004b5b1a735ab87cdaa7308b3c1a9743:1",
    ),
    (
        "tests/projects/open_model_data/_v4_shared_runtime_fixtures.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2c21077af928cf8552623d6a3620a12311d8739bb22040adecf476a239f9e0ef:1 605fb8639928f90750b53bf5a571ef513c548afe9fc6b5626dd31fa252a4226a:1",
    ),
    (
        "tests/projects/open_model_data/_v4_synthetic_chain_fixture.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "d83529c21c7a99195f2062a819ffb7142c2c9e7452ccb26e669b555f606a8f4c:1",
    ),
    (
        "tests/projects/open_model_data/test_phase3_corpus_miners.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "29625b19dfa8c416838b61c386b62740fd9ca7505bb07c941b944939b28a4635:1",
    ),
    (
        "tests/projects/open_model_data/test_v4_decolonization_reasoning.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "832075433fe6fe3f0f199aed1c990e9a46cd49771a56b8222ca54ec106c9e37f:1",
    ),
    (
        "tests/projects/open_model_data/test_v4_source_custody_access.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "39d8c26e8151b1784acce0c65b137c8431cfd9a70e7db126a929feafaede57b6:1",
    ),
    (
        "tests/rag/test_benchmark_harness.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "27d7805ba12bfd4dd5da84cec85667d6fe6771f0134e7025980bb17a0a021887:1 5baee993f64ddb64ddf51382fe4ea53cbdc0dbdf8d8bdf9ad0de79bcb72560e7:1 a465ba02db96fc9d16efa679f9a6f570ce581b5286cebe92f42c3be9f9755072:1 c900af2a7ca71d8d943b4461ba6d7ec662425616490d5e2034f41520158735a7:1",
    ),
    (
        "tests/review/seeds/test_adjudicate.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "d87868c810a89ee3fa1474cf4fc4647c69ebf01886865725278719bac2de08f8:1",
    ),
    (
        "tests/review/test_temp_lifecycle.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "d5fc1eb24e8bbab559bafaf7ac43f736a99350fb3734e2f51aaa8c46f1146113:1",
    ),
    (
        "tests/review/test_template_admission.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "4a308850390f5aa111b55e895915b9e5e80e39430043b6c3fe7a03fc5aa11e72:1",
    ),
    (
        "tests/test_agent_runtime.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "317d04c50054437108050cdaedc99c96edb14a6e92c85fa5b02c89a07ddfc65b:1 ab58b3198f71daa1600a43aaebb0a1fcd4df069ca24aac5e04532edf3e9dab75:1 c8661d1196f51754c192f1236f03c1f60014e00bc9f86ec36c5c4bbabea8cb8c:1",
    ),
    (
        "tests/test_agent_runtime_effort.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a3d7dd3e74201f7e9dbc1ace12195f2a328686987964c5b76ffe64c098357f82:1",
    ),
    (
        "tests/test_agent_runtime_env_sanitize.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "00c81db6ac6e12ac8a15612bb20ab59421cdb05b6d57f0f676a1d0c2142c14c7:1 587a8321f0c8593d51f1bbc5ac465899851c85fd0f3858326a5a14446a66d285:1 b05e8ab098fe2aa50201893b605fa6376c543d00ebe3481f2d33b72d0f02a18f:1 b0ef84eb140fe780b125aa15147727536f0e2706d21976526efadd7b563ced5b:1 cc77d44849990fe9b498a992839fe364c07d810c8355df81413d71db35c01dbf:1 cd2c04add61ae39780f454916b92d9fde10e3fad577924834acc718eba4caba9:1 d278e25f6adada5d87b66a1364c2cca3696ada63eaf46d2a0231d8bff42a9a28:1 e57675f0d44663b10cea1d278b24f23d5f76a49747ad313bc04142920647ceda:1 f1ae2347f419225140df736e8bbe882f990978fbfde730ecbc92644e33d9ae00:1",
    ),
    (
        "tests/test_ask_hermes.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "583cd88f6a966934a12dc9249856531b7025cc46a402c9dfcda66d888c146d5f:1",
    ),
    (
        "tests/test_atlas_job_protocol.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "15716cdf792289dfc44f56910d3fcb8d28b2c3e95b807c5106734a014511b500:1 19f3a543f4f0486d6ac3a31bec6a2a38b0f5e35baf12821a43b30bb8d854fb7e:1 34492587ed174aef0b19cb5e6922d2bd49289f9425e20eb0589035cc9e8ecd5c:1 4bb5ccd420379eaed73312bc81c4fd4606d036bd92029af3904a9bd7c88bc977:1 511acda571b82ad925b842d4c398de6c1bc4bbd73675beb6bf53a52771a65291:1 764cc45cd712603dcdf845c1d4b81372f1183e6b551dff1d4b077babed2403e9:2 86232b85e1881e7d84a60ab5166412ff79e2be82bb90161a32629f1edefcc733:1 8e7ac9f8aa37e299488d5ed0d5ba7dd882e1581e767bb7f27e86daaf6e07be41:2 c1b78efe7c80607993af2e5503c4ab2f4f428b8d84136954654b374c69d0cfdb:3 e2e6c1a4a55873b91ca0ff95b4dad4511982d562665c20cfe48d35eb7c3d632e:2 e6bd73273c1e7dba99c601d9844f9ad3f83a104a2d237353fcb7397bd14d2484:1 e706ff371a4aa11b55583bde6279b16d3931109fe6b117f5ff21e7d1181048ca:1 e8544ce2512fe5954d4e4a2fe74f5d02318743c6d451be2966fbd6ec4eda83c1:1",
    ),
    (
        "tests/test_backup_data_script.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "94b9e57a5011f479c24850ea0f748e0392ae7ee5194c79a163306ea3c994f419:1 fd63bacc44f78412e47dd0e3f7e21993bdb757e75cdc3e9276645351dfa20196:1",
    ),
    (
        "tests/test_batch_fix_mode.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3cfef27c84a34dd2ecaa7d91e3e2d4e209073a6640d9628b05a969b854cc86d0:6",
    ),
    (
        "tests/test_batch_fix_review_model.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:4",
    ),
    (
        "tests/test_bridge_inbox_cli.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "73d9019684d51706aaae17018e54c11e47ceb8248c1b6bb8d3d5183682437881:5",
    ),
    (
        "tests/test_build_sources_db_safety.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "64a66e5033ebe52b65971e7bd8adcd2cbc28c1ab9f820a8e4799c22e954b1567:1 f720b80c30717559c7b5534ca7fc43b10fb22c4bf06ad4407731d623f2df8c83:1",
    ),
    (
        "tests/test_certification_evidence.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "d03bc832067a4af0e3ffc10998b2af6214c85c1e7a2145ddfbbd331fded7468f:1",
    ),
    (
        "tests/test_citation_check.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "aace06b3a2442d7ea6a0173c05a4b0569fedea5040f42ce4f06d81bb5672285c:1",
    ),
    (
        "tests/test_claude_settings_permissions.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "068e5bc97d05574377b194c04625af29291192815cce684c8d1557c3be9580be:1 70d00d822877164ee66575338f93f8ab2ecce30dbb66a3dc4b920f841fd1d7ec:1 a67c5e5797b4ceffb0843d6eea984c98174620c0ae9e52906602951ae9b6c123:1 a7d7b3483122dfbee2b312562d5d700154596a9830e5e397ba95b98db1025d78:1",
    ),
    (
        "tests/test_clear_stale_git_lock.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "3136be78eb917baa65e4b4acd13b41eff81bca91204e7c7e7e1c20a4da28569e:1 5aeb942d390281fc0fa994707545105ce501c740b360e32423f99461c50ef0c4:1",
    ),
    (
        "tests/test_codex_bridge.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "61284c8b646546d57d60409d008be38134d1c089a9311b8e57c97b8835991467:1 d1795242af5b441564ae91326632018c268beea0f3dac5bbde1cc6f0aa3fd838:1",
    ),
    (
        "tests/test_conftest_worktree_guard.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "3612fcbe709da936ea0d1873371ab7940c33963d04a1368ce5160aa43e5e330d:1 55d875a8d2a66d82174ac49740e36693d87ea47f0b6f6f6b8c1ad16578ddac10:1 85cb44bb2f270f68e338e8197e2489438baa0cbd0f3fdbd440ff713b0464ad50:1 9b7557820a299807a365fb1e828f666a6927634d538d71ee9e177f962890b90b:1 fe476dd3805d13e6aab0fc8892cd10c9f55ad24d8fb81779045ea76c6dc0c92f:1",
    ),
    (
        "tests/test_context_profiles.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "6dbca71523c67116657bf7ff05feb584e4d445df73e18ed47d08b15e5ca7b217:1",
    ),
    (
        "tests/test_coverage_batch_agent.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "7b0559e9c0f5aaf008425371e63e202b088c53dc9ee71451d05c65c1f1dea1b6:29",
    ),
    (
        "tests/test_coverage_bridge_audit.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "0da758d1bbc117d5869f3184a60562a4f4e7e0fff754bb8428202045aeb22ade:1 2d406e7daf9227aaea86990d198b3119cb94c7f17f174861223b200c2a2d16b2:1 5b87ee12783b64bff080ca2fffa592c237344744576a593b8cc5f377c14233e9:1 d2bbe3a8ddb22edd0dda2e34f482e04abf35a75523138059e29dea33bc51ef24:1",
    ),
    (
        "tests/test_delegate.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "33f0583cd7c9a5955f851b1f7129c74eadd35308f59e735b9915596c45c3050e:1 4c93ba07004280171691c7a937f0ab990fc01bc70a984628177794e7ed483c46:1 50f5927d6114b6c3db54f70bb61068dfd94692452ba74b8cb3d67f071b8ba19f:2 632590773554973a0ad1e4e55a86eac6ec96e7defb18e77da7ed0381d165b017:1 70926b0281d7d07271b04529b2986ccbb7db229bae7231ccd9b801e17473aa2f:1 8485f898695fe7220b4734debaeefb13765ea8c694a0279b3b891e6929c2f175:1 8b870bb888fbd23c3deb973080fc6e19a9a49b44c67ac9cf85447cac1562b643:1 8c8d172dfae7820cec62bbe1d16acfc6292341e409870ab2c4fba2c528c77552:3 b9fb0b1fa2c3073b4dfe1573194920e5e3830248609b8dd1a893b63933497793:1 e3283a47ff84da2099322ff56bf6c3df86282c321d7d236d77d4b9ca6f55b479:1 e4957ef6a1af4d7f73bddfbfba66d6e0155da1a1a2910986e9509a4adadaa3ac:1 e6b7baa63b5d1f5cb1f444df2100444a8e016fedcdcb11a12c6fe8d2358aa39a:1 ea106d8e0097a0f65c300dd488275e16e7879c06a94192fc80b08d4d7d2870a1:1",
    ),
    (
        "tests/test_delegate_api.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "f1ba4371fa43ea259a115979dba64872159c6a7ef4907f9ede4f0a8faac2a602:1",
    ),
    (
        "tests/test_delegate_primary_integrity.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "9731e2b13468a18309c3631198515a58523bc2e0e963b59b8bb32a9d0dfb61e7:1",
    ),
    (
        "tests/test_delegate_read_only_db_lookups.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "4cc1be937798d635eddb3739d7f484d29721fbad1391e19ff6ff6c01daca2b52:1",
    ),
    (
        "tests/test_deploy_prompts_orphan_guard.sh",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3a551725531996d814535301069877e169a7e0f9c86164341e602d1f2efa1b43:1 c56cfefbf063a967029718ef699daba75bc10766c62bdf4bde8f1b09e00d62cc:1",
    ),
    (
        "tests/test_digest_codex_rollout.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "tests/test_docs_catalogue_markers.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "4917a35d487cc823bd29221347a0b9c2ab395ffa2bc719f7b85f17fc3a144177:1",
    ),
    (
        "tests/test_env_sanitize.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "9ac5d3aa786bfbc36a93ac2f4f79f7c24722676308136c650c74b5ed43d195b6:1 b96530f467e6ea8e193b2719502c700379d45be9fd89c64b8e9ad00b234cd572:1",
    ),
    (
        "tests/test_explicit_pro_routing.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "tests/test_fleet_comms_message_plane.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "488de6c1d190afb73355a16a9f235a631be7520d7aefeb2e6899355ba3d54211:1 9f7e35ee95164b710ab481d43178d96c37a7c7cb5ec54bd73859b55bde1c8de7:1 f0d727092f6dfdf01b79901d669570d7d91a038de8c22e111e7c3708aa88faf8:1",
    ),
    (
        "tests/test_fleet_observer_api.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "e479568f2cfc71647dc38593c01de322c2480866c4204b5c86076affe5de1ab0:1",
    ),
    (
        "tests/test_fleet_pr_identity.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "a62be7b3bfe9f9444bf8298b5321039a608af1de7f94bcc131bbecff3d444332:1",
    ),
    (
        "tests/test_gemini_session.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "67c8630e12d9d0743ef949c3db7ba9baf7f3a19df9a7c890b6a8ea8ebdbf52aa:1",
    ),
    (
        "tests/test_goal_driver_stop_hook.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2c80c17a314b718d5b0a80291f8953342d0d2f238398cba0c642418bdbecdd6c:1 7c9bed9d063a9190f7ecbabfdafeda3ced0b5bb34d751cb8e7c5ef4884f7c0d7:1",
    ),
    (
        "tests/test_guard_admin_merge.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "62f8e1429422bff63889e1e04e6dc2ff90af3ccfe4a125f0b3927b69c4a91685:1",
    ),
    (
        "tests/test_guard_branch_switch_in_main.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "54b1b78eb391550f8c689b50ce09c11c51935ea9f3134f8a69ef763734a847ab:1 cb11ee9a04f4b90a8c8f1f03ea9189c1ed715db74416866e1d1a041cb76a9b69:1",
    ),
    (
        "tests/test_guard_pr_merge.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "0a498667a00cf3866db6176890675ad62d7496fa0ffea45610c7e34336470768:1 122c346d125ed8ebdb8a8818e9a5edefb898cbc92b7492514b2e15ad71a35945:1 2d058860dbe75707e5f38cc37f47ed2a210c03f500cafa035a1275d1d185fa72:1 3461c11ec5fcddb90d1569b429f0aa6ca6dac6a70c205c9e48fd8ca34ede53de:1 5e7a159030dfdacff5e323bce2cbd6bb7750b0e7bc52ebae64d355b33bb272c1:1 6664d6c73cfd2f630f766f77884ce8e69f49ab9f1130a82243622a112e7cdb76:1 7a55735d436a1f315b39e3a3ea7efc4f352028496d5d62c016e55939306c9fa5:1 c9b6354b2cea734f3a992ee7110d481b4462dbba7de8b3fa8caad118a72d7a70:1 e2b25dbf760687366dbc531cad40d9b8025d25716a45c8aebf42b3e9fb5a44be:1 e82bb417b3cb300ac23b3d7ceca889102ee94db5aed23321fa946133e526bfed:1 f34a1c616d39d51223abc59dfff8bdc0ef13330bbf004962f13d9291e80f4c1c:1",
    ),
    (
        "tests/test_guard_primary_checkout_write.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "000da3cdd3dd666c210122021c0bbc599c3f73d12a3e5d77fd89b4c6318fb8c3:1 00cf1ea67ae9fc2eb8f5d74354c9efe44dc35ac6ec85aeb24c823cf809277322:1 019c5d66cc923c3019ce397017876fe9aa09e22485d4dea17f8cebaae3f2e272:1 01a1511f55d9d426dacb0acb4f2092d45b18d36c877f6ccabe47d6175b9c8e96:1 0249959b15badedc70105ac3fece60cbc1df91f8d7251bcbcdceaf89824dac0a:1 03a8aa8e6a73f3fd71cb53a413fe9f5f8fc4736375931102b43daff29e0c5bcf:1 03e06bc89e1288f3685c32ddddb514df34947a28ee6bf30843901463f8190b81:2 050443f8f221c128669085250d1bd8a8068bcfa54842970aeb905d1d1f093076:1 05948acc63300032857ce7b199875740e080c9806d02459febfdebbf892290ef:1 067a7eb2131b9bcd33d88f30580f7bd041fc0cc972b9557b7bdb7a21d0ec3b8d:1 06fb12fdf96477ec3227a960f31e5cb1c7ef20ed1e7df7321d7064aaac7dcaf6:1 0afe88998a44ce2baef98d15f4dbdd4661274026645333d85b691609566327f5:1 0b19628ed438327664b7136f653c84e17e37b35cee5d7523acbdab2c495c3c24:1 0bd6c1fa7e48a0fc84ba4d977a0cf293eeff78bf364f66e245b8115b410a59ab:1 0d1573d4b7bd98e07b068f1572e3455b099ef1a8aaba1bae7f4e5f51afc8f06c:1 0d484c558579f7147410801a045ec1b86280b5f1388fa33278c5f5e4b670f591:1 0eb152c8f375d83ad6de8e9e72e5eb7309f372a190062fe1f891c559cc1cfcef:1 0f28db7a7542bc428e5b2cbacd58cc4b7b124aecb52b4179c27bf377594f661c:1 10223a8c761bd9690999dd613cf127a80bf1bb45e1ceb579162ec984de0af11e:1 10712ceb5e28e9ec76e1b25f61eb54ff2895f646b948baf54094c6cf44108ea7:1 11db99ea89ddb9bff6180d4013f28290c6fea0af04b1053cecd2a6cc924b71d8:1 124937c97cc09ac54cfc12b252bda32cfec52d94ce565c8df0afb57be5c35068:1 131765dab492291477954a943de3d99b4009a25a80ddba4828be20ddd3bc6e22:1 13d9d9ff1cc92f716673cdd1b5f7def134fa0532e85befb54d76fb4c80f2f144:1 13f6d693aacbffa7a0870dc28823571cfd6b0684b1d05297bc0df8cb02ea3d8f:1 145a5faa8307e61573f8570cf283f9c41bf4c9b9c1c8dd6d9f4da43447d0ea79:1 154d2d6168e13ecedc0f024838f98b13f63fb2a0f22c02f3f7f59268d229ed93:1 1555186fe4e8e79b5b2b38b8a26f4cc9510fa7f1394f0db03a66af146c8921b5:1 1903a323a8e917d1fcf3bc6fde6e313ddf9448b023a6b6b8467d45367851da77:1 1ccb186cb357557b3430512853fc3ac3f39b930d5c99a6cfa5f6193f978a5ec8:1 1d20bb5be2867c07cea39cc618c2d94108885b423582f793ca1187b69d4145b6:1 1e4023c9a4caff8625cd8eabafdf443b237740a3cb982f3a58ee0123f6020caa:1 1e8b1eb388c52d028ab9a6711d9fd55baf000feffb3b182a8a2d50c2c54a1f6d:1 1f59c629953e178851089c57529af3ad4ae8f1e44001612f20eaf532347d2b98:1 1fd7de1113b5eab0b2c19d81d416cca31f246c3b0778399bb1cd1fe6ce954106:1 20ba8a4a9eba5259d29801552d16d3270401d77b00fad1beec6fb0dd17e51981:1 211685450bd017f324172659dfd0528f6a53dc82b1d8d0ac7d5dba7c16074cb0:1 226e7427b75ecb6bf137997e7d14ed3a72f3de94f6268155621c8a03b843fdd4:1 22bd8b56ba11b3971ec0571f7e1bed06a1711b8c35ab69694bd5ff24eb2b5a54:1 236ce953fd5fc572aab73df87de002439ae52156538f145255cbe112acb23010:1 241cb248f079d5994fbdd4a4718b821108df77ba872c5aade9c1731f28331de4:1 2434bcb7abf1d5def0f2f4c2d4d7f24564a88c08d972354d79a01241aa74f569:1 249c3f744e9c82a4a053df787eae427a6130335b90a88591349b7d8f38ba0c90:1 25b955358beb844e40269929fc031eca899c3f0120b45ba2069f673cabe2f8d9:1 29e2a678f000dc3f468c6e30645240a79f9c9764061e4328f54884dd63eb3fb3:1 29fc4d1230ce922a6009fd4fa1d0ab5df03ca3db7e532c2c73dcf087b01f578d:1 2b062e8c410193249406f34215b6832cc51c50a1f954b9b4560a527afb51f754:1 2bc1facd1e8af0dd23ded5c21997e219ba9e1446a00a8aa01a5b98060bd8d595:1 2c7640a70778fe4a15feb8e1839455c443ae0fee2183129abfa78b70c71bbb1c:2 2d7bcaaf3529a91c88387c7db3067e82e6d6f15afd2bba0e964ba6af7f8dbff8:1 2e6c6cdb37a65a8cf797f713e1acc01da7ffa9d50dd29f7cde0c2ceeb2f20881:1 2eccaeb7d58ef8f00099cf68ff72b7c85cdd4406a9b5f45287a0138db48e1cb3:1 2fbaaaafa87c09d5a196ec598eb1cf84d6a39e9608e489553d99f255f16e9494:1 30950c7f0e12224c71d963bb3f4e5ff5dce35d2beb7838767f6fcb25ecf50859:1 30aef622b22be089199dbd2af13bbcfcc3e8f7806d89a6750c2fdf23dda46989:1 339193b6b545099323ceb487db7fc867383bda19b274c5c67f6e9e807529ae39:1 34142175cdeb79e1105c9e8f2a4808d48bbb7c243453f443f1d31e9359e6f8ec:1 35044d82070c87e72b60a214d0326d3038b9d1da370edd80daa1777b6d393afd:1 37326e930314c11ef445de96dc6d5f04acd7791323904432d2c465d43c374dcc:1 396b5a3187468f2f6c264e77caab605ae87b7a1353bcc72e1fd6953fc8081ee7:1 3cd2bce62f5ebc336993155984cb427786a573a4ea10d86ba11ed13caa067d71:1 3d5ac19bda9af6e233a26a72b5420fa70be903ecf3db2f7b27108d6cee65cdfc:1 3dc59e62cac881e3204a552d6de85386beebbd336ed68fc5ad3403231fed0390:1 45be54d046c8bc882ab65f94824263b4e7aad854205dabc9e0bf58319fe2e930:1 482fc83e0c491c41f3a4e8ed2a635d532282664f8f3fe3e7923f61332b52628c:1 4930a138c83336b696509f2554ad10e12d50e74d5fd5f5a8c7a62f2a28198dab:1 4a50aa2a035d9f649a9d8d28dbfcbd8a5b3410f46da1e82ba3d8df2ab1f75c55:1 4a9deff2afaf641753b724c135b4525a0e171106a9b68041b621eb14a403f1bf:1 4d437f24c3cb0fde008c3d6c8e412f7c86bb557a3f7b7b6f037672ee38798136:1 4e7a63d8f9a2ec0099c79880924d4ab1ee3a67614cdaf07d61b2bee95b18104e:1 51008e8275d3f2393aad435925adafa542c3e00919ffd36fbdbe663989822b09:1 520a631cef06db99b3b42baadcd3148a733995be900cd55cd72dd5fcbb04fbcb:1 52eadd224d2ea2bd09f9de2c318d87200702b6275488e91210c93c519a68e204:1 54f18777c68667db60944fd02978665849debcc568b017f08a54e587c0f8373d:1 552e274a1f2c5c855987fe2537eb55504a33186a79ad7fedd89bd758ff6c9caa:1 56fa135298728b19c9653588b8c2bf3955672902ab2ba632df8428076fc29ba3:1 5aa54db49f155ab828e8ba25b4d19994eab51278481bff0f0c0726bb7d8a401d:1 5bb319253917c3a0b5acd830a95a585c623a1ccd24db4d422487d0115a412067:1 5c588d69427ec404e2345536c26d88bf1e5c435253954d4de2e3953be56ee8db:1 5d9192203d40f5e962259a5b492bfc314c2e271551ebffc1c2ff28c14bb30a52:1 5db8221695f53f560d3bfba33477c04b018a97254581d088b241e8e97ff9e325:1 62008d37db3e3b3a9f15880b57b755584f622a9de96c4af4ffccd1452c04dab9:1 65b1c5c6c22e7ba29da20b5fef3b6453488a1b14fb5e75d95548b8b7ee710328:1 67bf3691d7cff384f2414780b8d28df36a34adc0537af4e61b18d59381608c50:1 67c5b365cad22a1543517322d29458bf17448bf7bc686258c6244d2d562facf7:1 67f4034d9c9f21df261d5cc1e13f4cda095cfc55cb16573f2303d94f6d9bd52b:1 68933414dba17d9a29c7a70525136f9b3dd997a55cd0b1d0be1a51d40fc6ad55:1 68cb479aa4f9d925d588806709e874f5f4e1641b04af9e8a53fb4651343cb3bd:1 6914998a9b50a3e7f769e9d6d9099332bc58ee4d1bedec419cfd990f21c8eb88:1 6aae5dae87c3a28e9d803edd44d51c1bc3eaf40569ddcb7eba595e2402b2f318:1 6b7dd5b847a8de55fa21944fc4eb6c5bd1d281c0efa4e6b26bad98c548e7b509:1 6db2a7ce09c4d6f1d4a3208733ecbeed11972a02827e6dfe68d4843f0b69ecf1:1 6f7d694d48321f5bc816a97485aa088446417d99202214131f6092e590e815c5:1 70e39ca012ed122f6e9d9c3c38e335f10fd8fe1f479bc6e1d1739994a2cce561:1 747fc5365a747b32afaf808f0aed3801cab6f24f34661a25afdc16d4f54efdb4:1 75a8fc6d5dabfe5413b2e99083ed5fbf40f76ec555de1f76008f54816f787a88:1 773a62680effe7f27bc600118cd6d9388b2cef29aa596faba551ee9803e826ec:1 782e9378ebb6261d7ccf905a79384cbffb00a775c72b645f9fa0829b03ed16f9:1 7937d61ee7f8f32e822f2e64d081ced6c21b1804bf19062583dddeab68345643:1 7b14e15d92860f9e689150cab9fe4cd08ea1b92971b6d3c7facb53561f3a6ccc:1 7b86d2d3792d1951198d8b2dcbe5a577102fa03356ddf9807c0a863d10781575:1 7b8aa17bcfecea5f9e8678451fe937d5ef925059ab851484444b56c444d54d30:1 7c77bc7e2ee674837da66ed2bbbca3d6ea9fd22090cc85f172f7079dceff560a:1 7da0ac9d1020c8693a09d9538a6921083ea213381253750a39da2bc90e2ed0ff:1 7e41eb4ea8a25179ad3561614df0a4aaa1409aad428c84a107a6f5ad5e3144d7:1 7e5bcf77f39c115bb5890343eb6101cce0c373d9ab1d11dafa69ae03afd57966:2 7f4e0b188f9bf0942e9c3b0002e78e9ab76abf85bef447d294ae6535ed2c5f1a:1 837d5cf703e2cf656e577215d1ed4a490cbaeb66649437312359dbd11618f6df:1 847ee5d4e2b79cfb3b23a1ae637b0a3a159775a95a0f59b99e916a8eed5a013c:1 8577af3e3ef39bfa3453b059b19a80d0d57ebf4b15d7364dde92122646161062:1 86191bbd311ff36e1ffdb9fec513a5ef8512391e7781eada0ab347a9b7faf0f3:1 88a2836c0849ad1fc1575afd1eb6967c07023fc9e78a0d213a4ee10c57bfda5c:1 8941290e5e243a221d6c258db52cc158e82d3c03fbec19f8c3059786f21188f2:1 8dbf31ca153990653817868f8bfad25f5df12b8be33ab7eb27e0ccccb8896ad5:1 8ec0a88717df99e626b4811a7732973e3f10fec5e8e972f137108b09cc5de268:1 90e585d0e9c7c4a7c3cfb35ed42d5c754ea18b92ab30e8fefcc6d1cf50a2ab37:1 937070aa665da0b187d01d14c5abb52fb3e692baeaf9f23aa12e779370dba762:1 94102f1b8305201dd5fadb7cdf2f2965f07c8e846be7443daef58fc7e15acf05:1 941cde32f4ac1f3de9e73a341b5bd41928532e4195cdf966da222d2fd0f894e6:1 94f46a3c2796979131bcdd20f85b3eb6b49f98e64d3647250f7bda81ceac646d:1 96bb204f4ed41376dadc173a5891e3afcf7a6c3d2865d9f354e23a0d44907b66:1 98380a71728fb2765754e72129f8d23ec366f00cd45b56a11de2bcce52c40138:1 98c22e04c96ec212a8a5fa38577ef2eea1a132204f4a4ba6328c884b32cae294:1 993b1ced626e27c64bad8e9a99594ee4fd15ba204d891dfa9720eb7c5a878da5:1 99954586bfa16ddc2347bd6725d49d3304665fdfee2446e22f9f300aa76fc511:1 9a2b202142a32e4cf121a5fbb89331348b2245e3da41baae1b9d3636350486ff:1 9b815d733757da1c48b986782be4b5bb9e85243e0d9f68142c275077f6a93655:1 9d0e79a42640fee23314ce9b89e56f52bf88296ed0ca30c09625bfccbb15f3b5:1 9df8dc446ae08f3ff1ce2e82efac27e5bc5d4926d69fdaf0dad0c76e06896a44:1 9e19f4434077a5516985e30ca51a1a563196613636c62a3e1547c8158852c263:1 a05e7b6fea34fc592b497746f9d334006522b0811cf69aa171ce3c4ed227c620:1 a136ac04d26fe57b0c53f9e2b2baab8085f7a5f77715e0962b53c8ca45ceaa23:1 a40cdf4388a55c8ba57558c84c37668d337812c47e55039d8ffb0381686be36a:1 a4570b42d7b7bf2a41fceb1810ac21989b55c559ccb225b9deeb4bec13609873:1 a7d8386af38ac1264690b33cc05b03a5a2ef1794d03c5ef3746a6c4325a91171:1 a9a5d960c21165a16368036f5c1a38875512f3f8efa30effc7ecbbb733b4e8ae:1 ab89e0afe489d8f99c7df481e433254b0e217b235cb7cdbdbd3eb0c707ca7646:1 ace5f674bc81cb251b40d9e1333bc2fbfd1bd4f934efda3268c1ee686007da60:1 b3725b6a6b24ec8710d4b655fc29ebc57b3a8ecb9585ac52a280ad78e4978146:1 b3cdcf98850e873d5e8a726e8eebaf5c2801a5c318b0daff8d44e94d10bda82d:1 b3f1110d8140a1fed02cdf4db65ae3f9263a266cf353d03c8c0c44c0f800db9a:1 b99d692d41b85bd58605b34dee70611f893a282c355f5e108833578f90ee9f19:1 b9f87d2db754bc021f4d49e2b8cc0de2ea1657ed1844099013d9abd6b16940d8:1 bab3526d7575486fbb1ffb174579108bd08359f6128c5306f89d666f2b365442:1 bc1e703aabf535a32153ce081f599947127afaa1edf4437ce33a65f63920ffc3:1 bd99e7ee4da7b8a8e19ab999276a6c907e8c69dcee58ba0d0f73f6f40a598b17:1 bdc713faf289f6bf16f7238386d57ffc795b35d5c15139361c981e46cf02b3c6:1 bf1b55fd99e1949a55cfedc6ff5fc2206df66785df44ffa9422def98a965c011:1 c08eb46371fa401d75a94caccd8121fea3481ac1057d8d1703a82595a71c4240:1 c3aebd5c7ab1294416028f31bc57e8dad30a7d3403f514d480b46e33d5381f5b:1 c4ecc4ca383bb2ce40fe826c4135c9e1ccb945b340b0ae5b1cd767066ef31c55:1 c81da273f10bbe69a2032ddeea497c545b554d10ad706020803ab7fcd3da6990:1 c8a4f6a6ed3526a758e1a8e36e51b39bf1e6eb5c2aaf68635dcef73ca23d3565:1 c98509dc1a5e665a5639f44455a2284adc5f32d095bbc5ef4b9c789a35d6bd70:1 caa516f8042df92917682723245ae0b060b58954a5a3ab7a4c7814f1f3ab1da4:1 cb672fadd65f52bf65e8b230bc3c5dcece153767df3776d0def95439b3b25ef4:1 d092ab07ce313d99fdeda8baff66ccd9c88a6a1e68a29a29b0eab330587d7466:1 d19750ad93652a70d9a3072afe845621c247e6de72c88587c8a637e05772a73e:1 d1c8be84dec1ab97c802420188a03f331b52cb6b806ba352a1f487e8d68f1e3f:1 d2d007ecfbfdcdb02c0c0ddcc6f691f2c01ae8991bec46ecf9703701a08ca78c:1 d337457204ba028548a65069258482cf6b79653b64cf0453d9f0a4d3c6cce191:1 d35343db46c6ff92c1b88cbd721f0ade3a9f39e1f0d40540fbc3a9d7fd11f570:1 d3c94053ce25f5427bef1ee4981c168e19bd1ac049d972eed2d1f1235db4557a:1 d41509ac6c3b704a9983de4bea0b82e31cc680b46d25c23ae204c4029086f734:1 d676da3222525121523f44cb4960b4ddd6ce45543561a3c67af9c978566d28d6:1 d70e7042486800bbdea65e8682258bfe84efdb23240a5639d70d197da73293b0:1 d96f3d7dba9873758dbb94cbcfe4ae1f7bfebedf7d9688bbfce501057aaa7555:1 db0175e20ef45cdcde0f7096c7ca4ee1b1ab04256b6a92d0c979fd15f081d53c:1 db1db44d8b7678be7d0c609ad05dd95c9768a25cbd85f6f7a9336329ae5cb445:1 de2c89be1129e608ac7f53396b373ba1030c620cc4dae65be3037d0eca41c2a0:1 dec83c3c61ff3f3eed75f885de6a0336276c4e49d70f818ac8ec76aad034de35:1 e3d257b1a40ebdc6938db4d01dc88ee8a1719e02150b8705e6e2a8909c4d67e0:3 e4939edc0fedd86536e9eab7c9f290dd074a09388d813a545f57cb7238cca2c4:1 e6849c3c935cba52816bdca7da04bfa8ecb9058ca4a6a5852b574320a869f83b:1 e9f5409df42546f4d4f1a97e1e61c01a482ff77614a7e38935b6f4dbdc037e80:1 eb121ad81f9029ee02f73c1cce551500ffdcf28982690b06fc4ce5c5c5d132b0:1 eb16f4774d71154b30534c41322976d7d618e554efe64b7f9fce638084928906:1 ec9f9b488eba2850003696b1d99fa799c0dc0f3be093ff8344f4c07705913671:1 efbee110c0dba08a271197ced6de91322d5553a9ca96c23514898f3bb18d7b32:1 efe7d827e8c83547fd553dffa6683ff697316a72695a0b43b3bcd0faf0578c00:1 f07460cab7fe20c10b4eba2885496dc35ae0068703cd905aed36ce508d4be7e8:1 f33c97114de3b6cb1775aa4fc2c969d4b328a2eccd58b94106a26dcdb3725d9b:1 f3d191863988b7f8b935154c65ebb30bed30ee9e8d86262594bfad036af2963d:1 f3d6a9dd2daa58af6ed5b3bb3e422c5843f8d40e2f0c033412f088a077dd1c72:1 f3e4c9a124a38b62a16a7ab7562b78921317c248b17aeb4f1a1cf72a7fbe8ca3:1 f3e83fa8948fbefd26e3807d8cc0a7a64087afad4cf43a3b7b7aff7e8ab93e80:1 f5a39fd5acd513ad4cbffbed5f48bd84fbac6670223e636195d93c40b1d13350:1 f63be3792cd8b54da3950c4129ab98e6287f14e5ab5d86d1b44451384dc5eb11:1 f781e6acc4301514a059d0bded8b77ae6837e5f9a3013c28b1d862ea1aa7a749:1 f8b79e1f60595eb6d1573137345e32854446241f296d4d8c48ceac6f6314bba8:1 f8ba0159ab8be23c0d95f75bbedf743181f7acdc22f308ec44c8352ccee3bd0f:1 f8ebfab42b748770c9a2404d595cfe33329749a27d7825a81eaed7aba017a1b6:1 f918b2f50f3c84da38d73d590d063e924e0eff70648a830294fda592d1922329:1 fa6c2b96722ecfb17cb52197866e6ab13a3d278e0581cea50e5f603640fa0178:1 fa85b1cfe1d505c8190a60121e0a901b23a3ad9383f508c1fa908f4c1ae612f3:1 faa5c07df957790362c20e764f4b5feedd77ed885f23baabaf9f007367835bbf:1 fbbf60614f9e7a3705170ef5a8b723d71ea75a81cf2b75e90c07a5464dab6bd4:1 fbd26e9881dfe8217b6e2132955e73783877c281aa2f740a9b94cac26513b858:1 fe85fe83f33d16125cc97e331942d6cadfbf86932f8267d600c04a1e3e6daea8:1 ff99b901b26fb972d5eabafd2f089daca6391c715029ea87a374298712cadb32:1 ffbcc586a0bd02eec67bd3cf372741d90fe178a21486370624c1b61e1052d274:1 ffeb86a9a82404cfff82e6f7c918293762d12c9be5852f23b385484db0a33c32:1",
    ),
    (
        "tests/test_guard_secret_print.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "03e06bc89e1288f3685c32ddddb514df34947a28ee6bf30843901463f8190b81:2 d3c94053ce25f5427bef1ee4981c168e19bd1ac049d972eed2d1f1235db4557a:1 efe7d827e8c83547fd553dffa6683ff697316a72695a0b43b3bcd0faf0578c00:2",
    ),
    (
        "tests/test_headless_claude_background_controls.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "9cdcb9c24e6f5e8885582202ec6ae1337436ff6056fee7abbaaafa052f84b378:1 fa2f94609fb8d76fad044f23291475292247be2320162d3bc5114a604b8b5bf3:1",
    ),
    (
        "tests/test_health_20k_runner.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "9a81dd84ff10febd15f2cc3e81e0ff5b9819984216cab9555dd3c88534dd8309:4",
    ),
    (
        "tests/test_human_eval_tracker.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:4",
    ),
    (
        "tests/test_kimi_finalize_tmp_reap.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "ebf79b85a024c41e0003dec7b49f8526af40d5b7f28f9207e8fab2e5359b4e15:1",
    ),
    (
        "tests/test_launch_reenrich_target_detection.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "2a8eacd9f7602ee91d4080eb6ddb76331b42024f8d02d9d6051a61ede8636699:2 9b13679fdc20dac81cad2fa1c9d1d6686e3e48c73fa5fbf3caf53067921aefc4:2 d2216cedd0c3908c5b745cbfc18040b8d35f8f31fe9b8ee5ffc8550c9ad40944:1 e81b1a27619f5f179bda118c9e98dfd527ffaccd2d8c6ea258a93e12fe116b48:1",
    ),
    (
        "tests/test_launcher_contract.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8f8d38db59dfd4600717e232140df8cd54c47cd40b213eacc26902a07d76605f:1",
    ),
    (
        "tests/test_layerb_judge_bridge.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "98517c31d0810ffa700c8c63aab70d05931f2880dbf9a83b1279790a1a6975a4:1 98707c151255427d3da351e267fbaae13978bcd6b93b81969b3d2f259087dd2d:1",
    ),
    (
        "tests/test_lexicon_runner_pr1.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "21131bdae5866c3f5b5b2da0cf4f1d4f98b62b1839459be094bfaf784de00ded:1 ea6c0a70ff1a361bbad41f3659f4948e96474196633eb7112344bc3412862b85:1",
    ),
    (
        "tests/test_lexicon_runner_pr4_finalize.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "tests/test_lexicon_timeouts.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "288cdb48e98ff6bc923b23bb7043f5331bc60d2dd7e44a09ae8947ea5942d37d:2 76698d6fa066a054e3d1ae0b5dc8932e327e0a51fa07c6f9f4dbfe5e7793fb3e:1",
    ),
    (
        "tests/test_lint_prompts.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "tests/test_phase3_cycle007_evidence_validator.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "99caa930c034ccf179bf8921f59e34e2793c80f8feeb3a31e953978a13014d01:1",
    ),
    (
        "tests/test_phase3_cycle007_labeling_guardian.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2219963a5a1e72c8db05c5b74e488322d39619ce816c3876439418c1c4901d25:1",
    ),
    (
        "tests/test_pipeline_state.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "080f4e4e6948695d57d80b8ed151897afb8d2885349ecb1d0641610b7ad69f21:1",
    ),
    (
        "tests/test_pre_push_hook.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "4118c7f62788dcf00928cfdd6540c9f3bacf50f17b117ebfb636e15ee08acfdd:1 4bd5dff8fd8c46f22dee404042901162205d543663ee20dc140bd21e7ca2ba90:1 7fe43be6e67da7b2c55cc16b763bd1901da0ef0a6689320d7be8b46507d912e5:1 8d2a041a50bd79185205720a3976f420bebc8b78fa2481a6fde177b4303e53f4:1 c1f00e19c0ac4f9e09ad5a5add680b30ee856b482f9b8ccd6a9fdfa2fadd33e5:1 fc3b22a14f3a60fffc28ab16cd09783229ba8b292f805aa36264d764a6e199e8:1",
    ),
    (
        "tests/test_rag_tools_timeouts.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "99c16842a1ada49a7da8f5f2f9e34c5159a5bde9669dd55abe86bef184b0b891:1",
    ),
    (
        "tests/test_repo_wide_marker_invariant.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:1",
    ),
    (
        "tests/test_retention_engine.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "02391888ccb6f49274726c2345c74f703162a1c2a33def38c43313888dd1eaca:1 09e53f1c85f3ee93a894559a0f90da776510d4a5e09b4d04f874a590424af0ee:1 37b3efbc4461de4050cd18e8044e73b233a332d98cff43bdcf6cfe21c03dd5b6:1 8ca9e1bbb1df8390d8e031968f578d6d8cf3c234334193983ecaa04f1e7ab0b8:1 f3424630a7e77b67559e0aca5a05994d3735e99fcd44e4df6e302d0dc9a8be44:1",
    ),
    (
        "tests/test_review_closeout_cli.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "6814ca425b869549a4a4589864ecb4b3fd38f916d1f75550dc363d03c74d8b6a:1",
    ),
    (
        "tests/test_review_isolation.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "151077e592d8a0c901846d8bb8cdb26f79afa57e140351e4847a3975026eb718:1 2804b88e531d3963124e6d940fd4d6d118aa41072b589f195b55683089675f9e:1 75553f637ecd6c2b69860a716f120536a4e438cf8dcbf7f6e9f94f0d8ced7237:1 825d9ee66199b191ece019122bdd17655bf611f8ca84d23b1a691375762254fa:1 9c08178ee82592f38eaa5d9d56bee7cd340eda5f64fdf2f6dc0279788e01f927:1 a697175d9636ef5cb48121eacd85178437c31cf37d4a49830e6095d64fafdb0c:1 d809bad843a66853377c4c5b3a6cb6d74e1028fdd41ed71119ace869827d0079:1 ecc2299b7cca74c2a646cc42d13dfac749c8ece3f11e64d1503c97419dae42c7:1 f149dac9c9a9a6e28a0a8b082793f13c823056e7593f58242af3ac1e80ff1503:1 f898c462a1fe088676d02fefb50894986d30f03739fd192f94dd9367cad016c5:1",
    ),
    (
        "tests/test_rules_core_loading.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "89990ce05012a058e05a981ffb7d53071528c09acf7aeb4032496ed47e5d2a69:1 9c762b6eeabe184fdbe74d4964867a69f17229124ea5adb8e63aafabde8219fb:1 f0370c1f760ee091faaac3e1be21448672df9e5e16fdd701a6eb3dab34e61efc:1",
    ),
    (
        "tests/test_runtime_scratch_isolation.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8f33991a5dab5bf61d03335befdb4903ecf72f452d1ddae066cd13ddd7b0d688:1",
    ),
    (
        "tests/test_scratch.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "587d112cafb16192830545861ca15756334364eb0cbff00a4c8cb8773cb3c475:1",
    ),
    (
        "tests/test_session_canary_hydrate.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "b49c9c7b24cf8969560a94fedb9d033ee224d7833bf874f5410b1bd9de381cca:1",
    ),
    (
        "tests/test_session_record.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "3b5c8b3f44ec288fc69587471482859ca86cf1069760a1e56c99663f6455144a:1 ec4e60c198f7c47d823ea26bab407b49ce285427a98b4a80de925ab0bf77861b:1 f123cdc0dfe2fe4920d3d01d2298de723aa657b166e4b0bbe9bfe553c5c9a65b:1",
    ),
    (
        "tests/test_shared_hydration.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "cbcbce9aa38263b1df2a380b5363f899ada794c26349000b9e6c8bdc79ea465a:1",
    ),
    (
        "tests/test_sibling_git.py",
        "Existing test literal; migration outside this bounded packet (#9702). Expanded checks retain exact legacy fingerprints (#9702).",
        "339bb84cb06fef129b0d738f951c82665c504d9856738988684a77f9b2a28dfa:1 9a9adb68d6e2e685b44d1f342d005464fe764ac60f01f5d7704fe99b95d38eb2:1 ce244f8fd681fd487d2bf2e8704fba53d31eac7ffe34542b56b478b5a74e8a55:1 f008e1d096a56887753a70f7436bf849afa26cd61af7d83daa223420345c2543:1",
    ),
    (
        "tests/test_socket_guard.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "1b0417ba7d4fd54591d781fb18620603db45f8cf4533f20e08121291ae4e30e4:1 af2fc75a68d53ede10915d3656e4a3a9f164f2317e938d8695f1510af9f5af70:1",
    ),
    (
        "tests/test_source_ingest_entrypoints.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "59386c60803d2e0788292d105f2d43d8232ed0d493758e54f0c0ed597fb57f15:1",
    ),
    (
        "tests/test_source_inventory_review_decisions.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "fe54ed63ad57a104dd80a0143609b55c18347047a1c3a0b1282f925120662b09:1",
    ),
    (
        "tests/test_sparse_collection_guard.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "b90a76b36e032fb7eaeca121ad693795cc2adb7d0b0ddc79e12f96a2b7c0bf70:1",
    ),
    (
        "tests/test_status_cache.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "3cfef27c84a34dd2ecaa7d91e3e2d4e209073a6640d9628b05a969b854cc86d0:4",
    ),
    (
        "tests/test_storage_classification_table.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a7a759cbbd9c87a01c8319ac5fd23aeb48ec0726fd02938c146decef17d26497:1",
    ),
    (
        "tests/test_storage_resolver.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "e0e3e8c0d93b60603885ef0d35cc84f49eb744bbd706988abc36a5b6db065ce6:1",
    ),
    (
        "tests/test_v4_sources_transport_credential_namespace.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "ed3fdee7c888f4389c4222fd891021d840fc087836ee32003ae88cc065cea124:1",
    ),
    (
        "tests/test_v7_build_reviewer_assert.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "2ca2890f45d3d5734f55b9b8ffea1af72b8a25bb279b1944834f472643a14276:1",
    ),
    (
        "tests/test_verbatim_overlap_gate.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "2492fcb13d0465f796c21f63cea148c5bfa243e2be9e51b17d97daa4d910e044:1",
    ),
    (
        "tests/test_verify_review.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "fb04258d59aaa3da8b6cc76a5706d17904554d861e90e8560483361ced618fe8:1",
    ),
    (
        "tests/test_video_discovery.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "a4b24ada95971b11223fe6969f2f981509c635e03415ebcc849f4f44a5a69937:4",
    ),
    (
        "tests/test_work_dashboard_private_integration.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "549434b400a8d842ea86f04481428a08beab8704f734cf6f7d7e94668e77a774:1",
    ),
    (
        "tests/test_yaml_validation.py",
        "Existing literal or temp producer exposed by expanded lint; migration tracked in #9702.",
        "8a29d4629d3631c0a1b6c19f95f1bf7d58f8e571c8928d419d94cdcc5b3d2b73:3",
    ),
)


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    message: str


def has_literal_temp_path(value: str) -> bool:
    """Detect temp roots at path boundaries, excluding the managed root subtree."""
    for match in LITERAL_TEMP.finditer(value):
        literal = match.group()
        path = posixpath.normpath(literal)
        if not (
            (literal == MANAGED_ROOT or literal.startswith(MANAGED_ROOT + "/"))
            and (path == MANAGED_ROOT or path.startswith(MANAGED_ROOT + "/"))
        ):
            return True
    return False


def qualified_name(node: ast.AST, aliases: dict[str, str]) -> str:
    """Resolve a dotted name through explicit import aliases."""
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return qualified_name(node.value, aliases) + "." + node.attr
    return ""


def is_scratch_expression(node: ast.AST, aliases: dict[str, str]) -> bool:
    """Accept explicit scratch sources and relative Path operations only."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        path = posixpath.normpath(node.value)
        return (node.value == MANAGED_ROOT or node.value.startswith(MANAGED_ROOT + "/")) and (
            path == MANAGED_ROOT or path.startswith(MANAGED_ROOT + "/")
        )
    if isinstance(node, ast.Name):
        return node.id in SCRATCH_NAMES
    if isinstance(node, ast.Subscript):
        return (
            qualified_name(node.value, aliases) == "os.environ"
            and isinstance(node.slice, ast.Constant)
            and node.slice.value in ENV_NAMES
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return (
            is_scratch_expression(node.left, aliases)
            and isinstance(node.right, ast.Constant)
            and isinstance(node.right.value, str)
            and not node.right.value.startswith("/")
            and ".." not in node.right.value.split("/")
        )
    if not isinstance(node, ast.Call):
        return False
    name = qualified_name(node.func, aliases)
    if name.rsplit(".", 1)[-1] in SCRATCH_HELPERS:
        return not node.args and not node.keywords
    if name in {"os.getenv", "os.environ.get"}:
        return (
            len(node.args) == 2
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in ENV_NAMES
            and is_scratch_expression(node.args[1], aliases)
            and not node.keywords
        )
    if name in {"Path", "pathlib.Path"}:
        return len(node.args) == 1 and not node.keywords and is_scratch_expression(node.args[0], aliases)
    return name in {"tmp_path_factory.mktemp", "tmp_path_factory.getbasetemp"} and all(
        not has_literal_temp_path(n.value)
        for n in ast.walk(node)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )


def scan_python(source: str, path: str) -> list[Finding]:
    """Find tempfile calls without an explicit managed directory, including aliases."""
    tree = ast.parse(source, filename=path)
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name] = item.name
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for item in node.names:
                if node.module == "tempfile" and item.name == "*":
                    aliases.update({name: "tempfile." + name for name in TEMP_CALLS})
                else:
                    aliases[item.asname or item.name] = node.module + "." + item.name
    findings = []
    source_lines = None
    temp_names = {"tempfile." + call for call in TEMP_CALLS}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            value = node.value.decode("utf-8", errors="replace") if isinstance(node.value, bytes) else node.value
            if isinstance(value, str) and has_literal_temp_path(value):
                findings.append(Finding(path, node.lineno, "literal system temp path"))
        if not isinstance(node, ast.Call):
            continue
        name = qualified_name(node.func, aliases)
        if name not in temp_names:
            continue
        directory = next((k.value for k in node.keywords if k.arg == "dir"), None)
        if directory is None or not is_scratch_expression(directory, aliases):
            # Source text is only fingerprinted locally; it is never printed by the CLI.
            if source_lines is None:
                source_lines = source.encode("utf-8").splitlines(keepends=True)
            segment = source_lines[node.lineno - 1 : node.end_lineno]
            segment[-1] = segment[-1][: node.end_col_offset]
            segment[0] = segment[0][node.col_offset :]
            text = b"".join(segment).decode("utf-8")
            findings.append(Finding(path, node.lineno, "tempfile-call: requires approved dir=: " + text.strip()))
    return sorted(set(findings))


def shell_substitutions(source: str) -> tuple[str, list[tuple[int, str]]]:
    """Extract executable substitutions before shlex removes surrounding quotes."""
    code = list(source)
    substitutions = []
    quote = ""
    index = 0
    while index < len(source):
        char = source[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if char in "'\"":
            if not quote:
                quote = char
            elif quote == char:
                quote = ""
            index += 1
            continue
        if char == "#" and not quote and (index == 0 or source[index - 1].isspace()):
            end = source.find("\n", index)
            index = len(source) if end < 0 else end
            continue
        backtick = char == "`"
        if quote == "'" or not (backtick or source.startswith("$(", index)):
            index += 1
            continue
        start = index + (1 if backtick else 2)
        end = start
        depth = 1
        inner_quote = ""
        while end < len(source):
            current = source[end]
            if current == "\\" and inner_quote != "'":
                end += 2
                continue
            if backtick and current == "`":
                break
            if current in "'\"":
                if not inner_quote:
                    inner_quote = current
                elif inner_quote == current:
                    inner_quote = ""
            elif not backtick and not inner_quote:
                if current == "(":
                    depth += 1
                elif current == ")":
                    depth -= 1
                    if not depth:
                        break
            end += 1
        substitutions.append((source.count("\n", 0, start), source[start:end]))
        for position in range(index, min(end + 1, len(source))):
            if code[position] != "\n":
                code[position] = " "
        index = end + 1
    return "".join(code), substitutions


def shell_heredocs(line: str) -> list[tuple[str, bool, bool]]:
    """Find heredoc operators outside quotes/comments, without parsing body data."""
    lexer = shlex.shlex(line, posix=False, punctuation_chars="<>")
    lexer.whitespace_split = True
    tokens = []
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    results = []
    for index, token in enumerate(tokens[:-1]):
        if token != "<<":
            continue
        word = tokens[index + 1]
        strip_tabs = word.startswith("-")
        if strip_tabs:
            word = word[1:] or (tokens[index + 2] if index + 2 < len(tokens) else "")
        quoted = any(char in word for char in "'\"\\")
        try:
            delimiter = shlex.split(word)
        except ValueError:
            continue
        if delimiter:
            results.append((delimiter[0], strip_tabs, quoted))
    return results


def scan_shell(source: str, path: str) -> list[Finding]:
    """Find mktemp commands; tolerate quoted heredoc bodies and incomplete quotes.

    Literal paths are also scanned as raw lines by scan_lines. Heredoc data is
    kept out of shlex, which is a token lexer rather than a shell parser.
    Unquoted heredocs still execute command substitutions, so scan those too.
    """
    lines = re.split(r"\r\n|\r|\n", source)
    code = []
    heredocs = []
    for line in lines:
        if heredocs:
            delimiter, strip_tabs, quoted = heredocs[0]
            if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                heredocs.pop(0)
                code.append("")
            elif quoted:
                code.append("")
            else:
                substitutions = re.findall(r"\$\((.*?)\)|`([^`]*)`", line)
                code.append("; ".join(a or b for a, b in substitutions))
            continue
        code.append(line)
        heredocs.extend(shell_heredocs(line))
    executable, substitutions = shell_substitutions("\n".join(code))
    stream = io.StringIO(executable)
    lexer = shlex.shlex(stream, posix=True, punctuation_chars="();<>|&\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    tokens = []
    newlines = [i for i, char in enumerate(executable) if char == "\n"]
    try:
        while (token := lexer.get_token()) is not None:
            position = max(0, stream.tell() - len(lexer.pushback) - 1)
            number = bisect_right(newlines, position - 1) + 1 - token.count("\n")
            tokens.append((token, max(1, number)))
    except ValueError:
        # A malformed token must not erase previously scanned commands or
        # turn the rest of the source into an implicit exemption.
        start = max(0, lexer.lineno - 1)
        for number, line in enumerate(code[start:], start + 1):
            tokens.extend((word, number) for word in re.findall(r"[^\s;()]+|[;()]", line))
    findings = [
        Finding(f.path, f.line + offset, f.message)
        for offset, command in substitutions
        for f in scan_shell(command, path)
    ]
    command_start = True
    for index, (token, number) in enumerate(tokens):
        if token and all(c in "();<>|&{}\n" for c in token):
            command_start = True
            continue
        if command_start and (
            token in {"command", "exec", "env", "if", "then", "elif", "else", "do", "!"}
            or re.match(r"[A-Za-z_]\w*=", token)
        ):
            continue
        is_command = command_start
        command_start = False
        if not is_command or token not in {"mktemp", "/usr/bin/mktemp", "/bin/mktemp"}:
            continue
        arguments = []
        for argument, _ in tokens[index + 1 :]:
            if argument and all(c in "();<>|&\n" for c in argument):
                break
            arguments.append(argument)
        managed = False
        for argument in arguments:
            value = argument.removeprefix("--tmpdir=")
            if any(
                value == "$" + name
                or value.startswith("$" + name + "/")
                or value == "${" + name + "}"
                or value.startswith("${" + name + "}/")
                for name in ENV_NAMES
            ) and ".." not in value.split("/"):
                managed = True
        if not managed:
            # Include the complete invocation in its counted fingerprint.
            findings.append(Finding(path, number, "mktemp-call: " + " ".join([token, *arguments])))
    return sorted(set(findings))


def scan_lines(repo_root: Path) -> list[tuple[str, int, str]]:
    """Collect raw/decoded literals and producer calls under the same exact baseline."""
    rows = []
    for directory in ("scripts", "tests"):
        for path in sorted((repo_root / directory).rglob("*")):
            if path.is_symlink() or not path.is_file() or path.suffix not in {".py", ".sh", ".bash"}:
                continue
            relative = path.relative_to(repo_root).as_posix()
            source = path.read_text(encoding="utf-8")
            lines = re.split(r"\r\n|\r|\n", source)
            literal_numbers = {n for n, line in enumerate(lines, 1) if has_literal_temp_path(line)}
            findings = scan_python(source, relative) if path.suffix == ".py" else scan_shell(source, relative)
            for finding in findings:
                if finding.message == "literal system temp path":
                    literal_numbers.add(finding.line)
                else:
                    rows.append((relative, finding.line, finding.message))
            rows.extend((relative, n, lines[n - 1].strip()) for n in sorted(literal_numbers))
    return sorted(rows)


def line_digest(line: str) -> str:
    """Identify exact stripped source text without emitting private path literals."""
    return hashlib.sha256(line.encode()).hexdigest()


def unmatched_rows(rows: list[tuple[str, int, str]]) -> list[tuple[str, int, str]]:
    """Find unmatched or repeated literals; allowlist entries carry a stated reason."""
    allowances = {}
    for path, reason, encoded in ALLOWLIST:
        if not reason:
            raise ValueError("allowlist reason required")
        for entry in encoded.split():
            digest, count = entry.split(":")
            allowances[path, digest] = int(count)
    used: Counter[tuple[str, str]] = Counter()
    findings = []
    for path, number, line in rows:
        key = path, line_digest(line)
        used[key] += 1
        if used[key] > allowances.get(key, 0):
            findings.append((path, number, line))
    return findings


def find_literal_tmp_paths(repo_root: Path = REPO_ROOT) -> list[tuple[str, int]]:
    """Find new literals and unmanaged calls outside the counted legacy baseline."""
    return [(path, number) for path, number, _ in unmatched_rows(scan_lines(repo_root))]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Flag literal system-temp paths and unmanaged tempfile/mktemp calls outside the counted allowlist.\nUse before review; worker scratch belongs under the managed TMPDIR lease.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.hygiene.lint_tmp_paths\n  .venv/bin/python -m scripts.hygiene.lint_tmp_paths --repo .\nOutputs: source locations, counted fingerprints and remediation; no writes or literal path contents.\nExit codes: 0 clean; 1 findings; 2 invalid arguments or source read/parse error.\nRelated: #8755; workflow.md; scripts.hygiene.lint_raw_rm_rf.",
    )
    parser.add_argument(
        "--repo", type=Path, default=REPO_ROOT, help="Repository to scan (default this checkout; example .)."
    )
    args = parser.parse_args(argv)
    try:
        rows = scan_lines(args.repo)
    except (OSError, SyntaxError, UnicodeError) as exc:
        location = Path(exc.filename).name if getattr(exc, "filename", None) else "source"
        print(f"{location}: cannot read or parse source", file=sys.stderr)
        return 2
    findings = unmatched_rows(rows)
    if findings:
        counts = Counter((path, line_digest(line)) for path, _, line in rows)
        for path, number, line in findings:
            digest = line_digest(line)
            print(
                f"{path}:{number}: literal system temp path or unmanaged temp producer; "
                f"counted fingerprint={digest}:{counts[path, digest]}"
            )
        print(
            'Fix producers: use "$TMPDIR/..." in shell or '
            "tempfile.TemporaryDirectory()/NamedTemporaryFile() in Python with explicit dir= from the managed lease. "
            "For a fixture, path detector, or deferred legacy use, add/update ALLOWLIST in "
            "scripts/hygiene/lint_tmp_paths.py: (repository-relative path, specific reason "
            "citing a follow-up issue such as #9702, counted fingerprint shown above). "
            "Merge the fingerprint into the file's existing entry; the number is the maximum "
            "allowed count of that exact stripped line or complete producer call, never a whole-file exemption."
        )
    print(f"literal_tmp_findings={len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
