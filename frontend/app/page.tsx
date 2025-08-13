"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Change {
  id: number;
  summary: string;
}

export default function HomePage() {
  const [changes, setChanges] = useState<Change[]>([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login';
      return;
    }
    fetch((process.env.NEXT_PUBLIC_API_URL || '') + '/v1/changes', {
      headers: { 'X-API-Key': token },
    })
      .then((res) => res.json())
      .then((data) => setChanges(data.items || []))
      .catch(() => setChanges([]));
  }, []);

  return (
    <main className="p-4">
      <h1 className="text-2xl font-bold mb-4">Recent Regulatory Changes</h1>
      {changes.length === 0 ? (
        <p>No changes found.</p>
      ) : (
        <ul className="space-y-2">
          {changes.map((change) => (
            <li key={change.id} className="p-2 border rounded">
              <Link href={`/impact/${change.id}`}>{change.summary}</Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
