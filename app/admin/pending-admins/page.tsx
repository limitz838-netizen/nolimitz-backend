"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, UserCheck, Power, RefreshCw, ArrowLeft, CheckCircle, XCircle } from "lucide-react";
import {
  getAdminToken,
  getApiBaseUrl,
  removeAdminToken,
} from "@/lib/admin-auth";

type AdminItem = {
  admin_id: number;
  full_name: string;
  email: string;
  role: string;
  is_approved: boolean;
  is_active: boolean;
};

export default function AdminManagementPage() {
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [admins, setAdmins] = useState<AdminItem[]>([]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setErrorMessage("");

      const token = getAdminToken();
      if (!token) {
        router.replace("/admin/login");
        return;
      }

      const res = await fetch(`${getApiBaseUrl()}/admin/all-admins`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        cache: "no-store",
      });

      if (res.status === 401) {
        removeAdminToken();
        router.replace("/admin/login");
        return;
      }

      if (res.status === 403) {
        router.replace("/admin/dashboard");
        return;
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail || "Failed to load admins.");
      }

      const data = await res.json();
      setAdmins(Array.isArray(data) ? data : []);
    } catch (error: any) {
      setErrorMessage(error?.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }, [router]);

  const handleApprove = async (adminId: number) => {
    try {
      setActionId(adminId);
      setErrorMessage("");
      setSuccessMessage("");

      const token = getAdminToken();
      const res = await fetch(`${getApiBaseUrl()}/admin/approve/${adminId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to approve admin.");
      }

      setSuccessMessage("Admin approved successfully!");
      await loadData();
      setTimeout(() => setSuccessMessage(""), 4000);
    } catch (error: any) {
      setErrorMessage(error?.message || "Approval failed.");
    } finally {
      setActionId(null);
    }
  };

  const handleDeactivate = async (adminId: number) => {
    try {
      setActionId(adminId);
      setErrorMessage("");
      setSuccessMessage("");

      const token = getAdminToken();
      const res = await fetch(`${getApiBaseUrl()}/admin/deactivate/${adminId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to deactivate admin.");
      }

      setSuccessMessage("Admin deactivated successfully!");
      await loadData();
      setTimeout(() => setSuccessMessage(""), 4000);
    } catch (error: any) {
      setErrorMessage(error?.message || "Deactivation failed.");
    } finally {
      setActionId(null);
    }
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

  const pendingAdmins = admins.filter(admin => !admin.is_approved);
  const approvedAdmins = admins.filter(admin => admin.is_approved);
  const sortedAdmins = [...pendingAdmins, ...approvedAdmins];

  return (
    <main className="min-h-screen bg-[#020817] px-4 py-8 text-white">
      <div className="mx-auto max-w-7xl">
        <div className="rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-2xl">
          {/* Header with Small Back Arrow */}
          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan-400/30 bg-white/5">
                <ShieldCheck className="h-7 w-7 text-cyan-300" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Admin Management</h1>
                <p className="text-white/60">Manage approvals and account status for all administrators</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Small Back to Dashboard Button */}
              <button
                onClick={() => router.push("/admin/dashboard")}
                className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white/80 transition hover:bg-white/10 hover:text-white"
                title="Back to Dashboard"
              >
                <ArrowLeft className="h-4 w-4" />
                <span className="hidden sm:inline">Dashboard</span>
              </button>

              {/* Refresh Button */}
              <button
                onClick={loadData}
                disabled={loading}
                className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm hover:bg-white/10 transition disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                <span className="hidden sm:inline">Refresh</span>
              </button>
            </div>
          </div>

          {/* Messages */}
          {errorMessage && (
            <div className="mb-6 rounded-2xl border border-red-400/30 bg-red-500/10 px-5 py-4 text-sm text-red-200">
              {errorMessage}
            </div>
          )}

          {successMessage && (
            <div className="mb-6 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-5 py-4 text-sm text-emerald-200">
              {successMessage}
            </div>
          )}

          {loading ? (
            <div className="rounded-2xl border border-white/10 bg-white/5 py-20 text-center">
              <div className="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent" />
              <p className="mt-5 text-white/70">Loading admin records...</p>
            </div>
          ) : (
            <>
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-2xl font-semibold">All Administrators</h2>
                <div className="text-sm text-white/50">
                  {sortedAdmins.length} total • {pendingAdmins.length} pending
                </div>
              </div>

              <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/5">
                {/* Table Header */}
                <div className="grid grid-cols-1 gap-4 border-b border-white/10 px-6 py-5 text-xs font-semibold uppercase tracking-widest text-white/40 md:grid-cols-12 md:items-center">
                  <div className="md:col-span-4">Admin Details</div>
                  <div className="md:col-span-2">Role</div>
                  <div className="md:col-span-2 text-center">Approval Status</div>
                  <div className="md:col-span-2 text-center">Account Status</div>
                  <div className="md:col-span-2 text-center">Actions</div>
                </div>

                {/* Table Body */}
                <div className="divide-y divide-white/10">
                  {sortedAdmins.length === 0 ? (
                    <div className="px-6 py-16 text-center text-white/60">
                      No administrators found in the system.
                    </div>
                  ) : (
                    sortedAdmins.map((admin) => {
                      const isPending = !admin.is_approved;
                      const isProcessing = actionId === admin.admin_id;

                      return (
                        <div
                          key={admin.admin_id}
                          className="grid grid-cols-1 gap-4 px-6 py-6 md:grid-cols-12 md:items-center hover:bg-white/5 transition"
                        >
                          {/* Admin Details */}
                          <div className="md:col-span-4">
                            <div className="flex items-center gap-3">
                              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5">
                                {isPending ? (
                                  <UserCheck className="h-5 w-5 text-amber-400" />
                                ) : (
                                  <ShieldCheck className="h-5 w-5 text-cyan-400" />
                                )}
                              </div>
                              <div>
                                <p className="font-semibold text-white">{admin.full_name}</p>
                                <p className="text-sm text-white/65">{admin.email}</p>
                              </div>
                            </div>
                          </div>

                          {/* Role */}
                          <div className="md:col-span-2">
                            <span className="inline-block rounded-full bg-white/10 px-4 py-1 text-sm capitalize">
                              {admin.role.replace("_", " ")}
                            </span>
                          </div>

                          {/* Approval Status */}
                          <div className="md:col-span-2 text-center">
                            <span
                              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1 text-sm font-medium ${
                                admin.is_approved
                                  ? "bg-emerald-500/10 text-emerald-300 border border-emerald-400/30"
                                  : "bg-amber-500/10 text-amber-300 border border-amber-400/30"
                              }`}
                            >
                              {admin.is_approved ? (
                                <>
                                  <CheckCircle className="h-4 w-4" /> Approved
                                </>
                              ) : (
                                <>
                                  <XCircle className="h-4 w-4" /> Pending
                                </>
                              )}
                            </span>
                          </div>

                          {/* Account Status */}
                          <div className="md:col-span-2 text-center">
                            <span
                              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1 text-sm font-medium ${
                                admin.is_active
                                  ? "bg-cyan-500/10 text-cyan-300 border border-cyan-400/30"
                                  : "bg-red-500/10 text-red-300 border border-red-400/30"
                              }`}
                            >
                              {admin.is_active ? "Active" : "Deactivated"}
                            </span>
                          </div>

                          {/* Actions */}
                          <div className="md:col-span-2 flex flex-col gap-2 md:flex-row md:justify-end">
                            {!admin.is_approved ? (
                              <button
                                onClick={() => handleApprove(admin.admin_id)}
                                disabled={isProcessing}
                                className="rounded-2xl bg-gradient-to-r from-cyan-400 to-blue-500 px-6 py-3 text-sm font-bold text-slate-950 hover:brightness-110 disabled:opacity-70 transition"
                              >
                                {isProcessing ? "Approving..." : "Approve"}
                              </button>
                            ) : admin.role !== "super_admin" && admin.is_active ? (
                              <button
                                onClick={() => handleDeactivate(admin.admin_id)}
                                disabled={isProcessing}
                                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-red-400/30 bg-red-500/10 px-6 py-3 text-sm font-bold text-red-200 hover:bg-red-500/20 disabled:opacity-70 transition"
                              >
                                <Power className="h-4 w-4" />
                                {isProcessing ? "Deactivating..." : "Deactivate"}
                              </button>
                            ) : (
                              <div className="rounded-2xl bg-white/5 px-6 py-3 text-center text-sm text-white/40">
                                {admin.role === "super_admin" ? "Super Admin" : "No Action"}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Optional larger back button at bottom (kept for convenience) */}
              <div className="mt-10 hidden md:block">
                <button
                  onClick={() => router.push("/admin/dashboard")}
                  className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-6 py-3 text-sm text-white/80 transition hover:bg-white/10"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to Dashboard
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}