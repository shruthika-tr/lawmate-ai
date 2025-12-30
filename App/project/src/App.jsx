import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Hero, Services as LandingServices, Footer } from "./LandingPage";
import { Header } from "./Header.jsx";
import ServicesPage from "./ServicesPage";
import ServiceChatPage from "./ServiceChatPage";
import LegalProfessionals from "./pages/LegalProfessionals";
import Login from "./Login";
import Signup from "./SignUp";
import ContactUs from "./ContactUs";
import AboutUs from "./AboutUs";
import Resources from "./Resources";
import { supabase } from "./supabase";
import { I18nextProvider } from "react-i18next";
import i18n from "./i18n";

function App() {
  const [user, setUser] = useState(null);
  const apiUrl = import.meta.env.VITE_API_URL;

  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.unsubscribe();
  }, []);

  return (
    <I18nextProvider i18n={i18n}>
      <Router>
        <div className="min-h-screen bg-gradient-to-b from-[#0d0d0d] to-[#121212] text-white flex flex-col">
          <Header user={user} />

          <main className="flex-1">
            <Routes>
              <Route
                path="/"
                element={
                  <>
                    <Hero />
                    <LandingServices />
                  </>
                }
              />
              <Route path="/services" element={<ServicesPage />} />
              <Route
                path="/service-chat/:serviceTitle"
                element={<ServiceChatPage />}
              />
              <Route
                path="/legal_professionals"
                element={<LegalProfessionals />}
              />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/contact" element={<ContactUs />} />
              <Route path="/resources" element={<Resources />} />
              <Route path="/about" element={<AboutUs />} />
            </Routes>
          </main>

          <Footer />
        </div>
      </Router>
    </I18nextProvider>
  );
}

export default App;
