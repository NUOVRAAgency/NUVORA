import React from "react";
import Header from "../components/Header";
import Hero from "../components/Hero";
import Portfolio from "../components/Portfolio";
import ConsultationForm from "../components/ConsultationForm";
import Contact from "../components/Contact";
import Footer from "../components/Footer";
import FloatingWhatsApp from "../components/FloatingWhatsApp";

export default function Home() {
  return (
    <div data-testid="home-page" className="min-h-screen">
      <Header />
      <Hero />
      <Portfolio />
      <ConsultationForm />
      <Contact />
      <Footer />
      <FloatingWhatsApp />
    </div>
  );
}
