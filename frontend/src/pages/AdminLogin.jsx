import React, { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { LogIn, Lock } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";

export default function AdminLogin() {
  const nav = useNavigate();
  const { login, user } = useAuth();
  const [email, setEmail] = useState("admin@mergent.com");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/admin" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success("تم تسجيل الدخول");
      nav("/admin");
    } catch (e) {
      const d = e?.response?.data?.detail;
      toast.error(typeof d === "string" ? d : "فشل تسجيل الدخول");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="admin-login-page" className="min-h-screen grid place-items-center bg-[#F6FAFB] p-6">
      <div className="admin-card w-full max-w-md p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-11 h-11 rounded-xl bg-[#0A3D42] text-white grid place-items-center"><Lock className="w-5 h-5" /></div>
          <div>
            <div className="font-display text-2xl text-[#112325]">لوحة التحكم</div>
            <div className="text-sm text-[#3a5358]">تسجيل دخول المسؤول</div>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-[#3a5358] mb-1">البريد الإلكتروني</label>
            <input data-testid="admin-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="light-input w-full" />
          </div>
          <div>
            <label className="block text-sm font-semibold text-[#3a5358] mb-1">كلمة المرور</label>
            <input data-testid="admin-password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="light-input w-full" />
          </div>
          <button data-testid="admin-login-btn" type="submit" disabled={loading} className="btn-3d bg-[#0A3D42] text-white w-full h-12 rounded-xl font-bold inline-flex items-center justify-center gap-2 disabled:opacity-60">
            <LogIn className="w-4 h-4" />
            <span>{loading ? "..." : "تسجيل الدخول"}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
