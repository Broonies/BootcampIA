import { useState } from "react";

export default function App() {
  const [message, setMessage] = useState("");
  const [chatLog, setChatLog] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;
    
    const userMessage = { role: "user", content: message };
    setChatLog(prev => [...prev, userMessage]);
    setMessage("");
    setLoading(true);
    
    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: userMessage.content, 
          history: chatLog 
        })
      });
      
      if (!res.ok) throw new Error("Erreur serveur");
      
      const data = await res.json();
      setChatLog(prev => [...prev, { 
        role: "assistant", 
        content: data.response 
      }]);
    } catch (error) {
      console.error("Erreur:", error);
      setChatLog(prev => [...prev, { 
        role: "assistant", 
        content: "❌ Erreur de connexion au serveur" 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <header className="bg-black/30 backdrop-blur-lg border-b border-purple-500/20 p-4">
        <h1 className="text-2xl font-bold text-white">🤖 Chatbot IA Local</h1>
        <p className="text-sm text-gray-400">Propulsé par Qwen3:30B</p>
      </header>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {chatLog.length === 0 && (
          <div className="text-center text-gray-400 mt-10">
            <p className="text-xl mb-2">👋 Bonjour !</p>
            <p>Posez-moi une question pour commencer</p>
          </div>
        )}
        
        {chatLog.map((msg, i) => (
          <div 
            key={i} 
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div className={`max-w-[80%] p-3 rounded-lg ${
              msg.role === "user" 
                ? "bg-purple-600 text-white" 
                : "bg-slate-800 text-gray-200 border border-purple-500/20"
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-purple-500/20 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-slate-800/50 backdrop-blur-lg border-t border-purple-500/20">
        <div className="flex gap-2">
          <input
            className="flex-1 p-3 rounded-lg bg-slate-900 border border-purple-500/30 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !loading && sendMessage()}
            placeholder="Tapez votre message..."
            disabled={loading}
          />
          <button 
            onClick={sendMessage}
            disabled={loading || !message.trim()}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition"
          >
            {loading ? "..." : "Envoyer"}
          </button>
        </div>
      </div>
    </div>
  );
}