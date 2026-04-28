import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  children: string;
}

/**
 * Safe Markdown renderer. react-markdown does not pass HTML through by
 * default, so we don't need an explicit sanitizer here.
 */
export function Markdown({ children }: Props) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ href, children: linkChildren }) => {
          const safe = typeof href === "string" && /^https?:\/\//i.test(href);
          return safe ? (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {linkChildren}
            </a>
          ) : (
            <span>{linkChildren}</span>
          );
        },
      }}
    >
      {children}
    </ReactMarkdown>
  );
}
