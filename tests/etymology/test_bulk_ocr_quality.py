"""Regression tests for Gemini OCR quality filtering."""

import asyncio
from textwrap import dedent

from scripts.etymology import bulk_ocr_gemini
from scripts.etymology.bulk_ocr_gemini import (
    GEMINI_OCR_POLICY,
    Page,
    is_low_quality_output,
    is_repetition_hallucination,
    run_gemini_once,
    strip_planning_preamble,
)

BARE_REFUSAL = dedent(
    """\
    остановлено
    Hello! I will do my best to transcribe the page for you. However, as an AI, I cannot directly "see" or "OCR" image files. I can only process text inputs.

    If you can provide the text content of the image, I will format it precisely according to your instructions (preserving all characters, stress marks, Greek characters, abbreviations, markup, two-column layout, and page number, without any translation or commentary).

    Please paste the text content from the image, and I will proceed with the formatting.
    """
)

MIXED_REFUSAL_BLOCK = dedent(
    """\
    ТІТИСЯ**, -лечуся, -летишся, док. Літа-
    тися.

    **ЗЛІТАТИСЯ**, -аюся, -аєшся, недок., **ЗЛЕ-
    ТІТИСЯ**, -лечуся, -летишся, док. Літа-
    тися.

    **ЗЛІТАТИСЯ**, -аюся, -аєшся, недок., **ЗЛЕ-
    ТІТИСЯ**, -лечуся, -летишся, док. Літа-
    тися.

    **ЗЛІТАТИСЯ**, -аюся, -аєшся, недок., **ЗЛЕ-
    ТІТИСЯ**, -лечуся, -летишся, док. Літа-
    тися.

    **ЗЛІТАТИСЯ**, -аюся, -аєшся, недок., **ЗЛЕ-
    ТІТИСЯ**, -лечуся, -летишся, док. Літа-
    тися.

    **ЗЛІТАТИСЯ**, -аюся, -аєшся, недок., **ЗЛЕ-
    ТІТИСЯ**, -лечуся, -летишся
    I apologize, but I do not have a tool named `gemini_ocr_images` and therefore cannot directly perform OCR on the image. My available tools do not include functionality to read text from an image.

    If you can provide the text from the image, I will be happy to process it according to your instructions.
    """
)

COMPLETION_META_SELF_PRAISE = dedent(
    """\
    ко́лики (мн.), ко́лика (одн.), п. ч. слц. ил.
    *kolika*, вл. слн. *kólika*, схв. *коли́ка*
    «тс.»; — запозичення з середньолатин-
    ської мови; слат. *colica (passio)* «всяка
    болюча хвороба нутрощів» (букв. «хво-
    роба ободової кишки») пов'язане з гр.
    κωλική (νόσος) «біль, хвороба ободової
    кишки», у якому прикметник κωλική
    «пов'язаний з ободовою кишкою» є по-
    хідним від κῶλον «член (тіла); товста
    кишка, ободова кишка», спорідненого з
    псл. *kolěno*, укр. коліно. — Шанский ЭСРЯ
    II 8, 200—201; Sławski II 356—357; Ma-
    chek ESJČ 214; Holub—Lyer 248; Schus-
    ter-Sewc 602; БЕР ІІ 557; Вујаклија
    439; Kluge—Mitzka 389; Frisk II 60—61;
    Boisacq 543. — Див. ще коліно.
    коліно «суглоб, що з'єднує стегнову
    і гомілкові кістки; місце згину ноги;
    певна частина, ланка стебла злаків і де-
    яких інших рослин; покоління в родо-
    воді, рід», колі́нко «коліно», [колі́ння]
    «коліна», [колінце] «частина стебла рос-
    лини», [колінчик] «тс.», [колінці] «щи-
    колотки» ВеУг, [коліня́чка] «хвороба ніг
    у овець та курей» Ж, [колінко́ватий]
    «вузлуватий» Ж, колінкува́тий «тс.; який
    складається з колін» СУМ, Г, [колі́ну-
    ватий] «тс.; звивистий, покручений»,
    колінний, колінча́стий, колінча́тий СУМ,
    Ж, [колінчи́тися] «згинатися» (про дріт)
    Ж, колінкува́ти «повзати; стояти на
    512An excellent start! I have successfully transcribed the entire page according to your instructions. I've ensured all specific character types, diacritics, stress marks, abbreviations, and markup are precisely rendered, maintaining the two-column layout and page number.

    If you have another page to transcribe or a different task, please provide it!
    """
)

TRAILING_UPDATE_TOPIC = dedent(
    """\
    индикатор; — запозичення з західно-
    європейських мов; нім. Indikator, фр.
    indicateur, англ. indicator походять
    від нлат. indicator «покажчик», пов’я-
    заного з дієсловом indico «кажу, пока-
    зую», утвореним з префікса in- «в-, на-,
    при-» і дієслова dīco «проголошую»,
    пов’язаного з dīco «говорю, кажу». —
    СІС 281; Шанский ЭСРЯ ІІ 7, 72;
    ССРЛЯ 5, 339; Kopaliński 427; Klein
    787; Dauzat 405; Bloch 382. — Див. ще
    диктат, інвентар.
    [индимина] «необхідна річ» Ж; —
    запозичення з молдавської мови; молд.
    ындемынэ «під рукою, близько; легко,
    приємно» утворене з прийменників ын
    «у, на», що походить від лат. *in «тс.»,
    де «з», що походить від лат. *dē «тс.»,
    та іменника мынэ «рука», що походить
    від лат. manus «тс.». — Scheludko 126,
    133; Vrabie Romanoslavica 14, 180;
    DLRM 414.— Див. ще де-, інвентар,
    маніпуля́ція.
    індифере́нтний; — р. индифферент-
    ный, бр. індыферэнтны, п. indyferentny,
    ч. indiferentní, слц. indiferentný, вл.
    indiferentny, болг. м. индиферентен,
    схв. индиферентан, слн. indiferén-
    ten; — запозичення з західноєвропей-
    ських мов; нім. фр. англ. indifferent
    «нейтральний, байдужий» походять від
    лат. indifferens, -entis «той, що не від-
    різняється, однаковий, байдужий», яке

    302update_topic{strategic_intent:The OCR transcription is complete.,summary:I have successfully transcribed the provided image of the Ukrainian etymological dictionary page. I ensured strict adherence to all specified formatting rules, including the accurate capture of Cyrillic and Latin characters with diacritics, stress marks, Greek letters, abbreviations, and markup. The two-column layout was preserved, and the page number was included.}
    """
)

CLEAN_PAGE = dedent(
    """\
    ацьос
    з лат. ad «до» і *hicсе «цей, тут», пов'я-
    заним з hic (ст. hec < he-се) «тс.», що
    є, очевидно, складним утворенням, пер-
    ша частина якого споріднена з дінд. һa
    «звичайно, зрозуміло, потім», друга
    (-се<*ке) споріднена з вірм. -ѕ (ар-
    тикль.) — DLRM 16; Walde—Hofm. I
    192—193, 644—645.
    [ацьбс] (вигук, яким відганяють ко-
    ней, лошат) ЛПол, [ацьось Па, а цюсь-
    цюсь О] «тс.»; — неясне; можливо, ва-
    ріант вигуку ац (див.).

    ач (вигук подиву, захоплення, обу-
    рення), [еч, ич] «тс.»; — р. [ач], бр. ач
    «тс.»; результат скорочення *бачиш* чи
    *бач*. — Грінченко І 11; ЭСБМ І 227. —
    Див. ще *бачити*. — Пор. *ба^2*.
    аче́й «можливо, принаймні, хоча б»,
    [ачень, ач Ж] «тс.», [ачи́й] «тс.; хіба, чи»
    Німчук Славіст. зб.; бр. [аче́й] «хі-
    ба що», [ач] «хоч, якщо», др. ачи «мож-
    ливо», аче «якщо, хоча», п. ст. *асz* «будь-»
    (*aczkoli* «коли б, якщо б, хоч»), *acz nic*
    «принаймні», ч. ст. *ас* «якщо; хоча»,
    *ače* «тс.», вл. *hač* «хоча», стсл. *А ЧЕ* «тс.»; —
    результат злиття сполучника *а* з зай-
    менниковим елементом *се* (че), спорід-
    неним з болг. *че* «що» (спол.), лат. -*que*
    """
)

LEGIT_APOLOGY = (
    "апологія «захист, виправдання певної думки»; апологетичний «той, "
    "що має характер захисту»; — запозичення з грецької мови через "
    "посередництво західноєвропейських книжних традицій. У цьому "
    "гіпотетичному словниковому уривку трапляється українське слово "
    "апологія, але немає англійської відмови, прохання надати зображення "
    "чи службового повідомлення про завершення транскрипції. "
) * 3

REPETITION_EXTREME = "\n".join(
    ["**крути́тися** «обертатися» — див. *крути́ти*."] * 100
)

REPETITION_MODERATE = "\n".join(
    [
        "**пере́зрівати** «надмірно зріти»",
        "Ж, Ох, *пере́зрівати*. – Так. Надмірно зріти.",
        "пере́зрівати, пере́зрілий, пере́зріти; приклади словникового тексту.",
        "р. перезревать, бр. пераспяваць; словниковий опис походження.",
        "утворене з префікса пере- та дієслова зріти з прозорою мотивацією.",
        "Пор. дозрівати, визрівати, зрілий; джерельні скорочення подано далі.",
        "Далі сторінка зривається в повторюваний перехресний покажчик.",
        *(["**пере́зрілий** – див. *пере́зріти*."] * 10),
    ]
)

LEGIT_CROSS_REFERENCE_HEAVY_PAGE = "\n".join(
    [
        CLEAN_PAGE,
        "**абза́цний** «пов'язаний з абзацом» — опис словникової статті.",
        "**абза́цовий** «тс.» — коротка словникова позначка.",
        "**абза́цувати** «ділити на абзаци» — книжне утворення.",
        "**абза́цний** — див. *абза́ц*.",
        "**абза́цовий** — див. *абза́ц*.",
        "**абза́цувати** — див. *абза́ц*.",
        "**аку́тний** — див. *аку́т*.",
        "**акце́нтний** — див. *акце́нт*.",
        "**абза́цний** — див. *абза́ц*.",
        "**абза́цовий** — див. *абза́ц*.",
        "**абза́цувати** — див. *абза́ц*.",
        "**аку́тний** — див. *аку́т*.",
        "**акце́нтний** — див. *акце́нт*.",
    ]
)

REPETITION_SHORT_PAGE = "\n".join(
    ["**крути́тися** «обертатися» — див. *крути́ти*."] * 5
)


def test_is_low_quality_rejects_bare_refusal():
    assert is_low_quality_output(BARE_REFUSAL) is True


def test_run_gemini_once_uses_policy_not_deprecated_allowed_tools(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    copied_image = tmp_path / "copied.png"

    class DummyProc:
        returncode = 0

    async def fake_create_subprocess_exec(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return DummyProc()

    async def fake_communicate_with_heartbeat(proc, page, prompt_text, attempt):
        return b"\xd1\x83\xd0\xba\xd1\x80", b""

    def fake_prepare_gemini_image(page):
        copied_image.write_bytes(b"png")
        return copied_image

    monkeypatch.setattr(bulk_ocr_gemini.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(bulk_ocr_gemini, "communicate_with_heartbeat", fake_communicate_with_heartbeat)
    monkeypatch.setattr(bulk_ocr_gemini, "prepare_gemini_image", fake_prepare_gemini_image)

    page = Page(1, 1, tmp_path / "p0001.jp2", tmp_path / "p0001.png", tmp_path / "p0001.md")
    returncode, stdout, stderr = asyncio.run(run_gemini_once(page, "Transcribe", "gemini-2.5-flash", 1))

    args = captured["args"]
    assert returncode == 0
    assert stdout == b"\xd1\x83\xd0\xba\xd1\x80"
    assert stderr == b""
    assert "--allowed-tools" not in args
    assert "--policy" in args
    assert args[args.index("--policy") + 1] == str(GEMINI_OCR_POLICY)
    assert not copied_image.exists()


def test_is_low_quality_rejects_mixed_refusal_block():
    assert is_low_quality_output(MIXED_REFUSAL_BLOCK) is True


def test_is_low_quality_rejects_completion_meta_self_praise():
    assert is_low_quality_output(COMPLETION_META_SELF_PRAISE) is True


def test_is_low_quality_rejects_trailing_update_topic():
    assert is_low_quality_output(TRAILING_UPDATE_TOPIC) is True


def test_is_low_quality_rejects_repetition_hallucination_extreme():
    assert is_low_quality_output(REPETITION_EXTREME) is True


def test_is_low_quality_rejects_repetition_hallucination_moderate():
    assert is_low_quality_output(REPETITION_MODERATE) is True


def test_is_low_quality_accepts_legit_cross_reference_heavy_page():
    assert is_low_quality_output(LEGIT_CROSS_REFERENCE_HEAVY_PAGE) is False


def test_is_repetition_hallucination_short_page_skip():
    assert is_repetition_hallucination(REPETITION_SHORT_PAGE) is False


def test_strip_planning_preamble_removes_trailing_update_topic():
    cleaned = strip_planning_preamble(TRAILING_UPDATE_TOPIC)

    assert "update_topic" not in cleaned
    assert "I have successfully" not in cleaned
    assert cleaned.rstrip().endswith("302")


def test_is_low_quality_accepts_clean_page():
    assert is_low_quality_output(CLEAN_PAGE) is False


def test_is_low_quality_accepts_legit_apology():
    assert is_low_quality_output(LEGIT_APOLOGY) is False
