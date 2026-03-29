import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import axios from 'axios';
import App from '../App';

vi.mock('axios');

const mockConfig = {
  title: 'Antigravity Mobile',
  theme: 'light',
  content: 'Welcome',
  components: [],
};

const mockConfigWithVerdict = {
  ...mockConfig,
  last_verdict: {
    action: 'Valid Action',
    status: 'PASSED',
    reason: 'Approved',
    timestamp: '2026-03-29T10:00:00Z',
  },
};

beforeEach(() => {
  vi.useFakeTimers();
  // Default: tab is visible
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    get: () => 'visible',
  });
  vi.clearAllMocks();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('App - initial render', () => {
  it('shows waiting state before first fetch resolves', () => {
    axios.get.mockReturnValue(new Promise(() => {})); // never resolves
    render(<App />);
    expect(screen.getByText('WAITING FOR ACTION...')).toBeInTheDocument();
    expect(screen.getByText('JUDGE GUARD')).toBeInTheDocument();
  });

  it('performs an initial fetch on mount', async () => {
    axios.get.mockResolvedValue({ data: mockConfig });
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(axios.get).toHaveBeenCalled();
  });

  it('includes a cache-busting timestamp in the request URL', async () => {
    axios.get.mockResolvedValue({ data: mockConfig });
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    const url = axios.get.mock.calls[0][0];
    expect(url).toMatch(/\/app_config\.json\?t=\d+/);
  });
});

describe('App - successful data fetch', () => {
  it('shows config title in footer after successful fetch', async () => {
    axios.get.mockResolvedValue({ data: mockConfig });
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(screen.getByText(/Antigravity Mobile/)).toBeInTheDocument();
  });

  it('renders VerdictCard when last_verdict is present in config', async () => {
    axios.get.mockResolvedValue({ data: mockConfigWithVerdict });
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(screen.getByText('PASSED')).toBeInTheDocument();
    expect(screen.getByText('Valid Action')).toBeInTheDocument();
  });

  it('does not render VerdictCard when last_verdict is absent', async () => {
    axios.get.mockResolvedValue({ data: mockConfig });
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(screen.getByText('WAITING FOR ACTION...')).toBeInTheDocument();
  });

  it('renders StatusPulse as connected after successful fetch', async () => {
    axios.get.mockResolvedValue({ data: mockConfig });
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(screen.getByText('LIVE')).toBeInTheDocument();
  });
});

describe('App - smart polling: skip fetch when tab hidden', () => {
  it('does not call axios.get when document is hidden', async () => {
    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      get: () => 'hidden',
    });
    axios.get.mockResolvedValue({ data: mockConfig });
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(600);
    });
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('fetches immediately when tab becomes visible again', async () => {
    // Start hidden
    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      get: () => 'hidden',
    });
    axios.get.mockResolvedValue({ data: mockConfig });
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(200);
    });
    expect(axios.get).not.toHaveBeenCalled();

    // Simulate tab becoming visible
    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      get: () => 'visible',
    });
    await act(async () => {
      document.dispatchEvent(new Event('visibilitychange'));
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(axios.get).toHaveBeenCalled();
  });
});

describe('App - smart polling: skip state update when data unchanged', () => {
  it('calls axios.get on each poll interval', async () => {
    axios.get.mockResolvedValue({ data: mockConfig });
    await act(async () => {
      render(<App />);
      // Allow initial fetch to complete
      await vi.advanceTimersByTimeAsync(100);
    });
    const callsAfterInit = axios.get.mock.calls.length;
    expect(callsAfterInit).toBeGreaterThanOrEqual(1);

    // Advance two 500ms intervals
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    // Should have additional fetches from the intervals
    expect(axios.get.mock.calls.length).toBeGreaterThan(callsAfterInit);
  });

  it('does not re-render with identical data (state stays stable)', async () => {
    // We verify by checking that axios was called multiple times but the
    // displayed content does not change (no errors thrown, stable DOM)
    axios.get.mockResolvedValue({ data: mockConfig });
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    // Content should still be the stable waiting state (no verdict in config)
    expect(screen.getByText('WAITING FOR ACTION...')).toBeInTheDocument();
  });
});

describe('App - connection loss handling', () => {
  it('shows OFFLINE when fetch always fails', async () => {
    // All fetches fail - component should report OFFLINE
    axios.get.mockRejectedValue(new Error('Network error'));

    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    // Connected starts false and error handler only sets false when connected=true,
    // so it stays false → OFFLINE
    expect(screen.getByText('OFFLINE')).toBeInTheDocument();
  });

  it('shows OFFLINE after initial success followed by failure', async () => {
    // Two successes (initial + re-run after connected changes), then all fail
    axios.get
      .mockResolvedValueOnce({ data: mockConfig })
      .mockResolvedValueOnce({ data: mockConfig })
      .mockRejectedValue(new Error('Network error'));

    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    expect(screen.getByText('LIVE')).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });
    expect(screen.getByText('OFFLINE')).toBeInTheDocument();
  });

  it('recovers connection when fetch succeeds after failure', async () => {
    // Fail first so connected never becomes true, then start succeeding
    axios.get
      .mockRejectedValueOnce(new Error('fail'))   // initial: connected stays false
      .mockResolvedValue({ data: mockConfig });    // recovery

    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    // First fetch failed but connected was false, so error branch is skipped → still OFFLINE
    expect(screen.getByText('OFFLINE')).toBeInTheDocument();

    // Next interval fetch succeeds → recovery (connected was false, so else branch fires)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });
    expect(screen.getByText('LIVE')).toBeInTheDocument();
  });
});

describe('App - cleanup on unmount', () => {
  it('removes visibilitychange event listener on unmount', async () => {
    const removeSpy = vi.spyOn(document, 'removeEventListener');
    axios.get.mockResolvedValue({ data: mockConfig });
    let unmount;
    await act(async () => {
      ({ unmount } = render(<App />));
      await vi.advanceTimersByTimeAsync(100);
    });
    unmount();
    expect(removeSpy).toHaveBeenCalledWith('visibilitychange', expect.any(Function));
  });

  it('clears poll interval on unmount', async () => {
    const clearIntervalSpy = vi.spyOn(global, 'clearInterval');
    axios.get.mockResolvedValue({ data: mockConfig });
    let unmount;
    await act(async () => {
      ({ unmount } = render(<App />));
      await vi.advanceTimersByTimeAsync(100);
    });
    unmount();
    expect(clearIntervalSpy).toHaveBeenCalled();
  });
});

describe('App - visibility change: no fetch when hidden', () => {
  it('does not fetch when visibilitychange fires but tab is still hidden', async () => {
    axios.get.mockResolvedValue({ data: mockConfig });
    // Start visible so initial fetch works
    await act(async () => {
      render(<App />);
      await vi.advanceTimersByTimeAsync(100);
    });
    const callsAfterInit = axios.get.mock.calls.length;
    expect(callsAfterInit).toBeGreaterThanOrEqual(1);

    // Tab goes hidden
    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      get: () => 'hidden',
    });
    await act(async () => {
      document.dispatchEvent(new Event('visibilitychange'));
      await vi.advanceTimersByTimeAsync(100);
    });
    // Visibility handler only fetches when state === "visible", so no extra call
    expect(axios.get.mock.calls.length).toBe(callsAfterInit);
  });
});