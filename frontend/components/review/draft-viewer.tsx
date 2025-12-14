"use client";

import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils/cn";

interface DraftViewerProps {
  content: string;
  className?: string;
}

export function DraftViewer({ content, className }: DraftViewerProps) {
  if (!content) {
    return (
      <div className="rounded-xl bg-muted/50 p-6 text-center border border-dashed border-border">
        <p className="text-muted-foreground text-sm">No draft content available</p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "prose prose-sm dark:prose-invert max-w-none rounded-xl bg-muted/30 p-6 border border-border/50",
        "prose-headings:text-foreground prose-p:text-foreground/90",
        "prose-strong:text-foreground prose-em:text-foreground/80",
        "prose-ul:text-foreground/90 prose-ol:text-foreground/90",
        "prose-blockquote:border-primary prose-blockquote:text-muted-foreground",
        "prose-code:bg-muted prose-code:text-foreground prose-code:rounded-md prose-code:px-1.5 prose-code:py-0.5",
        className
      )}
    >
      <ReactMarkdown
        components={{
          h1: ({ children }) => (
            <h1 className="text-xl font-bold mb-4 pb-2 border-b border-border">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-semibold mb-3 mt-6 text-foreground">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-medium mb-2 mt-4 text-foreground">{children}</h3>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-6 space-y-1.5 my-3">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-6 space-y-1.5 my-3">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-sm leading-relaxed">{children}</li>
          ),
          p: ({ children }) => (
            <p className="my-3 leading-relaxed">{children}</p>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-foreground/80">{children}</em>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-primary/50 bg-primary/5 pl-4 pr-3 py-2 italic my-4 rounded-r-lg">
              {children}
            </blockquote>
          ),
          code: ({ children }) => (
            <code className="rounded-md bg-muted px-1.5 py-0.5 text-sm font-mono text-foreground">
              {children}
            </code>
          ),
          hr: () => (
            <hr className="my-6 border-border" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
