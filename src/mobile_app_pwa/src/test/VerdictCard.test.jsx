import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import VerdictCard from '../components/VerdictCard';

describe('VerdictCard', () => {
  it('has displayName set to "VerdictCard"', () => {
    expect(VerdictCard.displayName).toBe('VerdictCard');
  });

  it('is a memoized component', () => {
    expect(typeof VerdictCard).toBe('object');
    expect(VerdictCard.$$typeof).toBeDefined();
  });

  it('returns null when verdict is undefined', () => {
    const { container } = render(<VerdictCard />);
    expect(container.firstChild).toBeNull();
  });

  it('returns null when verdict is null', () => {
    const { container } = render(<VerdictCard verdict={null} />);
    expect(container.firstChild).toBeNull();
  });

  describe('PENDING status', () => {
    const pendingVerdict = {
      status: 'PENDING',
      action: 'Checking authentication',
      reason: 'Awaiting judge decision',
      timestamp: '2026-03-29T10:00:00Z',
    };

    it('renders PENDING heading', () => {
      render(<VerdictCard verdict={pendingVerdict} />);
      expect(screen.getByText('JUDGE IS THINKING')).toBeInTheDocument();
    });

    it('renders action text in PENDING state', () => {
      render(<VerdictCard verdict={pendingVerdict} />);
      expect(screen.getByText('Checking authentication')).toBeInTheDocument();
    });

    it('renders reason text in PENDING state', () => {
      render(<VerdictCard verdict={pendingVerdict} />);
      expect(screen.getByText('Awaiting judge decision')).toBeInTheDocument();
    });

    it('applies animate-pulse class in PENDING state', () => {
      const { container } = render(<VerdictCard verdict={pendingVerdict} />);
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('does not render status heading in PENDING state', () => {
      render(<VerdictCard verdict={pendingVerdict} />);
      expect(screen.queryByText('PENDING')).not.toBeInTheDocument();
    });
  });

  describe('PASSED status', () => {
    const passedVerdict = {
      status: 'PASSED',
      action: 'Valid Action',
      reason: 'Approved by JudgeGuard v2.0',
      timestamp: '2026-03-29T10:00:00Z',
    };

    it('renders PASSED status heading', () => {
      render(<VerdictCard verdict={passedVerdict} />);
      expect(screen.getByText('PASSED')).toBeInTheDocument();
    });

    it('renders action in PASSED state', () => {
      render(<VerdictCard verdict={passedVerdict} />);
      expect(screen.getByText('Valid Action')).toBeInTheDocument();
    });

    it('renders reason in PASSED state', () => {
      render(<VerdictCard verdict={passedVerdict} />);
      expect(screen.getByText('Approved by JudgeGuard v2.0')).toBeInTheDocument();
    });

    it('renders timestamp in PASSED state', () => {
      render(<VerdictCard verdict={passedVerdict} />);
      expect(screen.getByText('2026-03-29T10:00:00Z')).toBeInTheDocument();
    });

    it('applies green background class in PASSED state', () => {
      const { container } = render(<VerdictCard verdict={passedVerdict} />);
      expect(container.querySelector('.bg-green-900')).toBeInTheDocument();
    });
  });

  describe('BLOCKED status (non-PASSED, non-PENDING)', () => {
    const blockedVerdict = {
      status: 'BLOCKED',
      action: 'Dangerous Action',
      reason: 'Rejected by JudgeGuard v2.0',
      timestamp: '2026-03-29T11:00:00Z',
    };

    it('renders BLOCKED status heading', () => {
      render(<VerdictCard verdict={blockedVerdict} />);
      expect(screen.getByText('BLOCKED')).toBeInTheDocument();
    });

    it('renders action in BLOCKED state', () => {
      render(<VerdictCard verdict={blockedVerdict} />);
      expect(screen.getByText('Dangerous Action')).toBeInTheDocument();
    });

    it('renders reason in BLOCKED state', () => {
      render(<VerdictCard verdict={blockedVerdict} />);
      expect(screen.getByText('Rejected by JudgeGuard v2.0')).toBeInTheDocument();
    });

    it('renders timestamp in BLOCKED state', () => {
      render(<VerdictCard verdict={blockedVerdict} />);
      expect(screen.getByText('2026-03-29T11:00:00Z')).toBeInTheDocument();
    });

    it('applies red background class for non-PASSED status', () => {
      const { container } = render(<VerdictCard verdict={blockedVerdict} />);
      expect(container.querySelector('.bg-red-900')).toBeInTheDocument();
    });

    it('does not apply green background for BLOCKED status', () => {
      const { container } = render(<VerdictCard verdict={blockedVerdict} />);
      expect(container.querySelector('.bg-green-900')).not.toBeInTheDocument();
    });
  });

  describe('arbitrary non-PASSED, non-PENDING status', () => {
    it('applies red background for any unrecognized status', () => {
      const verdict = { status: 'FAILED', action: 'x', reason: 'y', timestamp: 'z' };
      const { container } = render(<VerdictCard verdict={verdict} />);
      expect(container.querySelector('.bg-red-900')).toBeInTheDocument();
    });
  });

  it('renders the "Action" label', () => {
    const verdict = { status: 'PASSED', action: 'Do thing', reason: 'ok', timestamp: 'now' };
    render(<VerdictCard verdict={verdict} />);
    expect(screen.getByText('Action')).toBeInTheDocument();
  });
});