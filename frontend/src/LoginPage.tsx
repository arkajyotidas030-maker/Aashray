import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setSession } from "./api";
import { useI18n } from "./I18nProvider";
import { LangToggle } from "./LangToggle";
import { LogoMark } from "./LogoMark";

export function LoginPage() {
  const { t } = useI18n();
  const nav = useNavigate();
  const [email, setEmail] = useState("citizen@demo");
  const [password, setPassword] = useState("demo");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const r = await api.login(email, password);
      setSession(r.access_token, r.role);
      nav(r.role === "responder" ? "/ops" : "/c");
    } catch {
      setErr(t("loginError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(1200px_600px_at_10%_-10%,#99f6e4_0%,transparent_50%),radial-gradient(900px_500px_at_100%_0%,#fed7aa_0%,transparent_40%),#f4efe4]">
      <header className="px-6 py-5">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
        <div className="flex items-center gap-3">
          <LogoMark crop={false} className="h-14 w-auto" />
          <div>
            <p className="font-display text-xl font-semibold tracking-tight text-moss">{t("brand")}</p>
            <p className="text-xs text-moss/70">VBYLD · Hack for Social Cause</p>
          </div>
        </div>
        <LangToggle />
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-10 px-6 pb-16 pt-4 md:grid-cols-2 md:items-center">
        <section>
          <LogoMark crop={false} className="mb-6 h-auto w-full max-w-xs" />
          <h1 className="font-display text-4xl leading-tight text-ink md:text-5xl">{t("tagline")}</h1>
          <p className="mt-5 max-w-md text-base leading-relaxed text-ink/75">{t("welcomeOps")}</p>
          <ul className="mt-8 space-y-3 text-sm text-ink/80">
            <li className="flex gap-3"><span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-clay" />{t("thesis")}</li>
            <li className="flex gap-3"><span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-moss-2" />{t("notMissing")}</li>
          </ul>
        </section>

        <form onSubmit={onSubmit} className="rounded-3xl border border-white/60 bg-white/85 p-8 shadow-xl shadow-moss/10 backdrop-blur">
          <h2 className="font-display text-2xl text-ink">{t("loginTitle")}</h2>
          <p className="mt-1 text-sm text-ink/60">{t("loginHint")}</p>
          <div className="mt-6 grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setEmail("citizen@demo")}
              className={`rounded-2xl border px-3 py-3 text-left ${email.startsWith("citizen") ? "border-moss bg-moss text-white" : "border-sand bg-paper"}`}
            >
              <span className="block text-sm font-semibold">{t("citizen")}</span>
              <span className={`mt-1 block text-[11px] ${email.startsWith("citizen") ? "text-white/80" : "text-ink/55"}`}>{t("roleHintCitizen")}</span>
            </button>
            <button
              type="button"
              onClick={() => setEmail("ops@demo")}
              className={`rounded-2xl border px-3 py-3 text-left ${email.startsWith("ops") ? "border-moss bg-moss text-white" : "border-sand bg-paper"}`}
            >
              <span className="block text-sm font-semibold">{t("responder")}</span>
              <span className={`mt-1 block text-[11px] ${email.startsWith("ops") ? "text-white/80" : "text-ink/55"}`}>{t("roleHintOps")}</span>
            </button>
          </div>
          <label className="mt-6 block text-xs font-semibold uppercase tracking-wide text-ink/50">{t("email")}</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" className="mt-1 w-full rounded-2xl border border-sand bg-paper px-4 py-3 outline-none ring-moss focus:ring-2" />
          <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-ink/50">{t("password")}</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" className="mt-1 w-full rounded-2xl border border-sand bg-paper px-4 py-3 outline-none ring-moss focus:ring-2" />
          {err && <p className="mt-3 text-sm text-clay">{err}</p>}
          <button disabled={busy} className="mt-6 w-full rounded-2xl bg-moss py-3.5 text-sm font-bold text-white shadow-lg shadow-moss/25 hover:bg-moss-2 disabled:opacity-60">
            {busy ? t("sending") : t("enter")}
          </button>
        </form>
      </main>
    </div>
  );
}
