import { useI18n } from "./I18nProvider";

export function LangToggle({ dark = false }: { dark?: boolean }) {
  const { lang, setLang, t } = useI18n();
  const btn = dark
    ? "rounded-full px-3 py-1 text-xs font-semibold"
    : "rounded-full px-3 py-1 text-xs font-semibold";
  const on = dark ? "bg-amber-200 text-ops" : "bg-moss text-white";
  const off = dark ? "text-emerald-100/80 hover:text-white" : "text-moss hover:bg-sand";
  return (
    <div className={`inline-flex gap-1 rounded-full p-1 ${dark ? "bg-white/10" : "bg-sand"}`} aria-label={t("language")}>
      <button type="button" className={`${btn} ${lang === "en" ? on : off}`} onClick={() => setLang("en")}>
        {t("english")}
      </button>
      <button type="button" className={`${btn} ${lang === "hi" ? on : off}`} onClick={() => setLang("hi")}>
        {t("hindi")}
      </button>
    </div>
  );
}
