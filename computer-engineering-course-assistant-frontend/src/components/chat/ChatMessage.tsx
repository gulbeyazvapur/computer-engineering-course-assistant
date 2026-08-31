import { Bot, UserRound } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { ChatMessageModel } from "../../types/chat";
import SourceList from "./SourceList";

interface ChatMessageProps {
  message: ChatMessageModel;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <article
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <div
        className={[
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
          isUser
            ? "bg-charcoal text-white"
            : "bg-lavender-soft text-lavender",
        ].join(" ")}
      >
        {isUser ? (
          <UserRound className="h-4 w-4" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </div>

      <div
        className={[
          "max-w-[88%] rounded-lg border px-4 py-3 text-sm md:max-w-[78%]",
          isUser
            ? "border-charcoal bg-charcoal text-white"
            : "border-warm-border bg-white text-charcoal",
        ].join(" ")}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <>
            <div className="prose-answer">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
            <SourceList sources={message.sources ?? []} />
          </>
        )}
      </div>
    </article>
  );
}
