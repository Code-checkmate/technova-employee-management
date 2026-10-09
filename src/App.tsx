/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect } from 'react';

export default function App() {
  useEffect(() => {
    // Redirect root to Flask dashboard
    window.location.replace('/dashboard');
  }, []);

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: '2rem', textAlign: 'center' }}>
      <h2>Loading TechNova Employee Management System...</h2>
      <p>Redirecting to dashboard...</p>
    </div>
  );
}
