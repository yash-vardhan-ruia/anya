'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-zinc-950 font-sans flex flex-col overflow-x-hidden selection:bg-blue-500/10 selection:text-blue-500">
      {/* Glow aesthetic backgrounds */}
      <div className="absolute top-0 right-0 -z-10 opacity-30 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-10 left-1/4 w-[400px] h-[400px] bg-indigo-500/5 rounded-full blur-[100px] pointer-events-none"></div>

      {/* ── Header Navbar ── */}
      <header className="fixed top-0 left-0 w-full h-16 flex justify-between items-center px-6 md:px-12 bg-white/80 dark:bg-zinc-900/80 border-b border-slate-200 dark:border-zinc-800 backdrop-blur-md z-50 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-voxmed-primary rounded-lg flex items-center justify-center text-white font-bold shadow-lg shadow-voxmed-primary/20">
            V
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-tight text-slate-900 dark:text-white leading-none">VoxMed AI</span>
            <span className="text-[10px] text-emerald-500 font-medium tracking-wide mt-1 animate-pulse">
              Anya Core Operational
            </span>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-8">
          <nav className="flex gap-6 text-sm font-medium">
            <Link href="/" className="text-voxmed-primary font-bold border-b-2 border-voxmed-primary py-1 transition-all">
              Home
            </Link>
            <Link href="/calls" className="text-muted-foreground hover:text-slate-900 dark:hover:text-white transition-colors">
              Voice Booking
            </Link>
          </nav>
          <div className="flex items-center gap-4">
            <div className="h-8 w-[1px] bg-slate-200 dark:bg-zinc-800 mx-2"></div>
            <Link href="/login" className="text-sm font-semibold text-voxmed-primary hover:underline flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px]">admin_panel_settings</span>
              Staff Login
            </Link>
          </div>
        </div>
      </header>

      {/* ── Main Layout ── */}
      <main className="pt-16 flex-1 flex flex-col">
        {/* Hero Section */}
        <section className="relative px-6 py-12 md:py-24 max-w-7xl mx-auto w-full">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left side text and CTA */}
            <div className="space-y-8">
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-voxmed-primary/10 border border-voxmed-primary/25 text-voxmed-primary text-xs font-bold uppercase tracking-wider">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-voxmed-primary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-voxmed-primary"></span>
                </span>
                Next-Gen Patient Experience
              </div>

              <h1 className="text-5xl md:text-7xl font-extrabold text-slate-900 dark:text-white leading-[1.1] tracking-tight">
                Anya <span className="bg-gradient-to-r from-voxmed-primary to-indigo-500 bg-clip-text text-transparent">CareVoice</span> AI
              </h1>

              <p className="text-lg md:text-xl text-muted-foreground max-w-xl leading-relaxed">
                Transform your hospital reception with our clinical-grade voice intelligence. Effortless bookings, instant triage support, and seamless integration with your existing EMR.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/calls">
                  <Button size="lg" className="w-full sm:w-auto px-8 py-6 bg-voxmed-primary text-white hover:bg-voxmed-primary/90 rounded-xl font-bold text-lg shadow-lg shadow-voxmed-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3 group">
                    Start Voice Booking
                    <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">keyboard_double_arrow_right</span>
                  </Button>
                </Link>
                <Link href="/login">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto px-8 py-6 border-slate-200 dark:border-zinc-800 text-slate-700 dark:text-zinc-300 font-bold rounded-xl hover:bg-white dark:hover:bg-zinc-800 transition-colors flex items-center justify-center gap-2">
                    <span className="material-symbols-outlined">dashboard</span>
                    Staff Portal
                  </Button>
                </Link>
              </div>

              <div className="flex items-center gap-6 pt-4">
                <div className="flex -space-x-3">
                  <img className="w-10 h-10 rounded-full border-2 border-white dark:border-zinc-900 object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAbZQg_4yBSBOIOxayB4EkWZ48b0B_3jkNhRmoChwliC7PV-dh92rgSRXyG4w7Haf249vT6lPOKRBcsFU4QlJZwZaaw7KdCqyMGp3rqcJVmuBM7l2IOzQjV4bFiOBoMUhNs_H0pQ-r5_LmgbzpfF1lQcvN4uYX7HW56moEF124YDsFTKwn5qjofo1oEWEPOUB3Hraj8UuHPmUaOFvYoBHPgoaBen9IcyePAkuq2AkJAbpB6I-M43EYF5HZoqCVSXtRzpLbbGI9vuw" alt="Doctor Priya" />
                  <img className="w-10 h-10 rounded-full border-2 border-white dark:border-zinc-900 object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBZkYxSaZAR7g-SO9OI93_9PcsSumdA0mtFtgfcWLI6m_fgKb0QQe1myui-YbQx1-z2d5ME25_LUfxc6mADL_jFeZSYcynt0SEHG1d-b3m54akhTGUMtfNcjJ5VSvBU-_7covI-EKHTBrdnwTK9WRLH0c_JmgvWyw6PeWhWojmFTszmWfqT0op1RDa_6vEoPbZnvDagJIH1ZKlIsaAaoXBQ3sQeVKF7H1W-rTpEC0FojmKoHmuApe7ozpzLgAiyi9Dk-Il7c0UjDA" alt="Doctor Vikram" />
                  <img className="w-10 h-10 rounded-full border-2 border-white dark:border-zinc-900 object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAa6E3QjhTcc60cT8mvZtTzoz1z4Ql1V5VbhxOyV-x-YKZwfzj4QyYmGzGI_qeZHKRLwLx8a1BS7GV3fNhO0mb-9sRxhZUFk90ofeRDuaBMqK7b41vwLDN7j0JJ9t91YzIq5o3uywEpk0nM2r8uKu-1OHjlj2VOiHkFEmMLCQqxnfQJHyfblkDy82A0dq3A0RQwDplYmnSFGnDhsVzkvJUgepzfYCwOTrmutwNIPukD9JXklNwGLemaa6atnOzO4u7lZqE4B5qNAw" alt="Staff Admin" />
                </div>
                <p className="text-sm text-muted-foreground font-medium">Trusted by <span className="text-slate-900 dark:text-white font-bold">500+</span> healthcare providers</p>
              </div>
            </div>

            {/* Right side graphical showcase */}
            <div className="relative lg:h-[600px] flex items-center justify-center">
              <div className="relative w-full aspect-square md:aspect-auto md:h-full max-w-lg lg:max-w-none bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border border-slate-200/50 dark:border-zinc-800 rounded-3xl overflow-hidden shadow-2xl">
                <div className="absolute inset-0 bg-gradient-to-br from-voxmed-primary/10 to-transparent"></div>
                <img className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCcm9ty5DHboK5Qq6M545vTZWw6bEHxBDJh-1k4OyiqkUCRgV99f2DzZnYLuKm6zLu_uHKt6ZAFAFX4vq4QVWevBTniebYqWZr3-GgJ2ClGbxZTlDunVHXP_89sc5s1sxpBEjbx7XZMGYcgGnkCc3AnUmH42XRSjTXGUwkbmjyI--BG3N5kEP5dCkuPPuI2LXLWoBSH_8PI4jM1wIiOT2dtbNc_fdOz5jZVPxrI0ECpukm0YoqcYCnh7wv0pWBJ3ZNyHs0ebTwdAw" alt="Advanced medical portal lobby" />
                
                {/* Floating Micro-UI Cards */}
                <div className="absolute top-8 right-8 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-md border border-slate-200 dark:border-zinc-800 p-4 rounded-2xl shadow-xl animate-bounce duration-[3000ms] flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-500/20 text-green-600 rounded-full flex items-center justify-center">
                    <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-900 dark:text-white">HIPAA Secure</p>
                    <p className="text-[10px] text-muted-foreground">Real-time encryption active</p>
                  </div>
                </div>

                <div className="absolute bottom-8 left-8 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-md border border-slate-200 dark:border-zinc-800 p-4 rounded-2xl shadow-xl flex items-center gap-4 border-l-4 border-voxmed-primary max-w-[240px]">
                  <span className="material-symbols-outlined text-voxmed-primary text-3xl">mic</span>
                  <div className="flex-1">
                    <div className="h-2 w-full bg-slate-200 dark:bg-zinc-800 rounded-full overflow-hidden mb-1">
                      <div className="h-full bg-voxmed-primary w-2/3 animate-pulse"></div>
                    </div>
                    <p className="text-[11px] font-medium text-muted-foreground italic">"Anya, I need to schedule a..."</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Trust Indicators Strip */}
        <section className="bg-slate-900 text-white py-12">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div className="flex flex-col items-center gap-3 p-6 rounded-2xl hover:bg-white/5 transition-colors">
              <span className="material-symbols-outlined text-4xl text-voxmed-primary">neurology</span>
              <h3 className="text-xl font-bold">AI-Powered Booking</h3>
              <p className="text-sm text-slate-400">Intelligent voice recognition that understands clinical terminology with 99% accuracy.</p>
            </div>
            <div className="flex flex-col items-center gap-3 p-6 rounded-2xl hover:bg-white/5 transition-colors">
              <span className="material-symbols-outlined text-4xl text-voxmed-primary">verified_user</span>
              <h3 className="text-xl font-bold">Secure & HIPAA Compliant</h3>
              <p className="text-sm text-slate-400">Enterprise-grade security protocols ensuring patient data privacy and total regulatory compliance.</p>
            </div>
            <div className="flex flex-col items-center gap-3 p-6 rounded-2xl hover:bg-white/5 transition-colors">
              <span className="material-symbols-outlined text-4xl text-voxmed-primary">update</span>
              <h3 className="text-xl font-bold">Available 24/7</h3>
              <p className="text-sm text-slate-400">Your clinic never closes. Let patients book their next visit anytime, day or night, without wait times.</p>
            </div>
          </div>
        </section>

        {/* Features Bento Grid */}
        <section className="py-24 px-6 max-w-7xl mx-auto w-full">
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">Designed for Clinical Excellence</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">Modernizing healthcare interactions through empathetic technology.</p>
          </div>
          
          <div className="grid grid-cols-12 gap-6">
            {/* Large Feature */}
            <div className="col-span-12 lg:col-span-8 h-[400px] relative rounded-[2rem] overflow-hidden group cursor-pointer border border-slate-200 dark:border-zinc-800 shadow-sm">
              <div className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuDLtcq4oKVuyD4xbdLlOxvwXEE1PQ0CPZre9304rJAzm7As8EkRN2Q1Ugf5GOPZsD7hkJLc03qFkVhDyNw4ooAPrKMJxnJL9xJ2ruWG_KueEaOhzBHcDfg26s3TkiASBDidpnfYFyewapAp54x-KpY-lp5bAbVyUjMXpsMgKp0aKn1NiLRR--GMXeq0QuBotwGnDKsDddrpgEkfYCMw685ndtmQsniQ9AwqW2-iQzfmW5wpxHEqwEPk8P-R7RKzs478v9FgpQwqjw')" }}></div>
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent p-8 flex flex-col justify-end">
                <h3 className="text-2xl font-bold text-white mb-2">Seamless EMR Integration</h3>
                <p className="text-white/80 max-w-md text-sm">Connect directly to Epic, Cerner, or Athenahealth. Anya updates patient records in real-time, reducing administrative burden.</p>
              </div>
            </div>

            {/* Small Feature 1 */}
            <div className="col-span-12 md:col-span-6 lg:col-span-4 h-[400px] bg-blue-500/10 p-8 rounded-[2rem] flex flex-col justify-between border border-blue-500/20 shadow-sm">
              <div className="w-14 h-14 bg-white dark:bg-zinc-900 rounded-2xl flex items-center justify-center text-voxmed-primary shadow-sm">
                <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>analytics</span>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Call Analytics</h3>
                <p className="text-muted-foreground text-sm">Gain deep insights into patient needs and peak booking times with automated transcriptions and sentiment analysis.</p>
              </div>
            </div>

            {/* Small Feature 2 */}
            <div className="col-span-12 md:col-span-6 lg:col-span-4 h-[400px] bg-slate-900 text-white p-8 rounded-[2rem] flex flex-col justify-between border border-slate-800 shadow-sm">
              <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center text-white backdrop-blur">
                <span className="material-symbols-outlined text-3xl">record_voice_over</span>
              </div>
              <div>
                <h3 className="text-2xl font-bold mb-2">Natural Triage</h3>
                <p className="text-white/75 text-sm">Our AI identifies urgent medical concerns and can instantly route critical calls to human staff for immediate attention.</p>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="col-span-12 lg:col-span-8 h-[400px] bg-white dark:bg-zinc-900/40 p-8 rounded-[2rem] flex flex-col lg:flex-row gap-8 items-center border border-slate-200 dark:border-zinc-800 shadow-sm">
              <div className="flex-1 space-y-4">
                <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Bilingual Support</h3>
                <p className="text-muted-foreground text-sm">Break language barriers with seamless Hindi and English bilingual support, ensuring all patients feel heard and understood.</p>
                <div className="flex flex-wrap gap-2 pt-2">
                  <span className="px-3.5 py-1.5 bg-slate-100 dark:bg-zinc-800 rounded-full text-xs font-semibold text-slate-700 dark:text-zinc-300">English (Neutral)</span>
                  <span className="px-3.5 py-1.5 bg-slate-100 dark:bg-zinc-800 rounded-full text-xs font-semibold text-slate-700 dark:text-zinc-300">Hindi (Conversational)</span>
                </div>
              </div>
              <div className="flex-1 w-full h-full rounded-2xl overflow-hidden shadow-inner">
                <img className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBJdo77pYfT5QdfaSqMVewzZkTmuF97XFfyeSz4cr1lMDqtCS9FvlPit-hX7Q5h4Hs2WuOJcIdEQGs5eKDleEssXaE9AvlThAv0-nPLPcfkLAx1jMoJWX_HBJhN90D7UwWaqbZSRY_3Z1Q3MgkI6DtvV4-VIevbbDtiC4qTz2G-mDqWiGRSy4w0AVyYRRxpH-P1aDqnqstUTlToYkT0jLE4wFORZF7hMW_jxNXwUfQvDTbePY3P5j-UTU91Bzx3BwifQmqOgoiL5w" alt="Global languages indicator" />
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 px-6 max-w-7xl mx-auto w-full">
          <div className="max-w-5xl mx-auto bg-voxmed-primary rounded-[3rem] p-12 md:p-20 text-center text-white relative overflow-hidden shadow-2xl">
            <div className="absolute inset-0 bg-gradient-to-r from-voxmed-primary to-indigo-700 opacity-60 z-0"></div>
            <div className="relative z-10 space-y-8">
              <h2 className="text-4xl md:text-6xl font-extrabold tracking-tight">Ready to evolve your patient experience?</h2>
              <p className="text-xl text-blue-100/90 max-w-2xl mx-auto">Join the future of healthcare with Anya CareVoice AI. Begin your voice session today.</p>
              <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
                <Link href="/calls">
                  <Button size="lg" className="w-full sm:w-auto px-10 py-7 bg-white hover:bg-slate-50 text-voxmed-primary rounded-2xl font-extrabold text-xl shadow-lg transition-colors">
                    Start Voice Call
                  </Button>
                </Link>
                <Link href="/login">
                  <Button size="lg" className="w-full sm:w-auto px-10 py-7 bg-white/10 hover:bg-white/20 border border-white/20 text-white rounded-2xl font-extrabold text-xl transition-colors">
                    Staff Portal
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="bg-white dark:bg-zinc-900 border-t border-slate-200 dark:border-zinc-800 pt-16 pb-10 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
            <div className="space-y-6">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-voxmed-primary rounded-lg flex items-center justify-center text-white font-bold">
                  V
                </div>
                <span className="text-xl font-bold text-voxmed-primary">VoxMed AI</span>
              </div>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Redefining clinical operations through advanced conversational intelligence.
              </p>
            </div>
            <div>
              <h4 className="font-bold mb-6">Product</h4>
              <ul className="space-y-4 text-sm text-muted-foreground">
                <li><Link href="/calls" className="hover:text-voxmed-primary transition-colors">Voice Assistant</Link></li>
                <li><a className="hover:text-voxmed-primary transition-colors cursor-pointer">Triage Intelligence</a></li>
                <li><a className="hover:text-voxmed-primary transition-colors cursor-pointer">Security &amp; Trust</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-6">Resources</h4>
              <ul className="space-y-4 text-sm text-muted-foreground">
                <li><Link href="/login" className="hover:text-voxmed-primary transition-colors">Staff Login</Link></li>
                <li><a className="hover:text-voxmed-primary transition-colors cursor-pointer">HIPAA Compliance</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-6">Company</h4>
              <ul className="space-y-4 text-sm text-muted-foreground">
                <li><a className="hover:text-voxmed-primary transition-colors cursor-pointer">About Us</a></li>
                <li><a className="hover:text-voxmed-primary transition-colors cursor-pointer">Privacy Policy</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-slate-200 dark:border-zinc-800 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-muted-foreground font-medium">© 2026 VoxMed AI. All rights reserved. Anya CareVoice is a registered trademark.</p>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="material-symbols-outlined text-sm">lock</span>
              HIPAA Compliant Infrastructure
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
