"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  ShieldCheck,
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Loader2,
} from "lucide-react";
import { getApiBaseUrl } from "@/lib/admin-auth";

export default function AdminSignupPage() {
  const router = useRouter();

  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Enhanced input wrapper with better focus states
  const inputWrap = (name: string) =>
    `group flex h-12 items-center rounded-2xl border px-4 transition-all duration-300 ${
      focusedField === name
        ? "border-cyan-400/70 bg-white/10 shadow-[0_0_0_1px_rgba(103,232,249,0.3),0_0_30px_rgba(34,211,238,0.2)]"
        : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/[0.07]"
    }`;

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Basic client-side validation
    if (!fullName.trim() || !email.trim() || !password.trim()) {
      setErrorMessage("All fields are required.");
      return;
    }

    if (password.length < 8) {
      setErrorMessage("Password must be at least 8 characters long.");
      return;
    }

    setErrorMessage("");
    setSuccessMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${getApiBaseUrl()}/admin/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: email.trim().toLowerCase(),
          password: password.trim(),
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.detail || data?.message || "Failed to create account. Please try again."
        );
      }

      setSuccessMessage(
        "Account created successfully! Your account is pending super admin approval."
      );

      // Clear form
      setFullName("");
      setEmail("");
      setPassword("");

      // Redirect to login after success
      setTimeout(() => {
        router.push("/admin/login");
      }, 2800);
    } catch (error: any) {
      setErrorMessage(
        error?.message || "Something went wrong. Please check your connection and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen overflow-hidden bg-[#020817] text-white">
      <div className="relative min-h-screen bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.14),transparent_30%),linear-gradient(180deg,#020817_0%,#08142e_50%,#0a1f44_100%)] px-4 py-6">
        {/* Background glows */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute left-[-120px] top-20 h-72 w-72 rounded-full bg-cyan-400/10 blur-3xl" />
          <div className="absolute right-[-100px] top-40 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
          <div className="absolute bottom-0 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-violet-500/10 blur-3xl" />
        </div>

        <div className="relative mx-auto flex min-h-screen w-full max-w-[380px] items-center justify-center">
          <div className="w-full rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl backdrop-blur-2xl">
            {/* Header */}
            <div className="mb-8 flex flex-col items-center text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan-400/30 bg-white/5 shadow-[0_0_30px_rgba(34,211,238,0.12)]">
                <ShieldCheck className="h-8 w-8 text-cyan-300" />
              </div>

              <h1 className="bg-gradient-to-r from-cyan-300 via-sky-400 to-blue-500 bg-clip-text text-4xl font-black tracking-tighter text-transparent">
                NolimitzBots
              </h1>
              <p className="mt-1 text-sm font-medium text-white/60">Admin Portal</p>
            </div>

            {/* Form Card */}
            <div className="rounded-3xl border border-white/10 bg-white/5 p-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-xl">
              <h2 className="text-2xl font-bold tracking-tight">Create account</h2>
              <p className="mt-2 text-sm text-white/70">
                Register as an administrator. Your account will require super admin approval.
              </p>

              <form onSubmit={handleSubmit} className="mt-8 space-y-6">
                {/* Full Name */}
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-white/90">Full Name</label>
                  <div className={inputWrap("full_name")}>
                    <User className="mr-3 h-5 w-5 text-cyan-300/80" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="John Doe"
                      className="flex-1 bg-transparent text-base outline-none placeholder:text-white/40"
                      onFocus={() => setFocusedField("full_name")}
                      onBlur={() => setFocusedField(null)}
                      disabled={loading}
                    />
                  </div>
                </div>

                {/* Email */}
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-white/90">Email Address</label>
                  <div className={inputWrap("email")}>
                    <Mail className="mr-3 h-5 w-5 text-cyan-300/80" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="admin@nolimitzbots.com"
                      className="flex-1 bg-transparent text-base outline-none placeholder:text-white/40"
                      onFocus={() => setFocusedField("email")}
                      onBlur={() => setFocusedField(null)}
                      disabled={loading}
                    />
                  </div>
                </div>

                {/* Password */}
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-white/90">Password</label>
                  <div className={inputWrap("password")}>
                    <Lock className="mr-3 h-5 w-5 text-cyan-300/80" />
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Create a strong password"
                      className="flex-1 bg-transparent text-base outline-none placeholder:text-white/40"
                      onFocus={() => setFocusedField("password")}
                      onBlur={() => setFocusedField(null)}
                      disabled={loading}
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => !prev)}
                      className="ml-2 text-white/60 transition-colors hover:text-cyan-300"
                      disabled={loading}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                {/* Messages */}
                {errorMessage && (
                  <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {errorMessage}
                  </div>
                )}

                {successMessage && (
                  <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                    {successMessage}
                  </div>
                )}

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={loading}
                  className="mt-2 flex h-12 w-full items-center justify-center rounded-2xl bg-gradient-to-r from-cyan-400 via-blue-500 to-cyan-300 text-base font-bold text-slate-950 shadow-[0_0_30px_rgba(56,189,248,0.3)] transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_50px_rgba(56,189,248,0.5)] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Creating Account...
                    </>
                  ) : (
                    "Create Admin Account"
                  )}
                </button>
              </form>

              {/* Links */}
              <div className="mt-8 text-center">
                <p className="text-sm text-white/60">
                  Already have an account?{" "}
                  <Link
                    href="/admin/login"
                    className="font-semibold text-cyan-400 transition-colors hover:text-cyan-300"
                  >
                    Sign in
                  </Link>
                </p>
              </div>

              <div className="mt-8 flex items-center justify-center gap-3 text-xs text-white/40">
                <div className="h-px flex-1 bg-white/10" />
                <span>Approval required</span>
                <div className="h-px flex-1 bg-white/10" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}