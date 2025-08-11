"use client";

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

interface Assessment {
  id: number;
  summary: string;
  actions: string[];
  diff?: string;
}

export default function ImpactPage() {
  const params = useParams();
  const id = params?.id as string;
  const [assessment, setAssessment] = useState<Assessment | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login';
      return;
    }
    fetch((process.env.NEXT_PUBLIC_API_URL || '') + `/v1/impacts/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then(setAssessment)
      .catch(() => setAssessment(null));
  }, [id]);

  if (!assessment) return <p className="p-4">Loading...</p>;

  return (
    <main className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Impact Assessment</h1>
      <p>{assessment.summary}</p>
      <section>
        <h2 className="text-xl font-semibold">Actions</h2>
        <ul className="list-disc list-inside">
          {assessment.actions.map((a, idx) => (
            <li key={idx}>{a}</li>
          ))}
        </ul>
      </section>
      <section>
        <h2 className="text-xl font-semibold">Diff</h2>
        <pre className="bg-gray-200 p-2 overflow-auto">{assessment.diff}</pre>
      </section>
    </main>
  );
}
