"use client";

import Link from "next/link";
import { useState } from "react";
import { Mail, ShieldCheck, ArrowLeft } from "lucide-react";

export default function ForgotPasswordPage() {
  const [focusedField, setFocusedField] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const inputWrap = (name: string) =>
    `flex h-12 items-center rounded-2xl border px-4 transition-all duration-300 ${
      focusedField === name
        ? "border-cyan-400/70 bg-white/10 shadow-[0_0_0_1px_rgba(103,232,249,0.2),0_0_26px_rgba(34,211,238,0.15)]"
        : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/[0.07]"
    }`;

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // TODO: Add your password reset logic here
    setIsSubmitted(true);
    console.log("Password reset link requested");
  };

  return (
    <main className="min-h-screen bg-[#020817] text-white overflow-hidden">
      <div className="relative min-h-screen bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.14),transparent_30%),linear-gradient(180deg,#020817_0%,#08142e_50%,#0a1f44_100%)] px-4 py-6">
        
        <div className="mx-auto flex min-h-screen max-w-[380px] items-center justify-center">
          <div className="w-full rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl backdrop-blur-2xl">
            
            {/* Header */}
            <div className="mb-6 flex flex-col items-center text-center">
              <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-400/30 bg-white/5">
                <ShieldCheck className="h-7 w-7 text-cyan-300" />
              </div>

              <h1 className="bg-gradient-to-r from-cyan-300 via-sky-400 to-blue-500 bg-clip-text text-3xl font-black tracking-tighter text-transparent">
                NolimitzBots
              </h1>
              <p className="mt-1 text-sm font-medium text-white/60">Admin Portal</p>
            </div>

            {/* Form Container */}
            <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-xl">
              
              {!isSubmitted ? (
                <>
                  <h2 className="text-2xl font-bold tracking-tight text-white">
                    Forgot password
                  </h2>

                  <p className="mt-2 text-sm leading-relaxed text-white/70">
                    Enter your admin email and we&apos;ll send you a reset link.
                  </p>

                  <form onSubmit={handleSubmit} className="mt-6 space-y-5">
                    <div className="space-y-1.5">
                      <label className="text-sm font-medium text-white/90">Email Address</label>
                      <div className={inputWrap("email")}>
                        <Mail className="mr-3 h-5 w-5 text-cyan-300/80" />
                        <input
                          type="email"
                          required
                          placeholder="admin@nolimitzbots.com"
                          className="flex-1 bg-transparent text-base text-white outline-none placeholder:text-white/40"
                          onFocus={() => setFocusedField("email")}
                          onBlur={() => setFocusedField(null)}
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="mt-3 flex h-12 w-full items-center justify-center rounded-2xl bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-300 text-base font-bold text-slate-950 shadow-[0_0_30px_rgba(56,189,248,0.28)] transition-all duration-300 hover:scale-[1.015] hover:shadow-[0_0_45px_rgba(56,189,248,0.45)] active:scale-[0.985]"
                    >
                      Send Reset Link
                    </button>
                  </form>

                  {/* Back to Login */}
                  <div className="mt-6 text-center">
                    <Link
                      href="/admin/login"
                      className="inline-flex items-center gap-1.5 text-sm font-medium text-cyan-400 hover:text-cyan-300 transition-colors"
                    >
                      <ArrowLeft className="h-4 w-4" />
                      Back to Login
                    </Link>
                  </div>
                </>
              ) : (
                /* Success State */
                <div className="py-8 text-center">
                  <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full border border-green-500/30 bg-green-500/10">
                    <Mail className="h-8 w-8 text-green-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-white">Check your email</h3>
                  <p className="mt-3 text-sm text-white/70 leading-relaxed">
                    We&apos;ve sent a password reset link to your email.<br />
                    Please check your inbox (and spam folder).
                  </p>

                  <button
                    onClick={() => setIsSubmitted(false)}
                    className="mt-6 text-sm text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
                  >
                    Send another reset link
                  </button>
                </div>
              )}

              {/* Footer Note */}
              <div className="mt-6 flex items-center justify-center gap-2 text-xs text-white/40">
                <div className="h-px w-5 bg-white/10" />
                <span>Secure Password Recovery</span>
                <div className="h-px w-5 bg-white/10" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}