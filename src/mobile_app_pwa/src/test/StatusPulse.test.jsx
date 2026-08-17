import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatusPulse from '../components/StatusPulse';

describe('StatusPulse', () => {
  it('has displayName set to "StatusPulse"', () => {
    expect(StatusPulse.displayName).toBe('StatusPulse');
  });

  it('renders LIVE text when active is true', () => {
    render(<StatusPulse active={true} />);
    expect(screen.getByText('LIVE')).toBeInTheDocument();
  });

  it('renders OFFLINE text when active is false', () => {
    render(<StatusPulse active={false} />);
    expect(screen.getByText('OFFLINE')).toBeInTheDocument();
  });

  it('renders OFFLINE text when active is undefined', () => {
    render(<StatusPulse />);
    expect(screen.getByText('OFFLINE')).toBeInTheDocument();
  });

  it('applies green indicator class when active', () => {
    const { container } = render(<StatusPulse active={true} />);
    const indicator = container.querySelector('.bg-green-500');
    expect(indicator).toBeInTheDocument();
  });

  it('applies gray indicator class when inactive', () => {
    const { container } = render(<StatusPulse active={false} />);
    const indicator = container.querySelector('.bg-gray-500');
    expect(indicator).toBeInTheDocument();
  });

  it('applies animate-ping class when active', () => {
    const { container } = render(<StatusPulse active={true} />);
    const indicator = container.querySelector('.animate-ping');
    expect(indicator).toBeInTheDocument();
  });

  it('does not apply animate-ping class when inactive', () => {
    const { container } = render(<StatusPulse active={false} />);
    const indicator = container.querySelector('.animate-ping');
    expect(indicator).not.toBeInTheDocument();
  });

  it('is a memoized component', () => {
    // React.memo wraps the component; the type should not be a plain function
    expect(typeof StatusPulse).toBe('object');
    expect(StatusPulse.$$typeof).toBeDefined();
  });

  it('does not show LIVE when active is false', () => {
    render(<StatusPulse active={false} />);
    expect(screen.queryByText('LIVE')).not.toBeInTheDocument();
  });

  it('does not show OFFLINE when active is true', () => {
    render(<StatusPulse active={true} />);
    expect(screen.queryByText('OFFLINE')).not.toBeInTheDocument();
  });
});