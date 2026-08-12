import { render, screen, fireEvent } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import { expect, test } from 'vitest';
import React from 'react';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <div data-testid="redirect">Redirected to /ingest</div>;
};

const TestComponent = () => {
  const { login } = useAuth();
  const [navigated, setNavigated] = React.useState(false);
  
  const handleLoginAndNavigate = () => {
    login('test-token', 'test@example.com');
    setNavigated(true);
  };

  if (navigated) {
    return <ProtectedRoute><div data-testid="success">Success</div></ProtectedRoute>;
  }

  return (
    <button onClick={handleLoginAndNavigate}>Login</button>
  );
};

test('isAuthenticated is true during the immediate render after login', async () => {
  localStorage.clear();

  render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );

  fireEvent.click(screen.getByText('Login'));

  expect(screen.queryByTestId('redirect')).toBeNull();
  expect(screen.queryByTestId('success')).not.toBeNull();
});
