import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import App_Tw from './App_TW'; // 您的台語版本App

function Router() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/tw" element={<App_Tw />} />
      </Routes>
    </BrowserRouter>
  );
}

export default Router;
