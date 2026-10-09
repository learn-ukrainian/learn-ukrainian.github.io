"""Reject new literal system-temp paths in scripts and tests (#8755)."""

from __future__ import annotations

import argparse
import hashlib
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LITERAL_TEMP = re.compile(r"(?<![\w./~])/(?:private/)?tmp/")
# Content fingerprints and maximum occurrence counts, never whole-file exemptions.
# Legacy entries are residuals, not evidence that their producers are safe.
# Remote job hosts have their own exit/signal traps and no local TMPDIR lease.
ALLOWLIST: tuple[tuple[str, str, str], ...] = (
    (
        "scripts/agent_runtime/adapters/_template.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "2d478c815c365293b10ec511e722c6a22f7736d8cc6be2b3985b1a24ba65e77a:1",
    ),
    (
        "scripts/agent_runtime/adapters/agy.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "379b0e61e2c2edde93dea6849b152d61faf80670f394b5716d8f0838a4e09282:1",
    ),
    (
        "scripts/agent_runtime/probe_fallback.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "db01cca994b6ba71b665bd75596a2491438cef55fa6da3bba4b170f269095bc5:1",
    ),
    (
        "scripts/agent_runtime/runner.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "157c5504e246d91fc39c7a97000388fbb49ded2a1e940ab30d4a92310a851018:1 27e2a870d20bcd60a938424c008e9548500d4fdf66554af3ef7e89d14db9e54e:1 5626cf9c36f6c39aa27b49c3c3a28c37bd827034ba92e47f0e39bb9f8b0cf4d9:1",
    ),
    (
        "scripts/ai_agent_bridge/_job_host_forward.py",
        "Remote context; existing exit/signal cleanup traps own these files.",
        "66f0b828ce73cfa521a936ddc20086f876b0339568006cb5c280cad2c7d909df:1 bd9d67583ba97d091f3b3ae74e469afcda27b7119795018bc4f0b456c76a8d6d:1",
    ),
    (
        "scripts/atlas/measure_fill_enrich_divergence.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "938bc3e20fb5588f9c28647e414f4c9e9be0e93fa156e26e4a9b0f7e8a845031:1",
    ),
    (
        "scripts/audit/check_teacher_deck.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "bb84f6a9a5b2631e60e5c1fadc95095e7fc757834e84a003427c5f52d4ca91fd:1",
    ),
    (
        "scripts/audit/content_surface_gates.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "d415891a4b3ba96f81f5beecb5647595a9ed895a909431274fab123231470c33:1",
    ),
    (
        "scripts/audit/llm_qg_canaries.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "a939a6675fa5496c893bda2351817d67ad44c4c5e604bd17a54819691882de17:1",
    ),
    (
        "scripts/audit/measure_russicism_recall.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "547197605237a25fb85383eade35b889f7201271e397345306bf205f832f083f:1 61684fe365d1dc2985819bb098dce28fc2a4f354be970581ae1ed86ae51b615d:1",
    ),
    (
        "scripts/audit/sum11_sovietization_scan.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "8e756caf7dc8d194a6469f8a6ddc616f8842bb1c4a045a283175af69c1e2ef17:1",
    ),
    (
        "scripts/benchmarks/generate_synthetic_atlas.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "885534990de496ee26901de2db9459b6fc33f52def6afbef7e51611bad07cad4:1",
    ),
    (
        "scripts/build/fresh/cli.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "eae1df22874edeea214c15b4d2b3076b4107b01f0058e4bf22925d9104b934f5:1",
    ),
    (
        "scripts/build/generate_lesson_schema.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "2be206aec2189d58644ea43acb0569de5669cdbabf004d8964ff27d50160aa26:1",
    ),
    (
        "scripts/build/v7_build.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "708ff4eba09689b1d580a868b6afbda31a48f51fa0ab4f7d49373936c1a9aa45:1",
    ),
    (
        "scripts/curriculum/arc/generate_arc.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "031559c9efbea89f04d62485eee39ce666a433dbc843e6bdd84584c61105d1eb:1",
    ),
    (
        "scripts/curriculum/arc/generate_decisions.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "4186984cbd5c5a1c34a5eb0b9d9adf286883d0403855214161966ae7ecba21fb:1",
    ),
    (
        "scripts/curriculum/evidence/sense_cli.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#9702).",
        "463896cf52010bb03278ce5931e7bc372678af953d9f2d42def060aed8fd0233:1",
    ),
    (
        "scripts/deploy/vendor_atlas_tree.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "683bc12f9222df18c0caf3302ebeff8f35778ff07374307eceedf5dad19e291a:1",
    ),
    (
        "scripts/fleet_comms/cli.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "5caaa57aef52cbd95255244af892939f3ab92dad4e07eca0bc94a5584c4f8a17:1",
    ),
    (
        "scripts/ingest/build_a1_closed_class.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "e249bd0b8c9ceda07c8ed13b1ddf49247235038b2773a31a90afc68bd9c4a815:1",
    ),
    (
        "scripts/ingest/esum_abbyy_parser.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "6543462d80bc52af22ed2c7340f51bae15a7215c51dddc1f775065b3eae2b078:1 9bf9f282d8ca365bfca7daf6d02e19dcdb21cf871fbae3e4ffbd8d2760eeef50:1",
    ),
    (
        "scripts/ingest/pohribnyi_pronunciation_ingest.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "487da5ed3028eb10825fdd6f740b5e69d7d6518985c947aaf1afff72d657f8b5:1",
    ),
    (
        "scripts/ingest/pravopys_2019_ingest.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "2a69975d0abad50dafbea682027ff86a697713e62d6cd726e05eae1d5d45e591:1 8ee8cf52f49ea79206622a855311c022d2359e5a1c70dbace5d14219120732d5:1",
    ),
    (
        "scripts/lexicon/admit_textbook_book_glossary.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "46e1d19fe80db38e675e33b0a3bf5d811c3b9969d38ee32bc2ba286621eaa0e8:1",
    ),
    (
        "scripts/lexicon/apply_anchor_worksheet.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "f74b23c4e494751935f713cdbc649a527ce14b2f041801aeececa75529ef2430:1",
    ),
    (
        "scripts/lexicon/curriculum_atlas_intake.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "9f8c849f6397c57001976e5f13b13a4a2b2fd84c86e94b9d7532d15692114bcf:1 e9c2b41d5f26e6d8bf4102ed118299a0e9d80b5f5ba5172b557dffa3ed66c7b1:1",
    ),
    (
        "scripts/lexicon/extract_book_headword_inventory.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "bcf8650e90181f4b0c7d63ca7dfa8830243e755ce3c216e5da11e243e20fd603:1",
    ),
    (
        "scripts/lexicon/extract_textbook_chunk_headword_inventory.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "5a729a3ec5062cb6e6a9156bbe64b817b12c4d834310d949cffa39a5af94cf26:1",
    ),
    (
        "scripts/lexicon/generate_vesum_form_shards.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "d6a22b7661417f1311f461c66c47d149862e8a7b3aba5eb78cfc796040bf6bef:1",
    ),
    (
        "scripts/lexicon/obvious_noise_classifier.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "4bbef4334498b18af7c08162e18350575dbcc59224a6ef62e4d658bb4883726c:1",
    ),
    (
        "scripts/lexicon/ohoiko_atlas_intake.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "6259b63f6334678937c60097eca3bd376e5a532b96113507d06e5a59ed647064:1 ce32a4b965f82d15d41fe17b4f260582330699f220c1bf15cf7422377027c54f:1",
    ),
    (
        "scripts/lexicon/runner/generate_pr1_fixture.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "9b28f3356b6134a0fc4d29b60f56af56018e770880e1f0fd27c5dde1f380716e:1 c7bd115fed859bcca389d8a75dc6fc2b54f67b487b6d3636b87022fa433a08d5:1 f011ac1de68497952e5d0058678691e02e870566db58c15a68572d1802bcd668:1",
    ),
    (
        "scripts/lexicon/teacher_deck.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "051ace0daa3e81b7d63750ad007e107f06d953587576cf0a06efd1c25c5eea9f:1 6d136162d8c8fae3a4570fe3816b6c36e711802089e2d3471351ac43ade309ca:1 a8190a50c68b9d999578fb04aca3d6d662d8e50b888e10b6a2f4a0970d30ffd1:1 e673d1f726041628aab49907d4fd2923557df950f68059b996b71a202383d101:1",
    ),
    (
        "scripts/lexicon/thin_page_report.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "15b74063857626b6999f5c31494e0c58d053773ed30c039d615276a99869f109:1 47665105f277df7bf89515cf27d28719e03ab749bbc8495d78f2a27ba0dc921a:1 90ceaa68e89230e057ee91ba763cb83cb34fd94808ab4b22e325d8ebf0ad6978:1",
    ),
    (
        "scripts/maintenance/claude_session_scratch.py",
        "Existing temp inventory/cleanup tooling; migration outside this packet.",
        "7f2d2173e4933e843a43a0d57cbf3a2ee3933a11be752269752428cc02552b1d:1 c649da8e164c7a8b68f692304b79d5ac74bcc3db2258511744721e904522d49d:1",
    ),
    (
        "scripts/orchestration/job_host_exec.py",
        "Remote context; existing exit/signal cleanup traps own these files.",
        "27aa61ac8f66a6b34cfed0dd8cf8e12e93aeb31cdea4813f6f09c6062576c8fa:1",
    ),
    (
        "scripts/orchestration/tmp_leak_sweep.py",
        "Existing temp inventory/cleanup tooling; migration outside this packet.",
        "599560e7b81b3cf50ff1dd25e273f5e6bb4350f5ee283a230971326dc28d442e:1 f18c6c9fec60b901e4149456bdaebeeb7651baeee96f8df7b177c198ef96e839:1",
    ),
    (
        "scripts/practice/extract_textbook_error_corrections.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "46b80f25e3ef598a7706683af7a2bf7c361af050f0b794f18f69533fa3e669c4:1",
    ),
    (
        "scripts/practice/thin_mode_source_inventory.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "40179d544690d5a1ff061c882848d9363c86508095674e063e00ee7197b439c6:1",
    ),
    (
        "scripts/projects/open_model_data/build_decolonization_cases.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "9c8f7fdc58ed64143a902d9b9f64aac9cc160b58ddd32f760994e7702538b88f:1",
    ),
    (
        "scripts/projects/open_model_data/build_grammar_component_8342.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "43cafe21f889387aaea06226e5a7146adf83e7be30fd1a80d88cd5bf56f3ae65:1",
    ),
    (
        "scripts/projects/open_model_data/package_unified_dataset.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "487116ece65c02a87594e950040ad7f02bf6bb00ffd1ac3c9b1aa5b58073d22c:1 c5104e9eeac83dd9938de462dd05c879fa70c18ea22d7ab8da4f375afa3c99d8:1",
    ),
    (
        "scripts/projects/open_model_data/upload_to_huggingface.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "35f512e89d45d97b853c3a99363dac434eab977a7881748828c5dd3e741386f0:1",
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
        "Legacy persistent cache producer; follow-up outside this bounded packet (#8755).",
        "a0d729591d304503954d2be13948b1efd382cb29d88c1b845667c8fd0b711f40:1",
    ),
    (
        "scripts/projects/open_model_data/v4_open_weight_learning_study.py",
        "Existing path detection/privacy rule; not a temp directory producer.",
        "3d201e7701d7de84e782633a137a6abe74506ca0fe3b60ef5274263096b24ed4:1",
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
        "scripts/projects/ua_open_weight_eval/hf_jobs_baseline.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "1bc1d14ace5a1117442bb3c0eb426e61b65cd15451a420c4c790cde405608ab1:1",
    ),
    (
        "scripts/rag/benchmark_embeddings.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "e63af24144e98010a67b597989717f58f46fed472398a4182090e739e2800454:1",
    ),
    (
        "scripts/rag/benchmark_rerankers.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "fa11e5d86b17257803976932b8f31a817db4354bd10322a8d5bac4fc34b670f0:1",
    ),
    (
        "scripts/rag/migrate_add_literary_source_url.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "7657ce1f6d17244a67136ad136d2731ed93e8772de2c901a8f9ec80ec683f182:1",
    ),
    (
        "scripts/rag/poc_pair_page.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "3f2bdb5c6e3ed5f284c52a05c2b64922b54fbdcb80932330ddc0ba402dd68082:1",
    ),
    (
        "scripts/review/closeout_cli.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "b3aa9a5d42617c0b68719c98f3fb48d2bf30b2aebbc3b71ba0ae3b0746329db8:1",
    ),
    (
        "scripts/storage/artifacts.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "6872c6f40a0d28e1e45ac21457f6f8cb21877564cbbeb4571d6300fdbcfe9000:1 7c04326230eb9f14f45d886e4c20be927c2a43dd057153afafa96777ad76ff3c:1 cf16324e1d49563de02f3f93814b70da371b6174ec5edd79d4d0d51ecfc24fe6:1",
    ),
    (
        "scripts/storage/build_classification_table.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "de38a4b3d27869748216e8d8b2b660b8a1fab17ddb59a80dc44d7689f7f26715:1",
    ),
    (
        "scripts/storage/install_data_volume_dropins.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "555147d6feaab79ab3052f2cc60928944aa8adfd6f9a30beff6b67a8fee2da8f:1",
    ),
    (
        "scripts/tools/analyze_dead_code.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "52652b6d0a20d65322c20815f487b7b711c635229463d4251d6a7b8a9f1e2f03:1",
    ),
    (
        "scripts/wiki/diagnostics/retrieval_bakeoff_9233.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "29ce450404659d2c4d1df0ce1649be48612a465f53f3923394298e3fb74b40dc:1 7bc08c8d30e970d8bbe1217b4e37d4dab5c878e79128bcb835c546734b98f739:1 82a768536ff19763a3a840931416dcad693f9aeb3a65fea84cf3c8f60bc7ab6c:1 e6198f137697a713787cd1c15b304550eecdf915d9e32fbdb6425ffac3e6225b:1",
    ),
    (
        "scripts/wiki/fetch_external_sources.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "80128fd83446f42bfe156195837deec081c7272d09b0af60820626abf70f497b:1",
    ),
    (
        "scripts/wiki/run_chunk_policy_bakeoff.py",
        "Legacy literal/default/example; follow-up outside this bounded packet (#8755).",
        "7a0d1af525b57c1b0471b2e22b2b2e4e99b6400c66a586557d118dd49c4f5bc7:1",
    ),
    (
        "tests/agent_runtime/adapters/test_cursor_adapter.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "0b98abe8dccf8f19c998a0be2c2bca04d07cd9ae2e9d068f40fa2d28d6c82311:1 657dc2626b67c1273e614f714108d0c0667bac91572a3d328f3347b15a1b4cb2:1 77d5a6187f89959d00459396c5de94c61380634257541ce8eaf97fb8862c2d2a:2",
    ),
    (
        "tests/agent_runtime/test_acpx_adapter.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "0385e78aa5507980ea5b629d5c9a0505f8c2293d247217edafbc7ccde34f87b0:2 2676821ad57d4157817c761ab81441d836bc80524815d710d1a80e0a5a4a145e:2 641a23093a89388944d4c1865bea0dd57f7abb91263e540f4105c0bb3d05463c:1 f95316e83c3ccee9f6fd4998a9de78a167dd4280adb5d63a27a6a1b190fa9d1b:2",
    ),
    (
        "tests/agent_runtime/test_claude_permissions.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "97dfa412105444729b179ef986be6cb807e9de3e31f8f4118b0271cc015cd303:1",
    ),
    (
        "tests/agent_runtime/test_grok_reviewer_tools.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "20cf39be5272210ecf3f88f168d64d807b8d2c508e0d552d7bc8cd72a980b197:1 7ee84c26316c410898f53ddc3d4d4b8f6257be35e288603aa4faef00016f2d6e:1 e6da05fd4bcc084aee0ddedc5bcc99ad41913552c1fd75ece4a431aa71d950fc:1",
    ),
    (
        "tests/agent_runtime/test_review_mcp.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "a0515e9d9d82b47b2e22950ff6a53e16e01799649d6d2075d710231dd2e81bba:1",
    ),
    (
        "tests/ai_agent_bridge/test_ui_agy.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "c50482896c26790e72a87599d113fd550fb5f6034c75cadb4422b3354811691a:1",
    ),
    (
        "tests/api/opsec_sweep/test_opsec_route_sweep.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "ab88d4d1da7a82c6e641ba9a69e41677bceece895281f2dd5d4889a4e14afbe4:1 ad8d8584c67b9117388ca226a8b99815acdc7ea7fbac61c3bf0d609ee06a46f2:1 c3dbcd1207e1835f554d4d7fceca78c84ee60f6f8c9ee054c32e11d53cc43260:1",
    ),
    (
        "tests/api/opsec_sweep/test_opsec_sanitize.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "a3bc6f039b958ad0c9e2b4532d58759c3622d18f162adfed4697282362197409:2 fc7c3103cba39a68640d5b2667ab17dba2467c3bdb0d72ca420ec5f34e92f224:1",
    ),
    (
        "tests/api/opsec_sweep/test_opsec_scan.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "ce42f946689608c583dac2f1d10a8e3b1c711e08b2b995be003abcda55acc9a8:1 ed526f21b1c9ba360a4a48a24fbbedfe97cbb3601418dfe718d9889531a8b8b1:1",
    ),
    (
        "tests/api/test_atlas_jobs_router.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "5dd5fc216d5d873543123517e57dc53346e05c0f83da6de407f28477ed0a8e30:1 e2e6c1a4a55873b91ca0ff95b4dad4511982d562665c20cfe48d35eb7c3d632e:1 ea8c2c285b4106c1b154f412391fc0e20b40c23097d88aac63e3c11af584dd29:1",
    ),
    (
        "tests/audit/test_check_mdx_source_parity.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "e7cf38a7d98688f51c749993fcc205a4446d87368dbe464d8755f2a3915e4531:1",
    ),
    (
        "tests/audit/test_lint_agent_trailer.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "0502ea1bf78419862de04f2126c265e5efe00419c66a68d2b87d0724e284f6f3:1 970a8f9e04f29e15a2aa2a7af69a39791cc89cdaa917bdd00b7b21ea757ce341:2",
    ),
    (
        "tests/audit/test_qg_bakeoff.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "01a293307cc1064ca1ca99d5b9bd7a26756602c2d9e174a196da22164cf6885d:1",
    ),
    (
        "tests/audit/test_qg_shadow_run.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "b1ca26c0d64e0ee4ae93ed4c70e48fdd94e3a9c605cd40539017da3c7006cdf1:1",
    ),
    (
        "tests/build/test_fresh_cli.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "4b1299fdc76adcba7dbf842ced2d5995f2055b74506448badc7f7711a15f0be5:1",
    ),
    (
        "tests/build/test_fresh_path_guard.py",
        "Existing test literal; migration outside this bounded packet (#9702).",
        "e564f3201ef219053dd8b6b8c163c46042ab6e4dbe2484c131179c197568724b:1 7ba29ff00a51c6345994c175216930f1441a1f3e526e4cadbf7fd236db653329:1 974e64d68784c105870036fcbcc4a13cb95cbd594fcfc30968f85df59aa7f50b:1 987d5f2071ad8fee27ebb657646d6b2b250e6110f173b1f6ce7c6600671d6130:1 a8d7f83ee51e9f4c3c3e0163b4dbb8896611d082d76a387833ef20f292e81b58:1",
    ),
    (
        "tests/build/test_v7_build_resume.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "22e89f225ad0a570d4bf45c6d9811f3f18373390b7b1cfbaac11d48d1a7fbf98:1",
    ),
    (
        "tests/maintenance/test_claude_session_scratch.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "a73144ec31e1e70a566534e56044cba6207bf4b5c171e2daf7ce655e7dca111a:1",
    ),
    (
        "tests/orchestration/test_job_host_exec.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "169d4511743538b9be608c16cfd4a86ccd75de5d018d4cffc3f6bca40b8eda67:1 35eef957e7ac6dfb323982b5acdb0d4c5ac6bc3e41dba5a3f06a0d4ed8ad76c5:1 3cac3970d6434c27592340c8750dfe8c885f88ad6d33a46e20e461d810482bb5:1 6d0a3a07137da113db85eadf897776f58b8104244fa38a91b62e2d6e12fb9290:1 78a2828693382f4e53c60d70ea534f892706f2cdc6a74b1e3ff1f4a888c3f0af:1 9668994dd3e78910e686248664fb372b4ceb8c3b3c73f7394d646d27ca2e5199:3",
    ),
    (
        "tests/pre_commit/test_check_no_bare_python.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "9e80994f0b439e05f3880132a31e13fa097d3ea4cf8314ff55c688599dbe5ab1:1 cb9cdc313f79967100f6a3e49f923f4f18a947ae207ba12941bd493b9b0f2e65:1",
    ),
    (
        "tests/projects/open_model_data/test_phase3_corpus_miners.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "29625b19dfa8c416838b61c386b62740fd9ca7505bb07c941b944939b28a4635:1",
    ),
    (
        "tests/projects/open_model_data/test_v4_decolonization_reasoning.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "832075433fe6fe3f0f199aed1c990e9a46cd49771a56b8222ca54ec106c9e37f:1",
    ),
    (
        "tests/rag/test_benchmark_harness.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "27d7805ba12bfd4dd5da84cec85667d6fe6771f0134e7025980bb17a0a021887:1 5baee993f64ddb64ddf51382fe4ea53cbdc0dbdf8d8bdf9ad0de79bcb72560e7:1 a465ba02db96fc9d16efa679f9a6f570ce581b5286cebe92f42c3be9f9755072:1 c900af2a7ca71d8d943b4461ba6d7ec662425616490d5e2034f41520158735a7:1",
    ),
    (
        "tests/review/seeds/test_adjudicate.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "d87868c810a89ee3fa1474cf4fc4647c69ebf01886865725278719bac2de08f8:1",
    ),
    (
        "tests/review/test_template_admission.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "4a308850390f5aa111b55e895915b9e5e80e39430043b6c3fe7a03fc5aa11e72:1",
    ),
    (
        "tests/test_agent_runtime.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "ab58b3198f71daa1600a43aaebb0a1fcd4df069ca24aac5e04532edf3e9dab75:1",
    ),
    (
        "tests/test_agent_runtime_env_sanitize.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "00c81db6ac6e12ac8a15612bb20ab59421cdb05b6d57f0f676a1d0c2142c14c7:1 b05e8ab098fe2aa50201893b605fa6376c543d00ebe3481f2d33b72d0f02a18f:1 b0ef84eb140fe780b125aa15147727536f0e2706d21976526efadd7b563ced5b:1 cc77d44849990fe9b498a992839fe364c07d810c8355df81413d71db35c01dbf:1 e57675f0d44663b10cea1d278b24f23d5f76a49747ad313bc04142920647ceda:1",
    ),
    (
        "tests/test_ask_hermes.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "583cd88f6a966934a12dc9249856531b7025cc46a402c9dfcda66d888c146d5f:1",
    ),
    (
        "tests/test_atlas_job_protocol.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "15716cdf792289dfc44f56910d3fcb8d28b2c3e95b807c5106734a014511b500:1 19f3a543f4f0486d6ac3a31bec6a2a38b0f5e35baf12821a43b30bb8d854fb7e:1 34492587ed174aef0b19cb5e6922d2bd49289f9425e20eb0589035cc9e8ecd5c:1 4bb5ccd420379eaed73312bc81c4fd4606d036bd92029af3904a9bd7c88bc977:1 511acda571b82ad925b842d4c398de6c1bc4bbd73675beb6bf53a52771a65291:1 764cc45cd712603dcdf845c1d4b81372f1183e6b551dff1d4b077babed2403e9:2 86232b85e1881e7d84a60ab5166412ff79e2be82bb90161a32629f1edefcc733:1 8e7ac9f8aa37e299488d5ed0d5ba7dd882e1581e767bb7f27e86daaf6e07be41:2 c1b78efe7c80607993af2e5503c4ab2f4f428b8d84136954654b374c69d0cfdb:3 e2e6c1a4a55873b91ca0ff95b4dad4511982d562665c20cfe48d35eb7c3d632e:2 e6bd73273c1e7dba99c601d9844f9ad3f83a104a2d237353fcb7397bd14d2484:1 e706ff371a4aa11b55583bde6279b16d3931109fe6b117f5ff21e7d1181048ca:1 e8544ce2512fe5954d4e4a2fe74f5d02318743c6d451be2966fbd6ec4eda83c1:1",
    ),
    (
        "tests/test_backup_data_script.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "94b9e57a5011f479c24850ea0f748e0392ae7ee5194c79a163306ea3c994f419:1 fd63bacc44f78412e47dd0e3f7e21993bdb757e75cdc3e9276645351dfa20196:1",
    ),
    (
        "tests/test_bridge_inbox_cli.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "73d9019684d51706aaae17018e54c11e47ceb8248c1b6bb8d3d5183682437881:5",
    ),
    (
        "tests/test_build_sources_db_safety.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "64a66e5033ebe52b65971e7bd8adcd2cbc28c1ab9f820a8e4799c22e954b1567:1 f720b80c30717559c7b5534ca7fc43b10fb22c4bf06ad4407731d623f2df8c83:1",
    ),
    (
        "tests/test_certification_evidence.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "d03bc832067a4af0e3ffc10998b2af6214c85c1e7a2145ddfbbd331fded7468f:1",
    ),
    (
        "tests/test_citation_check.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "aace06b3a2442d7ea6a0173c05a4b0569fedea5040f42ce4f06d81bb5672285c:1",
    ),
    (
        "tests/test_claude_settings_permissions.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "068e5bc97d05574377b194c04625af29291192815cce684c8d1557c3be9580be:1 70d00d822877164ee66575338f93f8ab2ecce30dbb66a3dc4b920f841fd1d7ec:1 a67c5e5797b4ceffb0843d6eea984c98174620c0ae9e52906602951ae9b6c123:1 a7d7b3483122dfbee2b312562d5d700154596a9830e5e397ba95b98db1025d78:1",
    ),
    (
        "tests/test_clear_stale_git_lock.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "5aeb942d390281fc0fa994707545105ce501c740b360e32423f99461c50ef0c4:1",
    ),
    (
        "tests/test_codex_bridge.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "61284c8b646546d57d60409d008be38134d1c089a9311b8e57c97b8835991467:1 d1795242af5b441564ae91326632018c268beea0f3dac5bbde1cc6f0aa3fd838:1",
    ),
    (
        "tests/test_conftest_worktree_guard.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "3612fcbe709da936ea0d1873371ab7940c33963d04a1368ce5160aa43e5e330d:1 55d875a8d2a66d82174ac49740e36693d87ea47f0b6f6f6b8c1ad16578ddac10:1 85cb44bb2f270f68e338e8197e2489438baa0cbd0f3fdbd440ff713b0464ad50:1 9b7557820a299807a365fb1e828f666a6927634d538d71ee9e177f962890b90b:1 fe476dd3805d13e6aab0fc8892cd10c9f55ad24d8fb81779045ea76c6dc0c92f:1",
    ),
    (
        "tests/test_coverage_batch_agent.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "7b0559e9c0f5aaf008425371e63e202b088c53dc9ee71451d05c65c1f1dea1b6:29",
    ),
    (
        "tests/test_coverage_bridge_audit.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "0da758d1bbc117d5869f3184a60562a4f4e7e0fff754bb8428202045aeb22ade:1 2d406e7daf9227aaea86990d198b3119cb94c7f17f174861223b200c2a2d16b2:1 5b87ee12783b64bff080ca2fffa592c237344744576a593b8cc5f377c14233e9:1 d2bbe3a8ddb22edd0dda2e34f482e04abf35a75523138059e29dea33bc51ef24:1",
    ),
    (
        "tests/test_delegate.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "33f0583cd7c9a5955f851b1f7129c74eadd35308f59e735b9915596c45c3050e:1 4c93ba07004280171691c7a937f0ab990fc01bc70a984628177794e7ed483c46:1 632590773554973a0ad1e4e55a86eac6ec96e7defb18e77da7ed0381d165b017:1 70926b0281d7d07271b04529b2986ccbb7db229bae7231ccd9b801e17473aa2f:1 8485f898695fe7220b4734debaeefb13765ea8c694a0279b3b891e6929c2f175:1 8b870bb888fbd23c3deb973080fc6e19a9a49b44c67ac9cf85447cac1562b643:1 8c8d172dfae7820cec62bbe1d16acfc6292341e409870ab2c4fba2c528c77552:3 b9fb0b1fa2c3073b4dfe1573194920e5e3830248609b8dd1a893b63933497793:1 e3283a47ff84da2099322ff56bf6c3df86282c321d7d236d77d4b9ca6f55b479:1 e4957ef6a1af4d7f73bddfbfba66d6e0155da1a1a2910986e9509a4adadaa3ac:1 e6b7baa63b5d1f5cb1f444df2100444a8e016fedcdcb11a12c6fe8d2358aa39a:1 ea106d8e0097a0f65c300dd488275e16e7879c06a94192fc80b08d4d7d2870a1:1",
    ),
    (
        "tests/test_delegate_api.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "f1ba4371fa43ea259a115979dba64872159c6a7ef4907f9ede4f0a8faac2a602:1",
    ),
    (
        "tests/test_delegate_primary_integrity.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "9731e2b13468a18309c3631198515a58523bc2e0e963b59b8bb32a9d0dfb61e7:1",
    ),
    (
        "tests/test_delegate_read_only_db_lookups.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "4cc1be937798d635eddb3739d7f484d29721fbad1391e19ff6ff6c01daca2b52:1",
    ),
    (
        "tests/test_env_sanitize.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "9ac5d3aa786bfbc36a93ac2f4f79f7c24722676308136c650c74b5ed43d195b6:1 b96530f467e6ea8e193b2719502c700379d45be9fd89c64b8e9ad00b234cd572:1",
    ),
    (
        "tests/test_fleet_comms_message_plane.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "488de6c1d190afb73355a16a9f235a631be7520d7aefeb2e6899355ba3d54211:1 9f7e35ee95164b710ab481d43178d96c37a7c7cb5ec54bd73859b55bde1c8de7:1 f0d727092f6dfdf01b79901d669570d7d91a038de8c22e111e7c3708aa88faf8:1",
    ),
    (
        "tests/test_fleet_observer_api.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "e479568f2cfc71647dc38593c01de322c2480866c4204b5c86076affe5de1ab0:1",
    ),
    (
        "tests/test_fleet_pr_identity.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "a62be7b3bfe9f9444bf8298b5321039a608af1de7f94bcc131bbecff3d444332:1",
    ),
    (
        "tests/test_gemini_session.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "67c8630e12d9d0743ef949c3db7ba9baf7f3a19df9a7c890b6a8ea8ebdbf52aa:1",
    ),
    (
        "tests/test_guard_admin_merge.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "62f8e1429422bff63889e1e04e6dc2ff90af3ccfe4a125f0b3927b69c4a91685:1",
    ),
    (
        "tests/test_guard_branch_switch_in_main.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "54b1b78eb391550f8c689b50ce09c11c51935ea9f3134f8a69ef763734a847ab:1 cb11ee9a04f4b90a8c8f1f03ea9189c1ed715db74416866e1d1a041cb76a9b69:1",
    ),
    (
        "tests/test_guard_pr_merge.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "5e7a159030dfdacff5e323bce2cbd6bb7750b0e7bc52ebae64d355b33bb272c1:1",
    ),
    (
        "tests/test_guard_primary_checkout_write.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "000da3cdd3dd666c210122021c0bbc599c3f73d12a3e5d77fd89b4c6318fb8c3:1 00cf1ea67ae9fc2eb8f5d74354c9efe44dc35ac6ec85aeb24c823cf809277322:1 01a1511f55d9d426dacb0acb4f2092d45b18d36c877f6ccabe47d6175b9c8e96:1 0249959b15badedc70105ac3fece60cbc1df91f8d7251bcbcdceaf89824dac0a:1 03a8aa8e6a73f3fd71cb53a413fe9f5f8fc4736375931102b43daff29e0c5bcf:1 03e06bc89e1288f3685c32ddddb514df34947a28ee6bf30843901463f8190b81:2 050443f8f221c128669085250d1bd8a8068bcfa54842970aeb905d1d1f093076:1 067a7eb2131b9bcd33d88f30580f7bd041fc0cc972b9557b7bdb7a21d0ec3b8d:1 06fb12fdf96477ec3227a960f31e5cb1c7ef20ed1e7df7321d7064aaac7dcaf6:1 0b19628ed438327664b7136f653c84e17e37b35cee5d7523acbdab2c495c3c24:1 0bd6c1fa7e48a0fc84ba4d977a0cf293eeff78bf364f66e245b8115b410a59ab:1 0d484c558579f7147410801a045ec1b86280b5f1388fa33278c5f5e4b670f591:1 0eb152c8f375d83ad6de8e9e72e5eb7309f372a190062fe1f891c559cc1cfcef:1 0f28db7a7542bc428e5b2cbacd58cc4b7b124aecb52b4179c27bf377594f661c:1 10223a8c761bd9690999dd613cf127a80bf1bb45e1ceb579162ec984de0af11e:1 10712ceb5e28e9ec76e1b25f61eb54ff2895f646b948baf54094c6cf44108ea7:1 11db99ea89ddb9bff6180d4013f28290c6fea0af04b1053cecd2a6cc924b71d8:1 124937c97cc09ac54cfc12b252bda32cfec52d94ce565c8df0afb57be5c35068:1 131765dab492291477954a943de3d99b4009a25a80ddba4828be20ddd3bc6e22:1 13d9d9ff1cc92f716673cdd1b5f7def134fa0532e85befb54d76fb4c80f2f144:1 13f6d693aacbffa7a0870dc28823571cfd6b0684b1d05297bc0df8cb02ea3d8f:1 145a5faa8307e61573f8570cf283f9c41bf4c9b9c1c8dd6d9f4da43447d0ea79:1 154d2d6168e13ecedc0f024838f98b13f63fb2a0f22c02f3f7f59268d229ed93:1 1555186fe4e8e79b5b2b38b8a26f4cc9510fa7f1394f0db03a66af146c8921b5:1 1903a323a8e917d1fcf3bc6fde6e313ddf9448b023a6b6b8467d45367851da77:1 1ccb186cb357557b3430512853fc3ac3f39b930d5c99a6cfa5f6193f978a5ec8:1 1e4023c9a4caff8625cd8eabafdf443b237740a3cb982f3a58ee0123f6020caa:1 1e8b1eb388c52d028ab9a6711d9fd55baf000feffb3b182a8a2d50c2c54a1f6d:1 1f59c629953e178851089c57529af3ad4ae8f1e44001612f20eaf532347d2b98:1 1fd7de1113b5eab0b2c19d81d416cca31f246c3b0778399bb1cd1fe6ce954106:1 20ba8a4a9eba5259d29801552d16d3270401d77b00fad1beec6fb0dd17e51981:1 211685450bd017f324172659dfd0528f6a53dc82b1d8d0ac7d5dba7c16074cb0:1 226e7427b75ecb6bf137997e7d14ed3a72f3de94f6268155621c8a03b843fdd4:1 22bd8b56ba11b3971ec0571f7e1bed06a1711b8c35ab69694bd5ff24eb2b5a54:1 236ce953fd5fc572aab73df87de002439ae52156538f145255cbe112acb23010:1 241cb248f079d5994fbdd4a4718b821108df77ba872c5aade9c1731f28331de4:1 2434bcb7abf1d5def0f2f4c2d4d7f24564a88c08d972354d79a01241aa74f569:1 249c3f744e9c82a4a053df787eae427a6130335b90a88591349b7d8f38ba0c90:1 25b955358beb844e40269929fc031eca899c3f0120b45ba2069f673cabe2f8d9:1 29e2a678f000dc3f468c6e30645240a79f9c9764061e4328f54884dd63eb3fb3:1 29fc4d1230ce922a6009fd4fa1d0ab5df03ca3db7e532c2c73dcf087b01f578d:1 2d7bcaaf3529a91c88387c7db3067e82e6d6f15afd2bba0e964ba6af7f8dbff8:1 2e6c6cdb37a65a8cf797f713e1acc01da7ffa9d50dd29f7cde0c2ceeb2f20881:1 2eccaeb7d58ef8f00099cf68ff72b7c85cdd4406a9b5f45287a0138db48e1cb3:1 2fbaaaafa87c09d5a196ec598eb1cf84d6a39e9608e489553d99f255f16e9494:1 30950c7f0e12224c71d963bb3f4e5ff5dce35d2beb7838767f6fcb25ecf50859:1 30aef622b22be089199dbd2af13bbcfcc3e8f7806d89a6750c2fdf23dda46989:1 339193b6b545099323ceb487db7fc867383bda19b274c5c67f6e9e807529ae39:1 34142175cdeb79e1105c9e8f2a4808d48bbb7c243453f443f1d31e9359e6f8ec:1 35044d82070c87e72b60a214d0326d3038b9d1da370edd80daa1777b6d393afd:1 37326e930314c11ef445de96dc6d5f04acd7791323904432d2c465d43c374dcc:1 396b5a3187468f2f6c264e77caab605ae87b7a1353bcc72e1fd6953fc8081ee7:1 3cd2bce62f5ebc336993155984cb427786a573a4ea10d86ba11ed13caa067d71:1 3d5ac19bda9af6e233a26a72b5420fa70be903ecf3db2f7b27108d6cee65cdfc:1 3dc59e62cac881e3204a552d6de85386beebbd336ed68fc5ad3403231fed0390:1 45be54d046c8bc882ab65f94824263b4e7aad854205dabc9e0bf58319fe2e930:1 482fc83e0c491c41f3a4e8ed2a635d532282664f8f3fe3e7923f61332b52628c:1 4930a138c83336b696509f2554ad10e12d50e74d5fd5f5a8c7a62f2a28198dab:1 4a50aa2a035d9f649a9d8d28dbfcbd8a5b3410f46da1e82ba3d8df2ab1f75c55:1 4a9deff2afaf641753b724c135b4525a0e171106a9b68041b621eb14a403f1bf:1 4d437f24c3cb0fde008c3d6c8e412f7c86bb557a3f7b7b6f037672ee38798136:1 4e7a63d8f9a2ec0099c79880924d4ab1ee3a67614cdaf07d61b2bee95b18104e:1 51008e8275d3f2393aad435925adafa542c3e00919ffd36fbdbe663989822b09:1 520a631cef06db99b3b42baadcd3148a733995be900cd55cd72dd5fcbb04fbcb:1 52eadd224d2ea2bd09f9de2c318d87200702b6275488e91210c93c519a68e204:1 54f18777c68667db60944fd02978665849debcc568b017f08a54e587c0f8373d:1 552e274a1f2c5c855987fe2537eb55504a33186a79ad7fedd89bd758ff6c9caa:1 56fa135298728b19c9653588b8c2bf3955672902ab2ba632df8428076fc29ba3:1 5aa54db49f155ab828e8ba25b4d19994eab51278481bff0f0c0726bb7d8a401d:1 5c588d69427ec404e2345536c26d88bf1e5c435253954d4de2e3953be56ee8db:1 5d9192203d40f5e962259a5b492bfc314c2e271551ebffc1c2ff28c14bb30a52:1 5db8221695f53f560d3bfba33477c04b018a97254581d088b241e8e97ff9e325:1 62008d37db3e3b3a9f15880b57b755584f622a9de96c4af4ffccd1452c04dab9:1 67bf3691d7cff384f2414780b8d28df36a34adc0537af4e61b18d59381608c50:1 67c5b365cad22a1543517322d29458bf17448bf7bc686258c6244d2d562facf7:1 68933414dba17d9a29c7a70525136f9b3dd997a55cd0b1d0be1a51d40fc6ad55:1 68cb479aa4f9d925d588806709e874f5f4e1641b04af9e8a53fb4651343cb3bd:1 6aae5dae87c3a28e9d803edd44d51c1bc3eaf40569ddcb7eba595e2402b2f318:1 6b7dd5b847a8de55fa21944fc4eb6c5bd1d281c0efa4e6b26bad98c548e7b509:1 6f7d694d48321f5bc816a97485aa088446417d99202214131f6092e590e815c5:1 70e39ca012ed122f6e9d9c3c38e335f10fd8fe1f479bc6e1d1739994a2cce561:1 747fc5365a747b32afaf808f0aed3801cab6f24f34661a25afdc16d4f54efdb4:1 773a62680effe7f27bc600118cd6d9388b2cef29aa596faba551ee9803e826ec:1 7937d61ee7f8f32e822f2e64d081ced6c21b1804bf19062583dddeab68345643:1 7b14e15d92860f9e689150cab9fe4cd08ea1b92971b6d3c7facb53561f3a6ccc:1 7b86d2d3792d1951198d8b2dcbe5a577102fa03356ddf9807c0a863d10781575:1 7b8aa17bcfecea5f9e8678451fe937d5ef925059ab851484444b56c444d54d30:1 7da0ac9d1020c8693a09d9538a6921083ea213381253750a39da2bc90e2ed0ff:1 7e41eb4ea8a25179ad3561614df0a4aaa1409aad428c84a107a6f5ad5e3144d7:1 7e5bcf77f39c115bb5890343eb6101cce0c373d9ab1d11dafa69ae03afd57966:2 7f4e0b188f9bf0942e9c3b0002e78e9ab76abf85bef447d294ae6535ed2c5f1a:1 837d5cf703e2cf656e577215d1ed4a490cbaeb66649437312359dbd11618f6df:1 847ee5d4e2b79cfb3b23a1ae637b0a3a159775a95a0f59b99e916a8eed5a013c:1 86191bbd311ff36e1ffdb9fec513a5ef8512391e7781eada0ab347a9b7faf0f3:1 88a2836c0849ad1fc1575afd1eb6967c07023fc9e78a0d213a4ee10c57bfda5c:1 8941290e5e243a221d6c258db52cc158e82d3c03fbec19f8c3059786f21188f2:1 937070aa665da0b187d01d14c5abb52fb3e692baeaf9f23aa12e779370dba762:1 94102f1b8305201dd5fadb7cdf2f2965f07c8e846be7443daef58fc7e15acf05:1 941cde32f4ac1f3de9e73a341b5bd41928532e4195cdf966da222d2fd0f894e6:1 96bb204f4ed41376dadc173a5891e3afcf7a6c3d2865d9f354e23a0d44907b66:1 98380a71728fb2765754e72129f8d23ec366f00cd45b56a11de2bcce52c40138:1 98c22e04c96ec212a8a5fa38577ef2eea1a132204f4a4ba6328c884b32cae294:1 99954586bfa16ddc2347bd6725d49d3304665fdfee2446e22f9f300aa76fc511:1 9b815d733757da1c48b986782be4b5bb9e85243e0d9f68142c275077f6a93655:1 9d0e79a42640fee23314ce9b89e56f52bf88296ed0ca30c09625bfccbb15f3b5:1 9df8dc446ae08f3ff1ce2e82efac27e5bc5d4926d69fdaf0dad0c76e06896a44:1 9e19f4434077a5516985e30ca51a1a563196613636c62a3e1547c8158852c263:1 a136ac04d26fe57b0c53f9e2b2baab8085f7a5f77715e0962b53c8ca45ceaa23:1 a40cdf4388a55c8ba57558c84c37668d337812c47e55039d8ffb0381686be36a:1 a4570b42d7b7bf2a41fceb1810ac21989b55c559ccb225b9deeb4bec13609873:1 a9a5d960c21165a16368036f5c1a38875512f3f8efa30effc7ecbbb733b4e8ae:1 ab89e0afe489d8f99c7df481e433254b0e217b235cb7cdbdbd3eb0c707ca7646:1 ace5f674bc81cb251b40d9e1333bc2fbfd1bd4f934efda3268c1ee686007da60:1 b3725b6a6b24ec8710d4b655fc29ebc57b3a8ecb9585ac52a280ad78e4978146:1 b3cdcf98850e873d5e8a726e8eebaf5c2801a5c318b0daff8d44e94d10bda82d:1 b99d692d41b85bd58605b34dee70611f893a282c355f5e108833578f90ee9f19:1 b9f87d2db754bc021f4d49e2b8cc0de2ea1657ed1844099013d9abd6b16940d8:1 bab3526d7575486fbb1ffb174579108bd08359f6128c5306f89d666f2b365442:1 bc1e703aabf535a32153ce081f599947127afaa1edf4437ce33a65f63920ffc3:1 bf1b55fd99e1949a55cfedc6ff5fc2206df66785df44ffa9422def98a965c011:1 c08eb46371fa401d75a94caccd8121fea3481ac1057d8d1703a82595a71c4240:1 c3aebd5c7ab1294416028f31bc57e8dad30a7d3403f514d480b46e33d5381f5b:1 c4ecc4ca383bb2ce40fe826c4135c9e1ccb945b340b0ae5b1cd767066ef31c55:1 c81da273f10bbe69a2032ddeea497c545b554d10ad706020803ab7fcd3da6990:1 c8a4f6a6ed3526a758e1a8e36e51b39bf1e6eb5c2aaf68635dcef73ca23d3565:1 caa516f8042df92917682723245ae0b060b58954a5a3ab7a4c7814f1f3ab1da4:1 cb672fadd65f52bf65e8b230bc3c5dcece153767df3776d0def95439b3b25ef4:1 d092ab07ce313d99fdeda8baff66ccd9c88a6a1e68a29a29b0eab330587d7466:1 d19750ad93652a70d9a3072afe845621c247e6de72c88587c8a637e05772a73e:1 d1c8be84dec1ab97c802420188a03f331b52cb6b806ba352a1f487e8d68f1e3f:1 d70e7042486800bbdea65e8682258bfe84efdb23240a5639d70d197da73293b0:1 d96f3d7dba9873758dbb94cbcfe4ae1f7bfebedf7d9688bbfce501057aaa7555:1 db0175e20ef45cdcde0f7096c7ca4ee1b1ab04256b6a92d0c979fd15f081d53c:1 db1db44d8b7678be7d0c609ad05dd95c9768a25cbd85f6f7a9336329ae5cb445:1 dec83c3c61ff3f3eed75f885de6a0336276c4e49d70f818ac8ec76aad034de35:1 e3d257b1a40ebdc6938db4d01dc88ee8a1719e02150b8705e6e2a8909c4d67e0:3 e4939edc0fedd86536e9eab7c9f290dd074a09388d813a545f57cb7238cca2c4:1 e6849c3c935cba52816bdca7da04bfa8ecb9058ca4a6a5852b574320a869f83b:1 e9f5409df42546f4d4f1a97e1e61c01a482ff77614a7e38935b6f4dbdc037e80:1 eb121ad81f9029ee02f73c1cce551500ffdcf28982690b06fc4ce5c5c5d132b0:1 eb16f4774d71154b30534c41322976d7d618e554efe64b7f9fce638084928906:1 ec9f9b488eba2850003696b1d99fa799c0dc0f3be093ff8344f4c07705913671:1 efbee110c0dba08a271197ced6de91322d5553a9ca96c23514898f3bb18d7b32:1 efe7d827e8c83547fd553dffa6683ff697316a72695a0b43b3bcd0faf0578c00:1 f07460cab7fe20c10b4eba2885496dc35ae0068703cd905aed36ce508d4be7e8:1 f33c97114de3b6cb1775aa4fc2c969d4b328a2eccd58b94106a26dcdb3725d9b:1 f3d191863988b7f8b935154c65ebb30bed30ee9e8d86262594bfad036af2963d:1 f3e4c9a124a38b62a16a7ab7562b78921317c248b17aeb4f1a1cf72a7fbe8ca3:1 f3e83fa8948fbefd26e3807d8cc0a7a64087afad4cf43a3b7b7aff7e8ab93e80:1 f5a39fd5acd513ad4cbffbed5f48bd84fbac6670223e636195d93c40b1d13350:1 f63be3792cd8b54da3950c4129ab98e6287f14e5ab5d86d1b44451384dc5eb11:1 f781e6acc4301514a059d0bded8b77ae6837e5f9a3013c28b1d862ea1aa7a749:1 f8ba0159ab8be23c0d95f75bbedf743181f7acdc22f308ec44c8352ccee3bd0f:1 f8ebfab42b748770c9a2404d595cfe33329749a27d7825a81eaed7aba017a1b6:1 f918b2f50f3c84da38d73d590d063e924e0eff70648a830294fda592d1922329:1 fa6c2b96722ecfb17cb52197866e6ab13a3d278e0581cea50e5f603640fa0178:1 fa85b1cfe1d505c8190a60121e0a901b23a3ad9383f508c1fa908f4c1ae612f3:1 faa5c07df957790362c20e764f4b5feedd77ed885f23baabaf9f007367835bbf:1 fbd26e9881dfe8217b6e2132955e73783877c281aa2f740a9b94cac26513b858:1 fe85fe83f33d16125cc97e331942d6cadfbf86932f8267d600c04a1e3e6daea8:1 ff99b901b26fb972d5eabafd2f089daca6391c715029ea87a374298712cadb32:1 ffbcc586a0bd02eec67bd3cf372741d90fe178a21486370624c1b61e1052d274:1 ffeb86a9a82404cfff82e6f7c918293762d12c9be5852f23b385484db0a33c32:1",
    ),
    (
        "tests/test_guard_secret_print.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "03e06bc89e1288f3685c32ddddb514df34947a28ee6bf30843901463f8190b81:2 efe7d827e8c83547fd553dffa6683ff697316a72695a0b43b3bcd0faf0578c00:2",
    ),
    (
        "tests/test_health_20k_runner.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "9a81dd84ff10febd15f2cc3e81e0ff5b9819984216cab9555dd3c88534dd8309:4",
    ),
    (
        "tests/test_launch_reenrich_target_detection.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "2a8eacd9f7602ee91d4080eb6ddb76331b42024f8d02d9d6051a61ede8636699:2 9b13679fdc20dac81cad2fa1c9d1d6686e3e48c73fa5fbf3caf53067921aefc4:2 d2216cedd0c3908c5b745cbfc18040b8d35f8f31fe9b8ee5ffc8550c9ad40944:1 e81b1a27619f5f179bda118c9e98dfd527ffaccd2d8c6ea258a93e12fe116b48:1",
    ),
    (
        "tests/test_lexicon_runner_pr1.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "21131bdae5866c3f5b5b2da0cf4f1d4f98b62b1839459be094bfaf784de00ded:1",
    ),
    (
        "tests/test_lexicon_timeouts.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "288cdb48e98ff6bc923b23bb7043f5331bc60d2dd7e44a09ae8947ea5942d37d:2 76698d6fa066a054e3d1ae0b5dc8932e327e0a51fa07c6f9f4dbfe5e7793fb3e:1",
    ),
    (
        "tests/test_phase3_cycle007_evidence_validator.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "99caa930c034ccf179bf8921f59e34e2793c80f8feeb3a31e953978a13014d01:1",
    ),
    (
        "tests/test_retention_engine.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "02391888ccb6f49274726c2345c74f703162a1c2a33def38c43313888dd1eaca:1 09e53f1c85f3ee93a894559a0f90da776510d4a5e09b4d04f874a590424af0ee:1 37b3efbc4461de4050cd18e8044e73b233a332d98cff43bdcf6cfe21c03dd5b6:1 8ca9e1bbb1df8390d8e031968f578d6d8cf3c234334193983ecaa04f1e7ab0b8:1 f3424630a7e77b67559e0aca5a05994d3735e99fcd44e4df6e302d0dc9a8be44:1",
    ),
    (
        "tests/test_review_closeout_cli.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "6814ca425b869549a4a4589864ecb4b3fd38f916d1f75550dc363d03c74d8b6a:1",
    ),
    (
        "tests/test_review_isolation.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "2804b88e531d3963124e6d940fd4d6d118aa41072b589f195b55683089675f9e:1 a697175d9636ef5cb48121eacd85178437c31cf37d4a49830e6095d64fafdb0c:1 ecc2299b7cca74c2a646cc42d13dfac749c8ece3f11e64d1503c97419dae42c7:1",
    ),
    (
        "tests/test_rules_core_loading.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "89990ce05012a058e05a981ffb7d53071528c09acf7aeb4032496ed47e5d2a69:1 9c762b6eeabe184fdbe74d4964867a69f17229124ea5adb8e63aafabde8219fb:1 f0370c1f760ee091faaac3e1be21448672df9e5e16fdd701a6eb3dab34e61efc:1",
    ),
    (
        "tests/test_session_canary_hydrate.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "b49c9c7b24cf8969560a94fedb9d033ee224d7833bf874f5410b1bd9de381cca:1",
    ),
    (
        "tests/test_session_record.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "3b5c8b3f44ec288fc69587471482859ca86cf1069760a1e56c99663f6455144a:1 ec4e60c198f7c47d823ea26bab407b49ce285427a98b4a80de925ab0bf77861b:1 f123cdc0dfe2fe4920d3d01d2298de723aa657b166e4b0bbe9bfe553c5c9a65b:1",
    ),
    (
        "tests/test_shared_hydration.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "cbcbce9aa38263b1df2a380b5363f899ada794c26349000b9e6c8bdc79ea465a:1",
    ),
    (
        "tests/test_sibling_git.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "f008e1d096a56887753a70f7436bf849afa26cd61af7d83daa223420345c2543:1",
    ),
    (
        "tests/test_socket_guard.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "1b0417ba7d4fd54591d781fb18620603db45f8cf4533f20e08121291ae4e30e4:1 af2fc75a68d53ede10915d3656e4a3a9f164f2317e938d8695f1510af9f5af70:1",
    ),
    (
        "tests/test_source_inventory_review_decisions.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "fe54ed63ad57a104dd80a0143609b55c18347047a1c3a0b1282f925120662b09:1",
    ),
    (
        "tests/test_storage_resolver.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "e0e3e8c0d93b60603885ef0d35cc84f49eb744bbd706988abc36a5b6db065ce6:1",
    ),
    (
        "tests/test_v4_sources_transport_credential_namespace.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "ed3fdee7c888f4389c4222fd891021d840fc087836ee32003ae88cc065cea124:1",
    ),
    (
        "tests/test_v7_build_reviewer_assert.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "2ca2890f45d3d5734f55b9b8ffea1af72b8a25bb279b1944834f472643a14276:1",
    ),
    (
        "tests/test_verify_review.py",
        "Existing test literal; migration outside this bounded packet (#8755).",
        "fb04258d59aaa3da8b6cc76a5706d17904554d861e90e8560483361ced618fe8:1",
    ),
)


def scan_lines(repo_root: Path) -> list[tuple[str, int, str]]:
    """Collect literal-temp lines in Python/shell sources, including comments/help."""
    rows = []
    for directory in ("scripts", "tests"):
        for path in sorted((repo_root / directory).rglob("*")):
            if path.is_symlink() or not path.is_file() or path.suffix not in {".py", ".sh", ".bash"}:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if LITERAL_TEMP.search(line):
                    rows.append((path.relative_to(repo_root).as_posix(), number, line.strip()))
    return rows


def line_digest(line: str) -> str:
    """Identify exact stripped source text without emitting private path literals."""
    return hashlib.sha256(line.encode()).hexdigest()


def find_literal_tmp_paths(repo_root: Path = REPO_ROOT) -> list[tuple[str, int]]:
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
    for path, number, line in scan_lines(repo_root):
        key = path, line_digest(line)
        used[key] += 1
        if used[key] > allowances.get(key, 0):
            findings.append((path, number))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Flag literal system-temp paths outside the exact-line allowlist.\nUse before review; worker scratch belongs under the managed TMPDIR lease.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.hygiene.lint_tmp_paths\n  .venv/bin/python -m scripts.hygiene.lint_tmp_paths --repo .\nOutputs: source locations, counted fingerprints and remediation; no writes or literal path contents.\nExit codes: 0 clean; 1 findings; 2 invalid arguments.\nRelated: #8755; workflow.md; scripts.hygiene.lint_raw_rm_rf.",
    )
    parser.add_argument(
        "--repo", type=Path, default=REPO_ROOT, help="Repository to scan (default this checkout; example .)."
    )
    args = parser.parse_args(argv)
    findings = find_literal_tmp_paths(args.repo)
    if findings:
        fingerprints = {(path, number): line_digest(line) for path, number, line in scan_lines(args.repo)}
        counts = Counter((path, digest) for (path, _), digest in fingerprints.items())
        for path, number in findings:
            digest = fingerprints[path, number]
            print(
                f"{path}:{number}: literal system temp path; "
                f"counted fingerprint={digest}:{counts[path, digest]}"
            )
        print(
            'Fix producers: use "$TMPDIR/..." in shell or '
            "tempfile.TemporaryDirectory()/NamedTemporaryFile() in Python (honors TMPDIR). "
            "For a fixture, path detector, or deferred legacy use, add/update ALLOWLIST in "
            "scripts/hygiene/lint_tmp_paths.py: (repository-relative path, specific reason "
            "citing a follow-up issue such as #9702, counted fingerprint shown above). "
            "Merge the fingerprint into the file's existing entry; the number is the maximum "
            "allowed count of that exact stripped line, never a whole-file exemption."
        )
    print(f"literal_tmp_findings={len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
