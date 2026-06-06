import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { LangProvider } from "@/contexts/LangContext";
import { SettingsProvider } from "@/contexts/SettingsContext";
import { AuthProvider } from "@/contexts/AuthContext";
import Home from "@/pages/Home";
import AdminLogin from "@/pages/AdminLogin";
import AdminDashboard from "@/pages/AdminDashboard";

function App() {
  return (
    <div className="App">
      <LangProvider>
        <SettingsProvider>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/admin" element={<AdminDashboard />} />
                <Route path="/admin/login" element={<AdminLogin />} />
              </Routes>
            </BrowserRouter>
            <Toaster position="top-center" richColors closeButton />
          </AuthProvider>
        </SettingsProvider>
      </LangProvider>
    </div>
  );
}

export default App;
