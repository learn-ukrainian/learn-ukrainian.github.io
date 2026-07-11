import { Component, type ErrorInfo, type ReactNode } from 'react';

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
            <span lang="uk">Не вдалося завантажити практику. Спробуйте оновити сторінку.</span>{' '}
            <span lang="en">/ We couldn’t load practice. Try reloading the page.</span>
          </p>
          <button type="button" className="btn btn-accent" onClick={() => window.location.reload()}>
            <span lang="uk">Спробувати ще раз</span>{' '}
            <span className="btn-sub" lang="en">Try again</span>
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
