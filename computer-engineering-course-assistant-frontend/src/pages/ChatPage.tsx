import { useMemo, useState } from "react";
import { Trash2 } from "lucide-react";
import Alert from "../components/common/Alert";
import Button from "../components/common/Button";
import Loader from "../components/common/Loader";
import ChatInput from "../components/chat/ChatInput";
import ChatMessage from "../components/chat/ChatMessage";
import CourseSelector from "../components/chat/CourseSelector";
import EmptyChatState from "../components/chat/EmptyChatState";
import { useCourses } from "../hooks/useCourses";
import { sendQuestion } from "../services/chatService";
import type { ChatMessageModel } from "../types/chat";
import { getErrorMessage } from "../utils/getErrorMessage";

function newMessageId() {
  return crypto.randomUUID();
}

export default function ChatPage() {
  const { courses, isLoading: isCoursesLoading, error: coursesError } =
    useCourses();

  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessageModel[]>([]);
  const [question, setQuestion] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  const selectedCourse = useMemo(
    () => courses.find((course) => course.id === selectedCourseId),
    [courses, selectedCourseId],
  );

  async function handleSend() {
    const normalized = question.trim();

    if (!selectedCourseId) {
      setChatError("Lütfen önce bir ders seçin.");
      return;
    }

    if (!normalized) {
      setChatError("Soru boş bırakılamaz.");
      return;
    }

    if (isChatLoading) return;

    const userMessage: ChatMessageModel = {
      id: newMessageId(),
      role: "user",
      content: normalized,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setChatError(null);
    setIsChatLoading(true);

    try {
      const response = await sendQuestion({
        question: normalized,
        courseId: selectedCourseId,
      });

      setMessages((current) => [
        ...current,
        {
          id: newMessageId(),
          role: "assistant",
          content: response.answer,
          sources: response.sources,
        },
      ]);
    } catch (err) {
      setChatError(getErrorMessage(err, "AI yanıtı alınamadı."));
    } finally {
      setIsChatLoading(false);
    }
  }

  return (
    <section className="mx-auto max-w-6xl space-y-4">
      <div className="flex flex-col justify-between gap-4 rounded-lg border border-warm-border bg-white p-4 sm:flex-row sm:items-end">
        <div className="min-w-0 flex-1 sm:max-w-md">
          <CourseSelector
            courses={courses}
            value={selectedCourseId}
            onChange={(id) => {
              setSelectedCourseId(id);
              setChatError(null);
            }}
            disabled={isCoursesLoading || isChatLoading}
          />
          {selectedCourse && (
            <p className="mt-2 truncate text-xs text-warm-gray">
              Aktif ders: {selectedCourse.name}
            </p>
          )}
        </div>

        {messages.length > 0 && (
          <Button
            variant="secondary"
            type="button"
            onClick={() => {
              setMessages([]);
              setChatError(null);
            }}
            disabled={isChatLoading}
          >
            <Trash2 className="h-4 w-4" />
            Sohbeti Temizle
          </Button>
        )}
      </div>

      {coursesError && <Alert kind="error">{coursesError}</Alert>}
      {chatError && <Alert kind="error">{chatError}</Alert>}

      <div className="overflow-hidden rounded-lg border border-warm-border bg-cream-soft">
        <div className="min-h-[420px] max-h-[calc(100vh-18rem)] overflow-y-auto p-4 md:p-6">
          {messages.length === 0 ? (
            <EmptyChatState />
          ) : (
            <div className="space-y-5">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}

              {isChatLoading && (
                <div className="rounded-lg border border-warm-border bg-white p-4">
                  <Loader label="Yerel AI yanıt hazırlıyor..." />
                </div>
              )}
            </div>
          )}
        </div>

        <ChatInput
          value={question}
          onChange={setQuestion}
          onSubmit={() => void handleSend()}
          disabled={isChatLoading || isCoursesLoading}
        />
      </div>
    </section>
  );
}
