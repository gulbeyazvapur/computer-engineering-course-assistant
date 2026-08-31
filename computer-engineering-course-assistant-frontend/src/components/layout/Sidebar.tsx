import {
  BookOpen,
  Files,
  GraduationCap,
  Info,
  MessageSquareText,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const items = [
  { to: "/", label: "Chat", icon: MessageSquareText, end: true },
  { to: "/courses", label: "Dersler", icon: BookOpen },
  { to: "/documents", label: "Kaynaklar", icon: Files },
  { to: "/about", label: "Hakkında", icon: Info },
];

export default function Sidebar() {
  return (
    <aside className="border-b border-warm-border bg-white md:flex md:w-64 md:flex-col md:border-b-0 md:border-r">
      <nav className="flex gap-2 overflow-x-auto p-3 md:flex-col md:p-4">
        {items.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              [
                "flex shrink-0 items-center gap-3 rounded-lg border-l-[3px] px-3 py-2.5 text-sm transition",
                isActive
                  ? "border-terracotta bg-terracotta-soft font-semibold text-terracotta-dark"
                  : "border-transparent font-medium text-warm-gray hover:bg-cream-soft hover:text-charcoal",
              ].join(" ")
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={`h-4 w-4 ${isActive ? "text-terracotta" : ""}`} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="hidden px-4 pb-4 md:mt-auto md:block">
        <div className="rounded-lg border border-warm-border bg-cream-soft p-4">
          <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-terracotta-soft text-terracotta">
            <GraduationCap className="h-4 w-4" />
          </div>
          <p className="text-sm font-semibold text-charcoal">Yardımcıyız</p>
          <p className="mt-1 text-xs leading-5 text-warm-gray">
            Sorularınızı sorun, birlikte öğrenelim.
          </p>
        </div>
      </div>
    </aside>
  );
}
