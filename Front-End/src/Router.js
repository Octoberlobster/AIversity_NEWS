import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import EventDetail from './EventDetail';
import { SupabaseProvider } from './supabase';

function Router() {
  return (
    <BrowserRouter>
      <SupabaseProvider>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/event/:eventId" element={<EventDetail />} />
        </Routes>
      </SupabaseProvider>
    </BrowserRouter>
  );
}

export default Router;
