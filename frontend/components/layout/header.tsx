"use client";

import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "@/providers/theme-provider";
import { Button } from "@/components/ui/button";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

export function Header() {
  const { theme, setTheme } = useTheme();
  const pathname = usePathname();

  const cycleTheme = () => {
    const themes: Array<"light" | "dark" | "system"> = ["light", "dark", "system"];
    const currentIndex = themes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex]);
  };

  // Generate breadcrumbs based on pathname
  const getBreadcrumbs = () => {
    // Root/dashboard
    if (pathname === "/" || pathname === "") {
      return (
        <BreadcrumbItem>
          <BreadcrumbPage>Dashboard</BreadcrumbPage>
        </BreadcrumbItem>
      );
    }

    // Session detail page: /sessions/[id]
    const sessionMatch = pathname.match(/^\/sessions\/([^/]+)$/);
    if (sessionMatch) {
      const sessionId = sessionMatch[1];
      return (
        <>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/">Sessions</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage className="font-mono">
              {sessionId.slice(0, 8)}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </>
      );
    }

    // Exercises page
    if (pathname === "/exercises") {
      return (
        <BreadcrumbItem>
          <BreadcrumbPage>Exercises</BreadcrumbPage>
        </BreadcrumbItem>
      );
    }

    // Exercise detail page: /exercises/[id]
    const exerciseMatch = pathname.match(/^\/exercises\/([^/]+)$/);
    if (exerciseMatch) {
      const exerciseId = exerciseMatch[1];
      return (
        <>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/exercises">Exercises</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage className="font-mono">
              {exerciseId.slice(0, 8)}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </>
      );
    }

    // Default fallback
    return (
      <BreadcrumbItem>
        <BreadcrumbPage>Dashboard</BreadcrumbPage>
      </BreadcrumbItem>
    );
  };

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div className="flex items-center gap-4">
        <Breadcrumb>
          <BreadcrumbList className="text-lg font-semibold">
            {getBreadcrumbs()}
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={cycleTheme}
          className="h-9 w-9"
        >
          {theme === "light" && <Sun className="h-4 w-4" />}
          {theme === "dark" && <Moon className="h-4 w-4" />}
          {theme === "system" && <Monitor className="h-4 w-4" />}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </div>
    </header>
  );
}
