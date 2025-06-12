import React, { useState, useEffect } from 'react';
import SettingsPage from './components/SettingsPage';
import { apiService } from './services/api';
import './App.css';

function App() {
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      await apiService.healthCheck();
      setConnected(true);
    } catch (error) {
      console.error('Connection failed:', error);
      setConnected(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-300">Connecting to Gmail Spam Bot...</p>
        </div>
      </div>
    );
  }

  if (!connected) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Connection Failed</h1>
          <p className="text-gray-300 mb-4">Unable to connect to the Gmail Spam Bot server.</p>
          <button 
            onClick={checkConnection}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Gmail Spam Bot</h1>
          <p className="text-gray-400">LM Studio Integration with Smart Model Switching</p>
        </div>
        
        <SettingsPage />
      </div>
    </div>
  );
}

export default App;