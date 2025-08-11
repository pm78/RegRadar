"use client";

import { useState } from 'react';

export default function LoginPage() {
  const [password, setPassword] = useState('');

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === process.env.NEXT_PUBLIC_APP_PASSWORD) {
      localStorage.setItem('token', password);
      window.location.href = '/';
    } else {
      alert('Invalid password');
    }
  };

  return (
    <main className="flex items-center justify-center h-screen">
      <form onSubmit={submit} className="p-6 bg-white shadow rounded space-y-4">
        <h1 className="text-xl font-bold">Login</h1>
        <input
          type="password"
          className="border p-2 w-64"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
        />
        <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">
          Sign in
        </button>
      </form>
    </main>
  );
}
