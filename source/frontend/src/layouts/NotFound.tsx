import React from 'react';

export const NotFound = ({ children }: { children?: React.ReactNode }) => (
  <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
    <div className="w-full max-w-sm">
      {children || (
        <>
          <h1>404 - Page Not Found</h1>
          <p>The page you are looking for does not exist.</p>
        </>
      )}
    </div>
  </div>
);
