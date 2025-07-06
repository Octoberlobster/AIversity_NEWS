import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import EventDetail from './EventDetail';
import NewsCategory from './News_category';
import { SupabaseProvider } from './supabase';
import SearchResults from './SearchResults';

function Router() {
  return (
    <BrowserRouter>
      <SupabaseProvider>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/event/:eventId" element={<EventDetail />} />
          <Route path="/category/:type" element={<NewsCategory />} />
          <Route path="/search/:query" element={<SearchResults />} />
        </Routes>
      </SupabaseProvider>
    </BrowserRouter>
  );
}

export default Router;
