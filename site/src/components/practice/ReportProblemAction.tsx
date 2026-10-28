import { useState } from 'react';
import { practiceReportUrl } from '../../lib/lexicon/practice-report';

const COPY = {
  en: { action: 'Report a problem', disclosure: 'The report will be public on GitHub. A GitHub account is required. You can edit the text before submitting.', continue: 'Continue' },
  uk: { action: 'Повідомити про помилку', disclosure: 'Звіт буде публічним на GitHub. Потрібен обліковий запис GitHub. Ви зможете змінити текст перед надсиланням.', continue: 'Продовжити' },
};
interface ReportProblemActionProps {
  records: readonly object[];
  type: string;
  chromeLocale: 'en' | 'uk';
  item?: string;
}
export default function ReportProblemAction({ records, type, chromeLocale, item }: ReportProblemActionProps) {
  const [disclosed, setDisclosed] = useState<string | null>(null);
  const url = practiceReportUrl(records, type, chromeLocale, item);
  if (!url) return null;
  const text = COPY[chromeLocale];
  return <div className="practice-report" lang={chromeLocale}>
    <button type="button" className="btn" style={{ minHeight: 44 }} aria-expanded={disclosed === url} onClick={() => setDisclosed(disclosed === url ? null : url)}>{text.action}</button>
    {disclosed === url && <div>
      <p>{text.disclosure}</p>
      <a className="btn" style={{ display: 'inline-flex', minHeight: 44, alignItems: 'center' }} href={url} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer"
        onClick={(event) => { if (practiceReportUrl(records, type, chromeLocale, item) !== url) event.preventDefault(); }}>{text.continue}</a>
    </div>}
  </div>;
}
