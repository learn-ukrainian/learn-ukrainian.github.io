import { Component, type ErrorInfo, type ReactNode } from 'react';
import ChromeText, { ChromeDual } from '../lib/i18n/ChromeText';
import { CHROME_STRINGS } from '../lib/i18n/chrome';

interface PracticeErrorBoundaryProps {
  children: ReactNode;
}

interface PracticeErrorBoundaryState {
  error: Error | null;
}

export default class PracticeErrorBoundary extends Component<
  PracticeErrorBoundaryProps,
  PracticeErrorBoundaryState
> {
  state: PracticeErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): PracticeErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Practice hub render failure', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="lexicon-practice-fallback" role="alert" data-testid="practice-error-fallback">
          <p className="lexicon-practice-warning">
            <ChromeDual
              uk={CHROME_STRINGS.uk['practice.loadErrorReload']}
              en={CHROME_STRINGS.en['practice.loadErrorReload']}
            />
          </p>
          <button type="button" className="btn btn-accent" onClick={() => window.location.reload()}>
            <ChromeText k="practice.retry" />
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
