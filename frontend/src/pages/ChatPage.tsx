/**
 * Chat Page — Dark theme, RAG-powered clinical Q&A
 */
import React, { useState, useRef, useEffect } from "react";
import { ragAPI } from "../api/client";
import toast from "react-hot-toast";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  timestamp: Date;
}

const SUGGESTED_QUESTIONS = [
  "What are the main risk factors for Type 2 Diabetes?",
  "How does hypertension increase cardiovascular risk?",
  "What lifestyle changes reduce heart disease risk?",
  "Explain HbA1c and diabetes management.",
  "What does high LDL cholesterol mean for my health?",
];

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([{
    id: "welcome", role: "assistant", timestamp: new Date(),
    content: "Hello! I'm your clinical AI assistant powered by Llama 3 and medical literature. Ask me about disease risk factors, guidelines, or your assessment results.",
  }]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;
    setMessages(prev => [...prev, { id: Date.now().toString(), role: "user", content: text, timestamp: new Date() }]);
    setInput("");
    setIsLoading(true);
    try {
      const { data } = await ragAPI.query({ query: text, top_k: 5, include_sources: true });
      setMessages(prev => [...prev, {
        id: (Date.now()+1).toString(), role: "assistant",
        content: data.answer, sources: data.sources, timestamp: new Date(),
      }]);
    } catch {
      toast.error("Failed to get response.");
      setMessages(prev => [...prev, {
        id: (Date.now()+1).toString(), role: "assistant",
        content: "I encountered an error. Please try again.", timestamp: new Date(),
      }]);
    } finally { setIsLoading(false); }
  };

  return (
    <div className="h-screen bg-gray-950 flex flex-col p-4">
      <div className="mb-3">
        <h1 className="text-2xl font-bold text-white">Clinical AI Assistant</h1>
        <p className="text-gray-500 text-xs">Powered by Llama 3 + RAG · Grounded in medical literature</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-900 rounded-2xl border border-gray-800 p-4 space-y-3 mb-3">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-200 border border-gray-700"
            }`}>
              {msg.role === "assistant" && (
                <p className="text-xs font-semibold text-blue-400 mb-1.5">🤖 Clinical AI</p>
              )}
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <p className="text-xs font-semibold text-gray-500 mb-2">Sources:</p>
                  {msg.sources.slice(0, 3).map((src: any, i: number) => (
                    <div key={i} className="text-xs bg-gray-700 rounded-lg p-2 border border-gray-600 mb-1">
                      <span className="font-medium text-gray-300">{src.title}</span>
                      <span className="text-gray-500 ml-2">({(src.relevance_score*100).toFixed(0)}%)</span>
                      <p className="text-gray-500 mt-0.5 line-clamp-2">{src.excerpt}</p>
                    </div>
                  ))}
                </div>
              )}
              <p className="text-xs opacity-30 mt-1">{msg.timestamp.toLocaleTimeString()}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-2xl px-4 py-3 border border-gray-700">
              <div className="flex gap-1">
                {[0,150,300].map(d => (
                  <div key={d} className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested questions */}
      {messages.length <= 1 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map(q => (
            <button key={q} onClick={() => sendMessage(q)}
              className="text-xs bg-gray-800 text-gray-400 border border-gray-700 rounded-full px-3 py-1.5 hover:bg-gray-700 hover:text-gray-200 transition-colors">
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex gap-3">
        <input type="text" value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
          placeholder="Ask a clinical question..."
          className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none placeholder-gray-600"
          disabled={isLoading} />
        <button onClick={() => sendMessage(input)} disabled={isLoading || !input.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 text-white px-5 py-3 rounded-xl font-medium text-sm transition-colors">
          Send
        </button>
      </div>
    </div>
  );
};
