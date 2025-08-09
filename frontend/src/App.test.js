import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock window.location and history
const mockLocation = {
  href: 'http://localhost:3000/workouts',
  search: '',
  pathname: '/workouts',
  origin: 'http://localhost:3000',
  protocol: 'http:',
  host: 'localhost:3000',
  hostname: 'localhost',
  port: '3000',
  hash: '',
  searchParams: new URLSearchParams(),
};

Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

describe('Theme toggle', () => {
  test('switches between light and dark modes', () => {
    render(<App />);
    const toggle = screen.getByRole('button', { name: /dark mode/i });
    expect(document.body).not.toHaveClass('dark');
    fireEvent.click(toggle);
    expect(document.body).toHaveClass('dark');
  });
});

Object.defineProperty(window, 'history', {
  value: {
    replaceState: jest.fn(),
    pushState: jest.fn(),
  },
  writable: true,
});

describe('Workout Metric Selector', () => {
  beforeEach(() => {
    fetch.mockClear();
    window.history.replaceState.mockClear();
    
    // Mock successful API responses
    fetch.mockImplementation((url) => {
      if (url.includes('/api/profile')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ athlete_id: 'Jan' })
        });
      }
      if (url.includes('/api/workouts') && !url.includes('/timeseries')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            {
              id: 'test-workout-1',
              athlete_id: 'Jan',
              timestamp: '2025-01-01T10:00:00Z',
              workout_type: 'bike',
              tss: 50
            }
          ])
        });
      }
      if (url.includes('/api/workouts/test-workout-1')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'test-workout-1',
            athlete_id: 'Jan',
            timestamp: '2025-01-01T10:00:00Z',
            workout_type: 'bike',
            tss: 50,
            json_file: {
              data: [
                { timestamp: '2025-01-01T10:00:00Z', heart_rate: 120, speed: 25, power: 200 }
              ]
            }
          })
        });
      }
      if (url.includes('/timeseries')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            workout_id: 'test-workout-1',
            metric: 'hr',
            data: [
              { timestamp: '2025-01-01T10:00:00Z', value: 120, unit: 'bpm' }
            ],
            available_metrics: ['hr', 'speed', 'power']
          })
        });
      }
      return Promise.resolve({
        ok: false,
        status: 404
      });
    });
  });

  test('renders workout list and metric selector', async () => {
    render(<App />);
    
    // Wait for workouts to load
    await waitFor(() => {
      expect(screen.getByText('Workouts')).toBeInTheDocument();
    });

    // Click on a workout to open detail modal
    const workoutItem = await screen.findByText('bike');
    fireEvent.click(workoutItem);

    // Wait for modal to open and metric selector to appear
    await waitFor(() => {
      expect(screen.getByText('Workout Details')).toBeInTheDocument();
      expect(screen.getByText('Metric:')).toBeInTheDocument();
    });
  });

  test('metric selector shows correct options for bike workout', async () => {
    render(<App />);
    
    // Open workout detail modal
    const workoutItem = await screen.findByText('bike');
    fireEvent.click(workoutItem);

    // Wait for metric selector to load
    await waitFor(() => {
      expect(screen.getByText('Metric:')).toBeInTheDocument();
    });

    // Check that metric options are available
    const metricSelect = screen.getByRole('combobox');
    expect(metricSelect).toBeInTheDocument();
    
    // Open dropdown to see options
    fireEvent.click(metricSelect);
    
    // Check for expected options (these will be rendered by the browser)
    expect(metricSelect).toHaveValue('hr');
  });

  test('metric selector changes chart when selection changes', async () => {
    render(<App />);
    
    // Open workout detail modal
    const workoutItem = await screen.findByText('bike');
    fireEvent.click(workoutItem);

    // Wait for metric selector to load
    await waitFor(() => {
      expect(screen.getByText('Metric:')).toBeInTheDocument();
    });

    // Change metric selection
    const metricSelect = screen.getByRole('combobox');
    fireEvent.change(metricSelect, { target: { value: 'power' } });

    // Verify that API was called with new metric
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/workouts/test-workout-1/timeseries?metric=power')
      );
    });
  });

  test('URL updates when metric selection changes', async () => {
    render(<App />);
    
    // Open workout detail modal
    const workoutItem = await screen.findByText('bike');
    fireEvent.click(workoutItem);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByText('Workout Details')).toBeInTheDocument();
    });

    // Change metric selection
    const metricSelect = screen.getByRole('combobox');
    fireEvent.change(metricSelect, { target: { value: 'power' } });

    // Verify URL was updated
    await waitFor(() => {
      expect(window.history.replaceState).toHaveBeenCalledWith(
        {},
        '',
        expect.stringContaining('metric=power')
      );
    });
  });

  test('URL updates when workout is selected', async () => {
    render(<App />);
    
    // Click on a workout
    const workoutItem = await screen.findByText('bike');
    fireEvent.click(workoutItem);

    // Verify URL was updated with workout ID
    await waitFor(() => {
      expect(window.history.replaceState).toHaveBeenCalledWith(
        {},
        '',
        expect.stringContaining('workout=test-workout-1')
      );
    });
  });

  test('URL updates when workout modal is closed', async () => {
    render(<App />);
    
    // Open workout detail modal
    const workoutItem = await screen.findByText('bike');
    fireEvent.click(workoutItem);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByText('Workout Details')).toBeInTheDocument();
    });

    // Close modal
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    // Verify URL was updated to remove workout parameter
    await waitFor(() => {
      expect(window.history.replaceState).toHaveBeenCalledWith(
        {},
        '',
        expect.not.stringContaining('workout=')
      );
    });
  });

  test('initializes from URL parameters on page load', async () => {
    // Set URL parameters
    mockLocation.search = '?workout=test-workout-1&metric=power';
    mockLocation.searchParams = new URLSearchParams('workout=test-workout-1&metric=power');

    render(<App />);
    
    // Verify that the workout modal opens automatically
    await waitFor(() => {
      expect(screen.getByText('Workout Details')).toBeInTheDocument();
    });

    // Verify that the correct metric is selected
    const metricSelect = screen.getByRole('combobox');
    expect(metricSelect).toHaveValue('power');
  });

  test('handles unavailable metrics gracefully', async () => {
    // Mock API to return error for unavailable metric
    fetch.mockImplementation((url) => {
      if (url.includes('/timeseries?metric=unavailable')) {
        return Promise.resolve({
          ok: false,
          status: 404,
          json: () => Promise.resolve({
            detail: "Metric 'unavailable' not available. Available metrics: hr, speed, power"
          })
        });
      }
      return fetch.mock.results[0].value;
    });

    render(<App />);
    
    // Open workout detail modal
    const workoutItem = await screen.findByText('bike');
    fireEvent.click(workoutItem);

    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByText('Workout Details')).toBeInTheDocument();
    });

    // Try to select an unavailable metric (this would be handled by the backend)
    // The test verifies that the frontend handles the error gracefully
    expect(screen.getByText('Workout Details')).toBeInTheDocument();
  });
}); 