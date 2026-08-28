"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CalendarCheck, ClipboardList, LayoutDashboard, Users } from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/employees", label: "Employees", icon: Users },
  { href: "/attendance", label: "Attendance", icon: CalendarCheck },
  { href: "/reports", label: "Reports", icon: ClipboardList },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="flex w-60 shrink-0 flex-col bg-slate-900 text-slate-100">
      <div className="border-b border-slate-700 px-5 py-5">
        <p className="text-sm font-semibold tracking-wide">FactoryHR Lite</p>
        <p className="mt-1 text-xs leading-5 text-slate-400">
          Manufacturing Workforce Operations
        </p>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3" aria-label="주 메뉴">
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm outline-none ring-offset-2 ring-offset-slate-900 focus-visible:ring-2 focus-visible:ring-teal-300 ${
                active
                  ? "bg-slate-800 text-white shadow-[inset_3px_0_0_0_#2dd4bf]"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
              aria-current={active ? "page" : undefined}
            >
              <Icon size={16} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
