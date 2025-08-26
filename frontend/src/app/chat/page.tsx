"use client";
import { useState, useRef, useEffect, FormEvent, ChangeEvent, memo } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import axios from "axios";
import Cookies from "js-cookie";
import TextareaAutosize from "react-textarea-autosize";
import { Button } from "@/components/ui/button";

import {
  Paperclip,
  Send,
  LogOut,
  MessageSquarePlus,
  PanelLeftOpen,
  PanelLeftClose,
  Trash2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// Types
interface Message {
  role: "user" | "assistant";
  message: string;
}
interface ChatSession {
  id: string;
  title: string;
}

// --- Memoized UI Components ---

const Sidebar = memo(function Sidebar({
  chatSessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onLogout,
  isCollapsed,
  onToggleCollapse,
  onDeleteSession
}: {
  chatSessions: ChatSession[],
  activeSessionId: string | null,
  onNewChat: () => void,
  onSelectSession: (id: string) => void,
  onLogout: () => void,
  isCollapsed: boolean,
  onToggleCollapse: () => void,
  onDeleteSession: (id: string) => void
}) {
  return (
    <motion.div
      initial={false}
      animate={{ width: isCollapsed ? 64 : 280 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="bg-gray-950 border-r border-gray-800 text-gray-200 flex flex-col relative"
    >
      {/* Header with toggle button */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        {!isCollapsed && (
          <Button onClick={onNewChat} variant="default" className="flex-1 justify-start text-sm font-medium gap-2">
            <MessageSquarePlus size={16} /> New Chat
          </Button>
        )}
        <Button
          onClick={onToggleCollapse}
          variant="ghost"
          size="icon"
          className="text-gray-400 hover:text-white hover:bg-gray-800 transition-colors flex-shrink-0"
        >
          {isCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </Button>
      </div>

      {/* Chat Sessions */}
      <div className="flex-grow overflow-y-auto px-2">
        <div className="space-y-1 py-2">
          {chatSessions.map((session) => (
            <div key={session.id} className="group relative">
              <Button
                variant={activeSessionId === session.id ? "secondary" : "ghost"}
                className={`w-full text-sm ${isCollapsed ? 'px-2 justify-center' : 'justify-start truncate pr-8'}`}
                onClick={() => onSelectSession(session.id)}
                title={isCollapsed ? session.title : undefined}
              >
                {isCollapsed ? (
                  <div className="w-4 h-4 bg-gray-600 rounded flex items-center justify-center text-xs font-semibold">
                    {session.title.charAt(0).toUpperCase()}
                  </div>
                ) : (
                  session.title
                )}
              </Button>

              {/* Delete Button - Shows on hover */}
              <Button
                variant="ghost"
                size="icon"
                className={`absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 text-gray-400 hover:text-red-400 hover:bg-red-950 ${isCollapsed ? 'hidden' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm(`Delete chat session "${session.title}"?`)) {
                    onDeleteSession(session.id);
                  }
                }}
                title="Delete session"
              >
                <Trash2 size={12} />
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className={`p-4 border-t border-gray-800 ${isCollapsed ? 'flex justify-center' : ''}`}>
        <Button
          onClick={onLogout}
          variant="ghost"
          className={`text-sm ${isCollapsed ? 'p-2' : 'w-full justify-start gap-2'}`}
          title={isCollapsed ? 'Logout' : undefined}
        >
          {isCollapsed ? <LogOut size={16} /> : (
            <>
              <LogOut size={16} /> Logout
            </>
          )}
        </Button>
      </div>
    </motion.div>
  );
});

const ChatMessage = memo(function ChatMessage({ msg }: { msg: Message }) {
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-xl px-4 py-2 rounded-2xl shadow-md text-sm break-words ${msg.role === "user" ? "bg-blue-600 text-white rounded-br-none" : "bg-gray-800 text-gray-100 rounded-bl-none"}`}>
        {msg.message}
      </div>
    </motion.div>
  );
});

const EmptyState = memo(function EmptyState() {
    return (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="mb-4 text-gray-400"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
            <p className="text-lg">Your intelligent RAG chatbot</p>
        </div>
    );
});

// --- Main Page Component ---
export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const scrollViewportRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { logout, isAuthenticated, isLoading: authLoading } = useAuth();

  // Check authentication and redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  // --- Logic Functions ---
  useEffect(() => {
    const fetchChatSessions = async () => {
      try {
        const response = await axios.get("http://localhost:8000/api/chat/sessions", { withCredentials: true });
        setChatSessions(response.data);
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 401) router.push("/login");
      }
    };
    if (isAuthenticated) {
      fetchChatSessions();
    }
  }, [router, isAuthenticated]);

  // Improved auto-scroll logic
  useEffect(() => {
    const viewport = scrollViewportRef.current;
    if (viewport && shouldAutoScroll) {
      // Use requestAnimationFrame for smoother scrolling
      requestAnimationFrame(() => {
        viewport.scrollTo({ top: viewport.scrollHeight, behavior: "smooth" });
      });
    }
  }, [messages, shouldAutoScroll]);

  // Handle scroll events to detect manual scrolling
  useEffect(() => {
    const viewport = scrollViewportRef.current;
    if (!viewport) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = viewport;
      const isNearBottom = scrollTop + clientHeight >= scrollHeight - 100; // 100px threshold
      setShouldAutoScroll(isNearBottom);
    };

    viewport.addEventListener('scroll', handleScroll, { passive: true });
    return () => viewport.removeEventListener('scroll', handleScroll);
  }, []);

  const fetchSessionMessages = async (sessionId: string) => {
    if (isLoading) return;
    setActiveSessionId(sessionId);
    setIsLoading(true);
    setMessages([]);
    try {
      const response = await axios.get(`http://localhost:8000/api/chat/history/${sessionId}`, { withCredentials: true });
      const formatted = response.data.map((msg: any) => ({ role: msg.role, message: msg.message }));
      setMessages(formatted);
    } catch {
      setMessages([{ role: "assistant", message: "⚠️ Error loading chat history." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => { setActiveSessionId(null); setMessages([]); setInput(""); };
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => { if (event.target.files) handleFileUpload(event.target.files[0]); };

  const handleFileUpload = async (file: File) => {
    if (!file) return;
    const sessionIdForUpload = activeSessionId || crypto.randomUUID();
    if (!activeSessionId) setActiveSessionId(sessionIdForUpload);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionIdForUpload);

    setIsLoading(true);
    setMessages((prev) => [...prev, { role: "assistant", message: `📂 Uploading ${file.name}...` }]);
    try {
      await axios.post("http://localhost:8000/api/upload", formData, { withCredentials: true });
      setMessages((prev) => [...prev, { role: "assistant", message: `✅ Uploaded ${file.name}. You can now ask about it.` }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", message: `❌ Error uploading ${file.name}. Try again.` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await axios.delete(`http://localhost:8000/api/chat/sessions/${sessionId}`, { withCredentials: true });

      // Remove from chat sessions list
      setChatSessions((prev) => prev.filter((session) => session.id !== sessionId));

      // If the deleted session was active, clear it
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
        setInput("");
      }

      // Refresh sessions list
      const response = await axios.get("http://localhost:8000/api/chat/sessions", { withCredentials: true });
      setChatSessions(response.data);
    } catch (error) {
      console.error("Error deleting session:", error);
      // Could add a toast notification here
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const currentInput = input.trim();
    if (!currentInput || isLoading) return;

    const userMsg: Message = { role: "user", message: currentInput };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    const sessionIdToSend = activeSessionId || crypto.randomUUID();

    try {
      const response = await axios.post("http://localhost:8000/api/chat", { query: currentInput, session_id: sessionIdToSend }, { withCredentials: true });
      const botMsg: Message = { role: "assistant", message: response.data.response };
      setMessages((prev) => [...prev, botMsg]);
      if (!activeSessionId) {
        setActiveSessionId(sessionIdToSend);
        setChatSessions((prev) => [{ id: sessionIdToSend, title: currentInput }, ...prev]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", message: "⚠️ Sorry, I couldn’t respond. Check API key or connection." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 via-black to-gray-950 overflow-hidden">
      <Sidebar
        chatSessions={chatSessions}
        activeSessionId={activeSessionId}
        onNewChat={handleNewChat}
        onSelectSession={fetchSessionMessages}
        onLogout={handleLogout}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        onDeleteSession={handleDeleteSession}
      />

      {/* --- IMPROVED CHAT PANEL LAYOUT --- */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div
          ref={scrollViewportRef}
          className="flex-1 overflow-y-auto scroll-smooth"
          style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgb(75 85 99) rgb(31 41 55)' }}
        >
          <div className="max-w-3xl mx-auto px-4 py-8 space-y-4">
            {messages.length === 0 && !isLoading ? (
              <EmptyState />
            ) : (
              <AnimatePresence>
                {messages.map((msg, i) => (
                  <ChatMessage key={`${activeSessionId || 'new'}-${i}`} msg={msg} />
                ))}
              </AnimatePresence>
            )}
            {isLoading && messages.length > 0 && messages[messages.length-1]?.role === 'user' && (
              <div className="flex justify-start">
                <div className="bg-gray-800 text-gray-100 rounded-2xl shadow-md p-3">
                  <div className="flex items-center space-x-2">
                    <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"></span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input Area */}
        <div className="flex-shrink-0 border-t border-gray-800 bg-gray-950/90 backdrop-blur-sm p-4">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex items-center gap-2">
            <Button type="button" variant="ghost" size="icon" className="text-gray-400 hover:text-white hover:bg-gray-800 transition-colors" onClick={() => fileInputRef.current?.click()} disabled={isLoading}>
              <Paperclip className="h-5 w-5" />
            </Button>
            <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".pdf"/>
            <TextareaAutosize value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask anything, or attach a file..." className="flex-1 bg-gray-900 text-gray-200 border border-gray-700 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500" onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) handleSubmit(e); }} minRows={1} maxRows={5}/>
            <Button type="submit" variant="default" size="icon" disabled={isLoading || !input.trim()} className="bg-blue-600 hover:bg-blue-700">
              <Send className="h-5 w-5" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
