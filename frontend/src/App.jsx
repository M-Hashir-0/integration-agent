import React, { useState } from 'react';
import { Send, Plus, Server, Bot, User, Terminal } from 'lucide-react';
import { addIntegration, sendMessage } from './api';

function App()
{
  // --- State ---
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your Integration Agent. Connect an API to get started.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Integration Form State
  const [integName, setIntegName] = useState('Petstore');
  const [integUrl, setIntegUrl] = useState('https://petstore.swagger.io/v2/swagger.json');
  const [integKey, setIntegKey] = useState('');
  const [statusMsg, setStatusMsg] = useState('');

  // --- Handlers ---

  const handleConnect = async (e) =>
  {
    e.preventDefault();
    setStatusMsg('Connecting...');
    try
    {
      const res = await addIntegration(integName, integUrl, integKey);
      setStatusMsg(`Success! Added ${res.tools_count} tools.`);
    } catch (err)
    {
      setStatusMsg(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleSend = async (e) =>
  {
    e.preventDefault();
    if (!input.trim()) return;

    // add user Message
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try
    {
      // call API
      const data = await sendMessage(userMsg.content);

      // add Assistant Response
      const botMsg = {
        role: 'assistant',
        content: data.response,
        tool_calls: data.tool_calls
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err)
    {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error connecting to agent.' }]);
    } finally
    {
      setIsLoading(false);
    }
  };

  // --- Render ---
  return (
    <div className="flex h-screen bg-gray-900 text-gray-100 font-sans">

      {/* SIDEBAR: Configuration */}
      <div className="w-80 border-r border-gray-800 p-6 flex flex-col">
        <h1 className="text-xl font-bold flex items-center gap-2 mb-8 text-blue-400">
          <Server size={24} />
          Agent Control
        </h1>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <h2 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wider">Add Integration</h2>
          <form onSubmit={handleConnect} className="space-y-3">
            <div>
              <label className="block text-xs mb-1 text-gray-500">Name</label>
              <input
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-sm focus:border-blue-500 outline-none"
                value={integName}
                onChange={e => setIntegName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs mb-1 text-gray-500">OpenAPI Spec URL</label>
              <input
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-xs focus:border-blue-500 outline-none"
                value={integUrl}
                onChange={e => setIntegUrl(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs mb-1 text-gray-500">API Key (Optional)</label>
              <input
                type="password"
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-sm focus:border-blue-500 outline-none"
                placeholder="sk_..."
                value={integKey}
                onChange={e => setIntegKey(e.target.value)}
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded p-2 text-sm font-medium flex items-center justify-center gap-2 transition"
            >
              <Plus size={16} /> Connect API
            </button>
          </form>
          {statusMsg && (
            <div className={`mt-3 text-xs p-2 rounded ${statusMsg.includes('Success') ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
              {statusMsg}
            </div>
          )}
        </div>
      </div>

      {/* MAIN: Chat Interface */}
      <div className="flex-1 flex flex-col">
        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>

              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                  <Bot size={16} />
                </div>
              )}

              <div className={`max-w-2xl space-y-2`}>
                <div className={`p-4 rounded-2xl ${msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100 border border-gray-700'
                  }`}>
                  {msg.content}
                </div>

                {/* Render Tool Calls (Debug View) */}
                {msg.tool_calls && msg.tool_calls.length > 0 && (
                  <div className="bg-gray-900 rounded-lg border border-gray-800 p-3 text-xs font-mono text-green-400">
                    <div className="flex items-center gap-2 text-gray-500 mb-2 pb-2 border-b border-gray-800">
                      <Terminal size={12} /> Tool Execution Log
                    </div>
                    {msg.tool_calls.map((tool, i) => (
                      <div key={i} className="mb-1 last:mb-0">
                        <span className="text-yellow-500">{tool.name}</span>
                        <span className="text-gray-500">(</span>
                        <span className="text-blue-300">{JSON.stringify(tool.args)}</span>
                        <span className="text-gray-500">)</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center shrink-0">
                  <User size={16} />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex items-center gap-2 text-gray-500 text-sm ml-12">
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-75"></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-150"></div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-800 bg-gray-900">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto relative">
            <input
              className="w-full bg-gray-800 text-gray-100 rounded-xl pl-4 pr-12 py-4 focus:ring-2 focus:ring-blue-600 outline-none border border-gray-700 placeholder-gray-500"
              placeholder="Ask the agent to do something..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="absolute right-2 top-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;