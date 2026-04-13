"use client"

import { useState } from "react"
import { Download, Menu, X, Smartphone, Apple } from "lucide-react"

export default function HomePage() {
  const [open, setOpen] = useState(false)

  return (
    <main className="min-h-screen bg-[#020817] text-white">

      {/* HEADER */}
      <header className="border-b border-white/10">
        <div className="max-w-6xl mx-auto flex justify-between items-center px-4 py-4">

          {/* LOGO */}
          <div>
            <h1 className="text-xl font-bold">
              Nolimitz<span className="text-cyan-400">Bots</span>
            </h1>
            <p className="text-xs text-white/50">Forex Automation Platform</p>
          </div>

          {/* MENU BUTTON */}
          <button
            onClick={() => setOpen(!open)}
            className="p-2 rounded-lg bg-white/5 border border-white/10"
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>

        </div>

        {/* DROPDOWN MENU */}
        {open && (
          <div className="px-4 pb-4">
            <div className="bg-[#020817] border border-white/10 rounded-xl p-4 space-y-3">

              <a href="/admin/login" className="block text-sm">
                Admin Login
              </a>

              <a href="/admin/signup" className="block text-sm">
                Admin Sign Up
              </a>

              <a href="#" className="block text-sm text-cyan-400">
                Download Android
              </a>

              <a href="#" className="block text-sm text-cyan-400">
                Download iOS
              </a>

            </div>
          </div>
        )}
      </header>

      {/* HERO */}
      <section className="text-center px-4 py-20 max-w-4xl mx-auto">

        {/* HEADER TEXT */}
        <h2 className="text-4xl md:text-5xl font-bold leading-tight">
          Smart Forex Trading
          <br />
          <span className="text-cyan-400">Automation Robot</span>
        </h2>

        <p className="mt-6 text-white/60 text-lg">
          Connect your account, receive trades, and let the system handle execution automatically.
        </p>

        {/* BUTTONS */}
        <div className="mt-10 flex flex-col items-center gap-4">

          {/* ANDROID */}
          <a
            href="/download/android.apk"
            className="flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-semibold text-sm"
          >
            <Smartphone size={18} />
            Download Android
          </a>

          {/* IOS */}
          <button
            onClick={() => alert("iOS version coming soon 🚀")}
            className="flex items-center gap-2 px-6 py-3 rounded-lg border border-white/20 text-sm"
          >
            <Apple size={18} />
            Download iOS
          </button>

          {/* TELEGRAM */}
          <a
            href="https://t.me/yourchannel"
            target="_blank"
            className="text-sm text-cyan-400 underline"
          >
            Join Telegram Channel
          </a>

        </div>

      </section>

      {/* FEATURES */}
      <section className="max-w-5xl mx-auto px-4 py-16 grid md:grid-cols-3 gap-8 text-center">

        <div className="space-y-2">
          <Download className="mx-auto text-cyan-400" />
          <h3 className="font-semibold">Instant Setup</h3>
          <p className="text-sm text-white/60">
            Start trading within minutes after setup.
          </p>
        </div>

        <div className="space-y-2">
          <Smartphone className="mx-auto text-cyan-400" />
          <h3 className="font-semibold">Mobile Control</h3>
          <p className="text-sm text-white/60">
            Manage trades directly from your phone.
          </p>
        </div>

        <div className="space-y-2">
          <Download className="mx-auto text-cyan-400" />
          <h3 className="font-semibold">Auto Execution</h3>
          <p className="text-sm text-white/60">
            Trades are executed automatically without delay.
          </p>
        </div>

      </section>

      {/* HOW IT WORKS */}
      <section className="text-center px-4 py-20 max-w-3xl mx-auto">

        <h3 className="text-2xl font-bold">How It Works</h3>

        <p className="mt-6 text-white/60">
          Download the app, connect your trading account, and start receiving trades.
          NolimitzBots executes everything automatically.
        </p>

      </section>

      {/* CTA */}
      <section className="text-center py-16">

        <h3 className="text-xl font-semibold">
          Start Trading Smarter Today
        </h3>

        <div className="mt-6">
          <a
            href="/download/android.apk"
            className="px-6 py-3 rounded-lg bg-cyan-400 text-black text-sm font-semibold"
          >
            Download App
          </a>
        </div>

      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/10 text-center py-6 text-sm text-white/40">
        © 2026 NolimitzBots. All rights reserved.
      </footer>

    </main>
  )
}