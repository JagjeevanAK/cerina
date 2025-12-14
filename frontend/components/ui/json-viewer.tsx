"use client";

import { useState, useMemo } from "react";
import { ChevronRight, ChevronDown, Copy, Check } from "lucide-react";

interface JsonViewerProps {
  data: unknown;
  initialExpanded?: boolean;
  rootName?: string;
}

type JsonValue = string | number | boolean | null | JsonObject | JsonArray;
interface JsonObject { [key: string]: JsonValue }
type JsonArray = JsonValue[];

const JsonViewer = ({ data, initialExpanded = true, rootName }: JsonViewerProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="font-mono text-[13px] bg-[#1e1e1e] text-[#d4d4d4] rounded-md overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#252526] border-b border-[#3c3c3c]">
        <span className="text-[11px] text-[#808080]">JSON</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] text-[#808080] hover:text-[#d4d4d4] transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="p-3 overflow-x-auto">
        <JsonNode value={data} name={rootName} isLast={true} depth={0} initialExpanded={initialExpanded} />
      </div>
    </div>
  );
};

interface JsonNodeProps {
  value: unknown;
  name?: string;
  isLast: boolean;
  depth: number;
  initialExpanded: boolean;
}

const JsonNode = ({ value, name, isLast, depth, initialExpanded }: JsonNodeProps) => {
  const [expanded, setExpanded] = useState(initialExpanded && depth < 3);

  const valueType = useMemo(() => {
    if (value === null) return "null";
    if (Array.isArray(value)) return "array";
    return typeof value;
  }, [value]);

  const isExpandable = valueType === "object" || valueType === "array";
  const isEmpty = isExpandable && (
    (valueType === "array" && (value as JsonArray).length === 0) ||
    (valueType === "object" && Object.keys(value as JsonObject).length === 0)
  );

  const renderValue = () => {
    switch (valueType) {
      case "string":
        return <span className="text-[#ce9178]">&quot;{String(value)}&quot;</span>;
      case "number":
        return <span className="text-[#b5cea8]">{String(value)}</span>;
      case "boolean":
        return <span className="text-[#569cd6]">{String(value)}</span>;
      case "null":
        return <span className="text-[#569cd6]">null</span>;
      default:
        return null;
    }
  };

  const renderExpandable = () => {
    const items = valueType === "array" 
      ? (value as JsonArray).map((v, i) => ({ key: String(i), value: v }))
      : Object.entries(value as JsonObject).map(([k, v]) => ({ key: k, value: v }));
    
    const bracketOpen = valueType === "array" ? "[" : "{";
    const bracketClose = valueType === "array" ? "]" : "}";

    if (isEmpty) {
      return (
        <span>
          {name !== undefined && (
            <>
              <span className="text-[#9cdcfe]">&quot;{name}&quot;</span>
              <span className="text-[#d4d4d4]">: </span>
            </>
          )}
          <span className="text-[#d4d4d4]">{bracketOpen}{bracketClose}</span>
          {!isLast && <span className="text-[#d4d4d4]">,</span>}
        </span>
      );
    }

    return (
      <div>
        <div 
          className="flex items-center cursor-pointer hover:bg-[#2a2d2e] -ml-4 pl-4 rounded"
          onClick={() => setExpanded(!expanded)}
        >
          <span className="w-4 h-4 flex items-center justify-center text-[#808080] mr-0.5">
            {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </span>
          {name !== undefined && (
            <>
              <span className="text-[#9cdcfe]">&quot;{name}&quot;</span>
              <span className="text-[#d4d4d4]">: </span>
            </>
          )}
          <span className="text-[#d4d4d4]">{bracketOpen}</span>
          {!expanded && (
            <>
              <span className="text-[#808080] mx-1">
                {valueType === "array" ? `${items.length} items` : `${items.length} keys`}
              </span>
              <span className="text-[#d4d4d4]">{bracketClose}</span>
              {!isLast && <span className="text-[#d4d4d4]">,</span>}
            </>
          )}
        </div>
        {expanded && (
          <>
            <div className="ml-4 border-l border-[#3c3c3c] pl-2">
              {items.map((item, idx) => (
                <JsonNode
                  key={item.key}
                  name={valueType === "object" ? item.key : undefined}
                  value={item.value}
                  isLast={idx === items.length - 1}
                  depth={depth + 1}
                  initialExpanded={initialExpanded}
                />
              ))}
            </div>
            <div>
              <span className="text-[#d4d4d4]">{bracketClose}</span>
              {!isLast && <span className="text-[#d4d4d4]">,</span>}
            </div>
          </>
        )}
      </div>
    );
  };

  if (isExpandable) {
    return renderExpandable();
  }

  return (
    <div className="leading-6">
      {name !== undefined && (
        <>
          <span className="text-[#9cdcfe]">&quot;{name}&quot;</span>
          <span className="text-[#d4d4d4]">: </span>
        </>
      )}
      {renderValue()}
      {!isLast && <span className="text-[#d4d4d4]">,</span>}
    </div>
  );
};

export default JsonViewer;
export { JsonViewer };
