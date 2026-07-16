import { Fragment, type ReactNode } from "react";
import type { EntryRecord } from "../lib/lexicon/atlas-data-source";
import { safeHref } from "../lib/lexicon/safe-url";
import {
  buildWordAtlasArticleView,
  CASE_ROWS,
  CONTEXT_LABELS_UK,
  isMirrorUrl,
  learnerFacingUrls,
  MARKED_LEARNER_NOTE,
  PERSON_ROWS,
  sourceClass,
  sourceHost,
  TRACK_LABELS_UK,
} from "../lib/lexicon/word-atlas-article-model";
import { morphologyFormCountLabel } from "../lib/lexicon/register-markers";
import styles from "./WordAtlasArticle.module.css";

export interface WordAtlasArticleProps {
  record: EntryRecord;
  generatedAt: string;
  manifestVersion: string;
  /** Optional typeahead slot (Astro AtlasTypeahead on prerendered pages). */
  children?: ReactNode;
}

/** External link: always new tab, visible ↗, SR-announced «(нова вкладка)» (W3). */
function ExtLink({
  href,
  children,
  className,
  label,
}: {
  href: string;
  children: ReactNode;
  className?: string;
  /** Base accessible name; «(нова вкладка)» is appended. */
  label: string;
}) {
  return (
    <a
      className={className}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${label} (нова вкладка)`}
    >
      {children}
      <span className="ext-link-indicator" aria-hidden="true">
        {" "}
        ↗
      </span>
    </a>
  );
}

function DefaultAtlasTypeahead() {
  const id = "atlas-article-search";
  const inputId = `${id}-input`;
  const listId = `${id}-list`;
  return (
    <div className="atlas-typeahead" data-atlas-typeahead="">
      <label htmlFor={inputId} className="atlas-typeahead-label sr-only">
        Шукати слово в Лексиконі
      </label>
      <input
        id={inputId}
        type="search"
        className="atlas-typeahead-input"
        placeholder="офіс / ofis / office"
        role="combobox"
        aria-expanded="false"
        aria-autocomplete="list"
        aria-haspopup="listbox"
        aria-controls={listId}
        // React 19 SSR emits camelCase for autoComplete/spellCheck; use HTML names
        // so prerendered markup matches Astro's autocomplete/spellcheck attributes.
        {...({ autocomplete: "off", spellcheck: "false" } as Record<string, string>)}
        data-atlas-typeahead-input=""
      />
      <ul
        id={listId}
        className="atlas-typeahead-list"
        role="listbox"
        aria-label="Результати пошуку"
        hidden
        data-atlas-typeahead-list=""
      />
    </div>
  );
}

export default function WordAtlasArticle({
  record,
  generatedAt,
  manifestVersion,
  children,
}: WordAtlasArticleProps) {
  const view = buildWordAtlasArticleView(record, generatedAt, manifestVersion);
  const {
    entry,
    enrichment,
    sections,
    synonymSets,
    definitionCards,
    maxSovietizationRisk,
    sovietizationKeywords,
    letter,
    headerStress,
    nounParadigm,
    verbParadigm,
    markedFormGroups,
    isFullyMarked,
    isExpressionLikeEntry,
    suppressMorphology,
    entryTypeLabel,
    posLabel,
    headwordIpa,
    heritageBoxes,
    etymologyStages,
    courseUsage,
    textbookItems,
    externalGroups,
    componentLinks,
    phraseHasGloss,
    shouldShowEditorialWarning,
    shouldShowHeritageDefense,
    styleNotes,
    statusBadges,
    articleOverview,
    sourceList,
    hasPractice,
    stressDisplay,
  } = view;

  const typeahead = children ?? <DefaultAtlasTypeahead />;

  return (

    <div className={`${styles.root} word-atlas`} data-word-atlas="">
      <div className="word-switch">
        {typeahead}
        <a className="atlas-button filter" href={safeHref("/lexicon/") ?? undefined}>До Атласу</a>
        <span className="poc-label">Атлас слів (Лексикон)</span>
      </div>

      <div id={`word-${entry.url_slug}`}>
        {entry.form_of ? (
          <>
            <div className="word-hero">
              <div className="word-hero-inner">
                <span className="lexicon-badge">Лексикон · Форма слова</span>
                <h1 className="word-title">{entry.lemma}</h1>
                <div className="word-pos">
                  {[posLabel, headwordIpa, entry.gloss ? `«${entry.gloss}»` : null].filter(Boolean).join(" · ")}
                </div>
              </div>
            </div>
            <div className="content-area">
              <section className="atlas-section">
                <div className="editorial-calque info" data-severity="blue" style={{marginTop: "2rem"}}>
                  <div className="editorial-calque-header">
                    <div className="editorial-info-icon" aria-hidden="true">→</div>
                    Форма слова
                  </div>
                  <p style={{fontSize: "1.1rem"}}>
                    <strong>{entry.lemma}</strong>
                    {" — це граматична форма слова "}
                    <a href={safeHref(`/lexicon/${entry.form_of.url_slug}/`) ?? undefined} style={{fontWeight: "bold", textDecoration: "underline"}}>{entry.form_of.lemma}</a>
                    {"."}
                  </p>
                  <p>
                    {"Перейдіть на сторінку леми "}
                    <a href={safeHref(`/lexicon/${entry.form_of.url_slug}/`) ?? undefined}>{`«${entry.form_of.lemma}»`}</a>
                    {" для перегляду повного значення, відмінювання та етимології."}
                  </p>
                </div>
              </section>
            </div>
          </>
        ) : (
          <>
            <div className="word-hero">
          <div className="word-hero-inner">
            <span className="lexicon-badge">{entryTypeLabel ? `Лексикон · ${entryTypeLabel}` : `Лексикон · A-Я · ${letter}`}</span>
            <h1 className="word-title">
              {entry.lemma}
              {headerStress && <span className="word-stress">{`[${headerStress}]`}</span>}
            </h1>
            <div className="word-pos">
              {[posLabel, headwordIpa, entry.gloss ? `«${entry.gloss}»` : null].filter(Boolean).join(" · ")}
            </div>
            <div className="word-badges">
              {statusBadges.map((badge) => (
                <span key={badge.label} className={`status-badge ${badge.className}`} title={badge.title}>{badge.label}</span>
              ))}
              {hasPractice && (
                <a
                  href={safeHref(`/words-of-the-day/practice/?lemmaId=${entry.url_slug}`) ?? undefined}
                  className="practice-link-hero"
                  style={{marginLeft: "0.75rem", display: "inline-flex", alignItems: "center", color: "var(--lu-primary, #146e78)", fontWeight: "800", fontSize: "0.9rem", textDecoration: "underline"}}
                >
                  Практикувати це слово →
                </a>
              )}
            </div>
          </div>
        </div>

      <div className="content-area">
          {shouldShowEditorialWarning && (
            <section className="atlas-section">
              <div className="editorial-warn" data-editorial-warn="russianism_red" data-severity="red">
                <div className="editorial-warn-header">
                  <div className="editorial-warn-icon" aria-hidden="true">⚠</div>
                  {heritageBoxes.red?.title}
                </div>
                <p>{heritageBoxes.red?.body}</p>
              </div>
            </section>
          )}

          {heritageBoxes.yellow && (
            <section className="atlas-section">
              <div className="editorial-calque" data-severity="yellow">
                <div className="editorial-calque-header">
                  <div className="editorial-calque-icon" aria-hidden="true">→</div>
                  {heritageBoxes.yellow.title}
                </div>
                <p>{heritageBoxes.yellow.body}</p>
                {heritageBoxes.yellow.detail && <p className="atlas-muted">{heritageBoxes.yellow.detail}</p>}
              </div>
            </section>
          )}

          {shouldShowHeritageDefense && heritageBoxes.green && (
            <section className="atlas-section">
              <div className="editorial-success" data-severity="green">
                <div className="editorial-success-header">
                  <div className="editorial-success-icon" aria-hidden="true">✓</div>
                  {heritageBoxes.green.title}
                </div>
                <p>{heritageBoxes.green.body}</p>
              </div>
            </section>
          )}

          {heritageBoxes.blue && (
            <section className="atlas-section">
              <div className="editorial-calque info" data-severity="blue">
                <div className="editorial-calque-header">
                  <div className="editorial-info-icon" aria-hidden="true">→</div>
                  {heritageBoxes.blue.title} (стосується означення, не слова)
                </div>
                <p>
                  {heritageBoxes.blue.body}
                </p>
                <p className="atlas-muted">
                  Тригер: <code>{heritageBoxes.blue.detail}</code>
                  {sovietizationKeywords.length > 0 && <> · ключові слова: <code>{sovietizationKeywords.join(", ")}</code></>}
                </p>
              </div>
            </section>
          )}

          <section className="atlas-section atlas-overview-section" aria-label="Склад сторінки Атласу">
            <h2>Дані Атласу</h2>
            <div className="atlas-overview-grid">
              {articleOverview.map((item) => (
                <div key={item.label} className={`atlas-overview-card ${item.ready ? "ready" : "pending"}`}>
                  <span className="overview-state" aria-hidden="true">{item.ready ? "✓" : "○"}</span>
                  <span className="sr-only">{item.ready ? "готово" : "очікує"}</span>
                  <span className="overview-label">{item.label}</span>
                  <span className="overview-detail">{item.detail}</span>
                </div>
              ))}
            </div>
          </section>

          {isExpressionLikeEntry && componentLinks.length > 0 && (
            <section className="atlas-section expression-detail" data-expression-detail={entry.entry_type}>
              <div className="component-links">
                <div className="chip-label">Складники:</div>
                <div className="chip-row">
                  {componentLinks.map((component) => (
                    component.targetSlug ? (
                      <a key={component.text} className="chip" href={`/lexicon/${component.targetSlug}/`}>{component.text}</a>
                    ) : (
                      <span key={component.text} className="chip">{component.text}</span>
                    )
                  ))}
                </div>
              </div>
            </section>
          )}

          {(definitionCards.length > 0 || enrichment?.meaning || phraseHasGloss) && (
            <section className="atlas-section">
              <h2>Значення</h2>
              {definitionCards.map((card) => (
                <div key={card.id} className={`def-card ${sourceClass(card)}`}>
                  <div className="def-source">
                    {card.source_url && !isMirrorUrl(card.source_url) && safeHref(card.source_url) ? (
                      <ExtLink
                        className="src-pill"
                        href={safeHref(card.source_url)!}
                        label={card.source_pill ?? card.source}
                      >
                        {card.source_pill ?? card.source}
                      </ExtLink>
                    ) : (
                      <span className="src-pill">{card.source_pill ?? card.source}</span>
                    )}
                    {card.note && <span>{card.note}</span>}
                  </div>
                  <div className="def-text">
                    {card.definitions.map((definition) => <p key={definition}>{definition}</p>)}
                  </div>
                  {card.flag_note && <div className="def-flag-inline">{card.flag_note}</div>}
                </div>
              ))}
              {definitionCards.length === 0 && enrichment?.meaning && (
                <div className="def-card sum20">
                  <div className="def-source">
                    <span className="src-pill">{enrichment.meaning.source}</span>
                    <span>словникове тлумачення</span>
                  </div>
                  <div className="def-text">
                    {enrichment.meaning.definitions.map((definition) => <p key={definition}>{definition}</p>)}
                  </div>
                  {enrichment.meaning.note && <div className="def-flag-inline">{enrichment.meaning.note}</div>}
                </div>
              )}
              {definitionCards.length === 0 && !enrichment?.meaning && phraseHasGloss && (
                <div className="def-card sum20">
                  <div className="def-source">
                    <span className="src-pill">Курс</span>
                    <span>курсова фраза / chunk</span>
                  </div>
                  <div className="def-text">
                    <p>{entry.gloss}</p>
                  </div>
                </div>
              )}
            </section>
          )}

          {enrichment?.etymology && (
            <section className="atlas-section" id="etymology">
              <h2>Етимологія</h2>
              <div className="ety-timeline">
                {etymologyStages.map((stage, index) => (
                  <Fragment key={`${stage.period}-${stage.word}-${index}`}>
                    {index > 0 && <div className="ety-arrow" aria-hidden="true">→</div>}
                    <button type="button" className="ety-stage" data-ety-note={stage.note}>
                      <span className="ety-period">{stage.period}</span>
                      <span className={`ety-word ${stage.className}`}>{stage.word}</span>
                    </button>
                  </Fragment>
                ))}
              </div>
              <div className="ety-note" data-ety-note-output aria-live="polite">{enrichment.etymology.text}</div>
              <p className="atlas-muted">Джерело: {enrichment.etymology.source}</p>
            </section>
          )}

          {enrichment?.morphology && !suppressMorphology && (
            <section className="atlas-section">
              <h2>Морфологія</h2>
              <p className="atlas-muted">
                {enrichment.morphology.pos} · {morphologyFormCountLabel(enrichment.morphology, isFullyMarked)} · {enrichment.morphology.source}
              </p>
              {nounParadigm ? (
                <table className="paradigm-table">
                  <caption>Відмінювання</caption>
                  <thead>
                    <tr>
                      <th scope="col" className="col-case">Відмінок</th>
                      <th scope="col">Однина</th>
                      <th scope="col">Множина</th>
                    </tr>
                  </thead>
                  <tbody>
                    {CASE_ROWS.map((caseRow) => (
                      <tr key={caseRow.key}>
                        <td className="case-name">{caseRow.label}</td>
                        <td className="form">{stressDisplay(nounParadigm.cases[caseRow.key]?.singular)}</td>
                        <td className="form">{stressDisplay(nounParadigm.cases[caseRow.key]?.plural)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : verbParadigm ? (
                <>
                  {verbParadigm.infinitive && (
                    <p><strong>Інфінітив:</strong> <span className="ukr">{stressDisplay(verbParadigm.infinitive)}</span></p>
                  )}
                  {Object.entries(verbParadigm.tenses ?? {}).map(([tense, numbers]) => (
                    <table key={tense} className="paradigm-table">
                      <caption>{tense}</caption>
                      <thead>
                        <tr>
                          <th scope="col" className="col-case">Особа</th>
                          <th scope="col">Однина</th>
                          <th scope="col">Множина</th>
                        </tr>
                      </thead>
                      <tbody>
                        {PERSON_ROWS.map((person) => (
                          <tr key={person.key}>
                            <td className="case-name">{person.label}</td>
                            <td className="form">{stressDisplay(numbers["однина"]?.[person.key])}</td>
                            <td className="form">{stressDisplay(numbers["множина"]?.[person.key])}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ))}
                </>
              ) : (
                !isFullyMarked && enrichment.morphology.forms.length > 0 && (
                  <table className="paradigm-table">
                    <caption>Форми</caption>
                    <thead>
                      <tr>
                        <th scope="col">Форма</th>
                        <th scope="col">Позначка</th>
                      </tr>
                    </thead>
                    <tbody>
                      {enrichment.morphology.forms.slice(0, 24).map((form) => (
                        <tr key={`${form.form}-${form.label}`}>
                          <td className="form">{form.stress ?? stressDisplay(form.form)}</td>
                          <td className="case-name">{form.label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )
              )}
              {markedFormGroups.length > 0 && (
                isFullyMarked ? (
                  <div className="marked-forms marked-forms-primary">
                    <p className="atlas-muted marked-forms-note">{MARKED_LEARNER_NOTE}</p>
                    {markedFormGroups.map((group) => (
                      <div key={group.marker_label} className="marked-forms-group">
                        <div className="marked-forms-label">{group.marker_label}</div>
                        <table className="paradigm-table">
                          <caption>{group.marker_label}</caption>
                          <thead>
                            <tr>
                              <th scope="col">Форма</th>
                              <th scope="col">Позначка</th>
                            </tr>
                          </thead>
                          <tbody>
                            {group.forms.map((form) => (
                              <tr key={`${form.form}-${form.label}`}>
                                <td className="form">{form.stress ?? stressDisplay(form.form)}</td>
                                <td className="case-name">{form.label}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ))}
                  </div>
                ) : (
                  <details className="marked-forms">
                    <summary>Марковані форми (нестягнені, застарілі, розмовні)</summary>
                    <p className="atlas-muted marked-forms-note">{MARKED_LEARNER_NOTE}</p>
                    {markedFormGroups.map((group) => (
                      <div key={group.marker_label} className="marked-forms-group">
                        <div className="marked-forms-label">{group.marker_label}</div>
                        <table className="paradigm-table">
                          <caption>{group.marker_label}</caption>
                          <thead>
                            <tr>
                              <th scope="col">Форма</th>
                              <th scope="col">Позначка</th>
                            </tr>
                          </thead>
                          <tbody>
                            {group.forms.map((form) => (
                              <tr key={`${form.form}-${form.label}`}>
                                <td className="form">{form.stress ?? stressDisplay(form.form)}</td>
                                <td className="case-name">{form.label}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ))}
                  </details>
                )
              )}
            </section>
          )}

          {styleNotes.length > 0 && (
            <section className="atlas-section">
              <h2>Стилістичні нотатки</h2>
              <div className="editorial-calque info" data-severity="blue">
                <div className="editorial-calque-header">
                  <div className="editorial-info-icon" aria-hidden="true">ℹ</div>
                  Редакційна нотатка
                </div>
                {styleNotes.map((note) => <p key={note}>{note}</p>)}
              </div>
            </section>
          )}

          {((sections?.synonyms?.items.length ?? 0) > 0 || (sections?.antonyms?.items.length ?? 0) > 0) && (
            <section className="atlas-section">
              <h2>Синоніми та антоніми</h2>
              {(sections?.synonyms?.items.length ?? 0) > 0 && (
                <div>
                  <div className="chip-label">Синоніми:</div>
                  {synonymSets.length > 0 ? (
                    <div className="synonym-sets">
                      {synonymSets.map((synset) => (
                        <div key={synset.id} className="synonym-set">
                          {(synset.pos || synset.gloss?.text) && (
                            <div className="synonym-set-context">
                              {[synset.pos, synset.gloss?.text].filter(Boolean).join(" · ")}
                            </div>
                          )}
                          <div className="chip-row">
                            {synset.members
                              .filter((member) => member.lemma !== entry.lemma)
                              .map((member) => (
                                <span key={member.lemma} className="chip">
                                  {member.stressed}
                                  {member.gloss?.text ? (
                                    <span className="chip-gloss">{member.gloss.text}</span>
                                  ) : null}
                                </span>
                              ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="chip-row">
                      {sections!.synonyms!.items.map((item) => <span key={item} className="chip">{item}</span>)}
                    </div>
                  )}
                </div>
              )}
              {(sections?.antonyms?.items.length ?? 0) > 0 && (
                <div style={{marginTop: "14px"}}>
                  <div className="chip-label">Антоніми:</div>
                  <div className="chip-row">
                    {sections!.antonyms!.items.map((item) => <span key={item} className="chip antonym">{item}</span>)}
                  </div>
                </div>
              )}
              <div className="data-caveat">
                Дані синонімів та антонімів показано з джерел маніфесту; звіряйте з контекстом перед уживанням.
                {learnerFacingUrls(sections?.synonyms?.source_urls).length ? (
                  <>
                    {" "}Джерела синонімів: {learnerFacingUrls(sections?.synonyms?.source_urls).map((url, index) => {
                      const href = safeHref(url);
                      if (!href) return null;
                      const host = sourceHost(url);
                      return (
                        <Fragment key={url}>
                          {index > 0 && " · "}
                          <ExtLink href={href} label={host}>{host}</ExtLink>
                        </Fragment>
                      );
                    })}
                  </>
                ) : null}
                {learnerFacingUrls(sections?.antonyms?.source_urls).length ? (
                  <>
                    {" "}Джерела антонімів: {learnerFacingUrls(sections?.antonyms?.source_urls).map((url, index) => {
                      const href = safeHref(url);
                      if (!href) return null;
                      const host = sourceHost(url);
                      return (
                        <Fragment key={url}>
                          {index > 0 && " · "}
                          <ExtLink href={href} label={host}>{host}</ExtLink>
                        </Fragment>
                      );
                    })}
                  </>
                ) : null}
              </div>
            </section>
          )}

          {(sections?.homonyms?.items.length ?? 0) > 0 && (
            <section className="atlas-section">
              <h2>Омоніми</h2>
              <div className="chip-row">
                {sections!.homonyms!.items.map((item) => (
                  <span key={`${item.word}-${item.homonym_no ?? 0}`} className="chip">
                    <strong>{item.homonym_no ? `${item.word}` : item.word}{item.homonym_no ? <sup>{item.homonym_no}</sup> : null}</strong>
                    {item.pos ? ` (${item.pos}) — ${item.gloss}` : ` — ${item.gloss}`}
                  </span>
                ))}
              </div>
              <div className="data-caveat">
                Омоніми показано за нумерованими словниковими заголовками; звіряйте значення з контекстом.
                {learnerFacingUrls(sections?.homonyms?.source_urls).length ? (
                  <>
                    {" "}Джерела омонімів: {learnerFacingUrls(sections?.homonyms?.source_urls).map((url, index) => {
                      const href = safeHref(url);
                      if (!href) return null;
                      const host = sourceHost(url);
                      return (
                        <Fragment key={url}>
                          {index > 0 && " · "}
                          <ExtLink href={href} label={host}>{host}</ExtLink>
                        </Fragment>
                      );
                    })}
                  </>
                ) : null}
              </div>
            </section>
          )}

          {(sections?.paronyms?.items.length ?? 0) > 0 && (
            <section className="atlas-section">
              <h2>Пароніми</h2>
              <div className="chip-row">
                {sections!.paronyms!.items.map((item) => (
                  <span key={item.word} className="chip">
                    <strong>Не плутати з {item.word}</strong>
                    {item.distinction ? ` — ${item.distinction}` : ""}
                    {item.exam_provenance?.length ? ` (${item.exam_provenance.join("; ")})` : ""}
                  </span>
                ))}
              </div>
              <div className="data-caveat">
                Пароніми — близькі за формою слова з різними значеннями; розрізняйте їх за контекстом.
                {learnerFacingUrls(sections?.paronyms?.source_urls).length ? (
                  <>
                    {" "}Джерела паронімів: {learnerFacingUrls(sections?.paronyms?.source_urls).map((url, index) => {
                      const href = safeHref(url);
                      if (!href) return null;
                      const host = sourceHost(url);
                      return (
                        <Fragment key={url}>
                          {index > 0 && " · "}
                          <ExtLink href={href} label={host}>{host}</ExtLink>
                        </Fragment>
                      );
                    })}
                  </>
                ) : null}
              </div>
            </section>
          )}

          {(sections?.idioms?.items.length ?? 0) > 0 && (
            <section className="atlas-section">
              <h2>Фразеологізми та сталі вирази</h2>
              {sections!.idioms!.items.map((idiom) => (
                <div key={idiom.phrase} className="resource-card">
                  <h3>{idiom.phrase}</h3>
                  <p>{idiom.definition}</p>
                  {idiom.source_url && !isMirrorUrl(idiom.source_url) && safeHref(idiom.source_url) ? (
                    <ExtLink className="tag" href={safeHref(idiom.source_url)!} label={idiom.source}>
                      {idiom.source}
                    </ExtLink>
                  ) : (
                    <span className="tag">{idiom.source}</span>
                  )}
                </div>
              ))}
            </section>
          )}

          {enrichment?.literary_attestation && (
            <section className="atlas-section">
              <h2>Літературні засвідчення</h2>
              <div className="source-box">
                <div className="source-box-header">
                  {enrichment.literary_attestation.source_url && !isMirrorUrl(enrichment.literary_attestation.source_url) && safeHref(enrichment.literary_attestation.source_url) ? (
                    <ExtLink
                      href={safeHref(enrichment.literary_attestation.source_url)!}
                      label={enrichment.literary_attestation.source_label ?? "Літературний корпус"}
                    >
                      {enrichment.literary_attestation.source_label ?? "Літературний корпус"}
                    </ExtLink>
                  ) : (
                    enrichment.literary_attestation.source_label ?? "Літературний корпус"
                  )}
                </div>
                <blockquote>{enrichment.literary_attestation.text}</blockquote>
                <div className="source-cite">
                  {enrichment.literary_attestation.source}
                  {enrichment.literary_attestation.chunk_id && ` · ${enrichment.literary_attestation.chunk_id}`}
                </div>
              </div>
              <p className="atlas-muted">Джерело: <code>{enrichment.literary_attestation.source}</code></p>
            </section>
          )}

          {textbookItems.length > 0 && (
            <section className="atlas-section">
              <h2>У шкільних підручниках</h2>
              {textbookItems.map((item) => (
                <div key={item.title} className="resource-card textbook">
                  <h3>{item.title}</h3>
                  {item.text && <p>{item.text}</p>}
                  {item.tag && <span className="tag">{item.tag}</span>}
                </div>
              ))}
            </section>
          )}

          {externalGroups.length > 0 && (
            <section className="atlas-section">
              <h2>Зовнішні матеріали</h2>
              {externalGroups.map((group) => (
                <div key={group.name} className="external-group">
                  <div className="external-group-header">{group.name} <span className="external-group-count">{group.materials.length}</span></div>
                  {group.materials.map((item) => {
                    const materialHref = item.url ? safeHref(item.url) : null;
                    return (
                      <div key={item.title} className={`resource-card ${item.kind ?? "blog"}`}>
                        <h3>
                          {materialHref ? (
                            <ExtLink href={materialHref} label={item.title}>{item.title}</ExtLink>
                          ) : (
                            item.title
                          )}
                        </h3>
                        {item.description && <p>{item.description}</p>}
                        {item.tag && <span className="tag">{item.tag}</span>}
                      </div>
                    );
                  })}
                </div>
              ))}
            </section>
          )}

          {courseUsage.length > 0 && (
            <section className="atlas-section">
              <h2>У курсі — модулі, де зустрічається це слово</h2>
              {courseUsage.map((usage) => (
                <div key={`${usage.track}-${usage.module_num}-${usage.slug}`} className="used-in-card">
                  <span className="module-id">{`${TRACK_LABELS_UK[usage.track] ?? usage.track.toUpperCase()} M${String(usage.module_num).padStart(2, "0")}`}</span>
                  <span className="module-title">{usage.slug}</span>
                  <span className="lesson-gloss">{CONTEXT_LABELS_UK[usage.context] ?? usage.context}</span>
                  <a href={safeHref(`/${usage.track}/${usage.slug}/`) ?? undefined}>відкрити →</a>
                </div>
              ))}
              <p className="atlas-muted">Сканування <code>curriculum/l2-uk-en/*/*/vocabulary.yaml</code> · {courseUsage.length} модулі</p>
            </section>
          )}

          {(enrichment?.translation?.en?.length ?? 0) > 0 && enrichment?.translation && (
            <section className="atlas-section">
              <h2>Переклад</h2>
              <div className="translation-block">
                <span className="uk-side">{entry.lemma}</span>
                <span className="arrow">↔</span>
                <div className="en-side" lang="en">
                  {enrichment.translation.en.map((term) => <span key={term} className="en-term">{term}</span>)}
                </div>
              </div>
              <p className="atlas-muted">Джерело: {enrichment.translation.source}</p>
            </section>
          )}

          {entry.wiki_reference && (
            <section className="atlas-section">
              <h2>Вікіпедія</h2>
              <div className="wiki-card">
                {entry.wiki_reference.wikipedia ? (
                  <>
                    <h3>{entry.wiki_reference.wikipedia.title}</h3>
                    {entry.wiki_reference.wikipedia.summary && <p>{entry.wiki_reference.wikipedia.summary}</p>}
                    <p className="wiki-source">
                      Джерело: {safeHref(entry.wiki_reference.wikipedia.url) ? (
                        <ExtLink
                          href={safeHref(entry.wiki_reference.wikipedia.url)!}
                          label={entry.wiki_reference.wikipedia.url}
                        >
                          {entry.wiki_reference.wikipedia.url}
                        </ExtLink>
                      ) : null}
                    </p>
                  </>
                ) : (
                  <h3>Вікімедіа</h3>
                )}
                <p className="wiki-source">
                  {entry.wiki_reference.wiktionary_url && safeHref(entry.wiki_reference.wiktionary_url) && (
                    <ExtLink href={safeHref(entry.wiki_reference.wiktionary_url)!} label="Вікісловник">
                      Вікісловник
                    </ExtLink>
                  )}
                  {entry.wiki_reference.wikisource_url && safeHref(entry.wiki_reference.wikisource_url) && (
                    <>
                      {" · "}
                      <ExtLink href={safeHref(entry.wiki_reference.wikisource_url)!} label="Вікіджерела">
                        Вікіджерела
                      </ExtLink>
                    </>
                  )}
                </p>
              </div>
            </section>
          )}

          <div className="provenance-footer">
            <h3>Походження даних</h3>
            <div className="provenance-list">
              {sourceList.map((source) => (
                <span key={source} className="src">{source}</span>
              ))}
            </div>
            <div className="meta-line">
              <span>маніфест: {manifestVersion}</span>
              <span>згенеровано: {generatedAt}</span>
              {maxSovietizationRisk > 0 && <span>СУМ-11 із радянським ризиком приховано з тлумачень</span>}
            </div>
          </div>
        </div>
          </>
        )}
      </div>
    </div>
  );
}
