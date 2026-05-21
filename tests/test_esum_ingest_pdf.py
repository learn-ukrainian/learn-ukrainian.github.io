from scripts.ingest.esum_ingest import parse_esum


def test_parse_esum_text_pdf_merging():
    fixture_path = "tests/fixtures/esum_vol4_snippet.txt"
    with open(fixture_path, encoding="utf-8") as f:
        text = f.read()

    entries = parse_esum(text, vol=4, source_format="text-pdf")

    lemmas = [e["lemma"] for e in entries]

    # Check for expected lemmas
    assert "набербєрити" in lemmas
    assert "наберєжник" in lemmas
    assert "набаркати" in lemmas
    assert "набєзбаш" in lemmas
    assert "набахтурити" in lemmas
    assert "набетєжитися" in lemmas
    assert "набєхтатися" in lemmas

    # 'набат' is also in there, but it might be merged if current logic is failing
    assert "набат" in lemmas

def test_parse_esum_text_pdf_no_false_positives():
    # Example where abbreviation might cause false positive
    text = """на, схв. ні, слн. па, паїе (мн.), паїа (дв.); -- псл. па; -- очевидно, похідне від вказівної займенникової основи іє, кп. тієї самої, що і в частках но, 0-н, ге-н, займеннику ві-н, у лит. па «ну; так», по «то», лте. па (вигук погрози і відгону), гр. маї «так, справді», лат. пб «так, вірно», дінд. па-па «по-різному, так і сяк»; елемент -те (Че, слн. -їа) походить з дієслівної форми 2-Ї ос.
множини (і двоїни) і був доданий до вигуку, очевидно, вже в праслов'янський період. -- Черньх І 554; Фасмер Ш 33; Преобр. І 587; ЗСБМ 7, 159; Вгйскпег 351--352; Маспек ЕЗІС 3987; Зеспи5іві-5емс 977--978; Младенов 314; 5Кок П 495; Веліа[ Е55) П 209--210; ЗССЯ 21, 185--187; Е55) 51. єг. П 432--433; ЕгаепКе! 477; Маїде--Ноїт. П 150; Воізасд 655. -- Пор."""

    entries = parse_esum(text, vol=4, source_format="text-pdf")
    lemmas = [e["lemma"] for e in entries]

    # 'множини' should NOT be a lemma
    assert "множини" not in lemmas
