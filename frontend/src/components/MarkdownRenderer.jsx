import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ExternalLink, Pin, AlertCircle } from 'lucide-react';
import CodeBlock from './CodeBlock';

export default function MarkdownRenderer({ content = '', isStreaming = false }) {
  if (!content) return null;

  // Custom component overrides for retro-tactical HUD typography
  const components = {
    // Headings
    h1: ({ children }) => (
      <h1 className="text-sm sm:text-base font-black tracking-wide text-white uppercase mt-3 mb-1.5 border-b border-zinc-800 pb-1 flex items-center gap-1.5 font-mono">
        <span className="w-2 h-2 bg-red-600 inline-block mr-1"></span>
        {children}
      </h1>
    ),
    h2: ({ children }) => {
      const textVal = String(children);
      const isDiscussionSoFar = /discussion\s+so\s+far/i.test(textVal);

      if (isDiscussionSoFar) {
        return (
          <div className="mt-4 mb-2 pt-2 border-t border-zinc-800">
            <div className="flex items-center gap-2 p-2 bg-zinc-950 border-l-4 border-red-500 text-xs font-bold uppercase tracking-wider text-white font-mono shadow-sm">
              <Pin className="w-3.5 h-3.5 text-red-400 shrink-0 animate-pulse" />
              <span>[ 📌 CONTINUOUS DISCUSSION SUMMARY ]</span>
            </div>
          </div>
        );
      }

      return (
        <h2 className="text-xs sm:text-sm font-bold tracking-wide text-red-400 uppercase mt-3 mb-1 flex items-center gap-1.5 font-mono">
          <span className="text-zinc-600 font-mono">&gt;</span>
          {children}
        </h2>
      );
    },
    h3: ({ children }) => (
      <h3 className="text-xs font-bold text-zinc-200 mt-2.5 mb-1 flex items-center gap-1 font-mono">
        <span className="text-red-500 font-bold">•</span>
        {children}
      </h3>
    ),
    h4: ({ children }) => (
      <h4 className="text-xs font-semibold text-zinc-300 mt-2 mb-0.5 font-mono">
        {children}
      </h4>
    ),

    // Paragraphs
    p: ({ children }) => (
      <p className="text-xs text-zinc-200 leading-relaxed mb-2 last:mb-0 font-mono">
        {children}
      </p>
    ),

    // Lists
    ul: ({ children }) => (
      <ul className="list-disc list-outside ml-4 space-y-1 mb-2.5 text-xs text-zinc-300 marker:text-red-500 font-mono">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className="list-decimal list-outside ml-4 space-y-1 mb-2.5 text-xs text-zinc-300 marker:text-red-400 font-medium font-mono">
        {children}
      </ol>
    ),
    li: ({ children }) => (
      <li className="leading-relaxed pl-0.5">
        {children}
      </li>
    ),

    // Tables
    table: ({ children }) => (
      <div className="overflow-x-auto my-3 border border-zinc-800 bg-black/70 shadow-md">
        <table className="w-full text-left border-collapse font-mono text-xs text-zinc-200">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="bg-zinc-900 border-b border-zinc-700 text-[10px] uppercase font-bold text-red-400 tracking-wider">
        {children}
      </thead>
    ),
    tbody: ({ children }) => (
      <tbody className="divide-y divide-zinc-900">
        {children}
      </tbody>
    ),
    tr: ({ children }) => (
      <tr className="hover:bg-zinc-900/40 transition">
        {children}
      </tr>
    ),
    th: ({ children }) => (
      <th className="p-2 border-r border-zinc-800 last:border-r-0 font-bold whitespace-nowrap">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="p-2 border-r border-zinc-900 last:border-r-0 align-top">
        {children}
      </td>
    ),

    // Blockquote
    blockquote: ({ children }) => (
      <blockquote className="border-l-2 border-red-500 bg-zinc-950/60 p-2.5 my-2.5 text-zinc-300 italic text-xs space-y-1 font-mono">
        {children}
      </blockquote>
    ),

    // Links & Citations
    a: ({ href, children }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-0.5 text-red-400 hover:text-red-300 underline font-semibold decoration-red-500/50 hover:decoration-red-300 transition"
      >
        <span>{children}</span>
        <ExternalLink className="w-2.5 h-2.5 inline-block shrink-0" />
      </a>
    ),

    // Code & Syntax Highlighting
    code: ({ node, inline, className, children, ...props }) => {
      const match = /language-(\w+)/.exec(className || '');
      const codeString = String(children).replace(/\n$/, '');

      if (!inline && (match || codeString.includes('\n'))) {
        return (
          <CodeBlock
            language={match ? match[1] : ''}
            value={codeString}
          />
        );
      }

      return (
        <code
          className="px-1.5 py-0.5 rounded-none bg-zinc-900 border border-zinc-700 text-red-300 font-mono text-[11px] selection:bg-red-800"
          {...props}
        >
          {children}
        </code>
      );
    }
  };

  return (
    <div className="ops-markdown-content font-mono select-text">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
