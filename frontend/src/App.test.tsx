import { render, screen } from '@testing-library/react';
import App from './App';

test('renders app', () => {
  render(<App />);
  expect(screen.getByText(/emissions/i)).toBeInTheDocument(); // Adjust to match your app
});
