import React from 'react';
import { Button } from "@/components/ui/button";
import './App.css';

function App() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100">
        Welcome to the Modernized App
      </h1>
      <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
        This is a demonstration of the new UI.
      </p>
      <div className="mt-8">
        <Button>Get Started</Button>
      </div>
    </div>
  );
}

export default App;