import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { copy, type CopyKey, type Lang } from "./i18n";

const Ctx = createContext<{
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (k: CopyKey) => string;
} | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => (localStorage.getItem("aashray.lang") as Lang) || "en");
  const setLang = (l: Lang) => {
    setLangState(l);
    localStorage.setItem("aashray.lang", l);
    document.documentElement.lang = l;
  };
  const t = useMemo(() => {
    document.documentElement.lang = lang;
    return (k: CopyKey) => copy[lang][k] ?? copy.en[k];
  }, [lang]);
  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}

export function useI18n() {
  const v = useContext(Ctx);
  if (!v) throw new Error("i18n");
  return v;
}
