import React, { useEffect, useState, useCallback } from 'react';
import styles from '../styles/Dashboard.module.css';

/* ───────── Types ───────── */

interface Job {
  id: string;
  video_path: string;
  preset: string;
  status: 'queued' | 'processing' | 'completed' | 'error' | 'cancelled';
  progress: number;
  created: string;
  started?: string;
  completed?: string;
  error?: string;
  results: string[];
  options?: Record<string, unknown>;
}

interface Stats {
  total_jobs: number;
  completed: number;
  processing: number;
  failed: number;
  queued: number;
  average_processing_time_seconds: number;
  total_output_size_mb: number;
}

/* ───────── Helpers (module-scope) ───────── */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

function getPresetColor(preset: string): string {
  const colors: Record<string, string> = {
    social_media: '#FF6B6B',
    educational: '#4ECDC4',
    corporate: '#45B7D1',
    testimonial: '#FFA07A',
  };
  return colors[preset] || '#999';
}

function formatTime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

function statusIcon(status: string): string {
  const map: Record<string, string> = {
    queued: '⚪',
    processing: '🟡',
    completed: '🟢',
    error: '🔴',
    cancelled: '⚫',
  };
  return map[status] || '❓';
}

function statusBorderColor(status: string): string {
  const map: Record<string, string> = {
    error: '#FF6B6B',
    completed: '#10b981',
    processing: '#4ECDC4',
    queued: '#FFB347',
  };
  return map[status] || '#334155';
}

/* ───────── JobCard ───────── */

function JobCard({
  job,
  onCancel,
  onRetry,
}: {
  job: Job;
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
}) {
  const isProcessing = job.status === 'processing' || job.status === 'queued';
  const elapsed = job.started
    ? (Date.now() - new Date(job.started).getTime()) / 1000
    : 0;

  return (
    <div
      className={styles.jobCard}
      style={{ borderLeft: `4px solid ${statusBorderColor(job.status)}` }}
    >
      {/* header */}
      <div className={styles.jobHeader}>
        <div className={styles.jobTitle}>
          <span className={styles.statusIcon}>{statusIcon(job.status)}</span>
          <div>
            <h3>{job.video_path.split('/').pop()}</h3>
            <p className={styles.jobMeta}>
              Preset:{' '}
              <span style={{ color: getPresetColor(job.preset) }}>
                {job.preset.replace('_', ' ')}
              </span>{' '}
              &middot; {new Date(job.created).toLocaleDateString()}
            </p>
          </div>
        </div>
        <span className={styles.jobStatus}>{job.status.toUpperCase()}</span>
      </div>

      {/* progress */}
      {isProcessing && (
        <div className={styles.progressContainer}>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${job.progress}%` }}
            />
          </div>
          <div className={styles.progressText}>
            {job.progress}% &middot; {formatTime(elapsed)} elapsed
          </div>
        </div>
      )}

      {/* error */}
      {job.error && <div className={styles.errorMessage}>{job.error}</div>}

      {/* results */}
      {job.results && job.results.length > 0 && (
        <div className={styles.results}>
          <h4>Results ({job.results.length} files)</h4>
          <div className={styles.resultsList}>
            {job.results.map((f, i) => (
              <div key={i} className={styles.resultItem}>
                📄 {f.split('/').pop()}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* actions */}
      <div className={styles.jobFooter}>
        {job.status === 'processing' && (
          <button
            className={styles.btn}
            style={{ backgroundColor: '#FF6B6B' }}
            onClick={() => onCancel(job.id)}
          >
            Cancel
          </button>
        )}
        {job.status === 'error' && (
          <button
            className={styles.btn}
            style={{ backgroundColor: '#FFB347' }}
            onClick={() => onRetry(job.id)}
          >
            Retry
          </button>
        )}
        {job.status === 'completed' && (
          <>
            <button
              className={styles.btn}
              style={{ backgroundColor: '#4ECDC4' }}
            >
              Download
            </button>
            <button
              className={styles.btn}
              style={{ backgroundColor: '#45B7D1' }}
            >
              Share
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/* ───────── Dashboard (main page) ───────── */

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'active' | 'completed' | 'stats'>('active');

  /* fetch loop */
  const fetchData = useCallback(async () => {
    try {
      const [jRes, sRes] = await Promise.all([
        fetch(`${API_URL}/api/jobs?limit=100`),
        fetch(`${API_URL}/api/stats`),
      ]);
      if (!jRes.ok || !sRes.ok) throw new Error('API error');
      const jData = await jRes.json();
      const sData = await sRes.json();
      setJobs(jData.jobs || []);
      setStats(sData);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Connection failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 3000);
    return () => clearInterval(id);
  }, [fetchData]);

  /* actions */
  const cancelJob = async (jobId: string) => {
    await fetch(`${API_URL}/api/jobs/${jobId}/cancel`, { method: 'POST' });
    fetchData();
  };
  const retryJob = async (jobId: string) => {
    await fetch(`${API_URL}/api/jobs/${jobId}/retry`, { method: 'POST' });
    fetchData();
  };

  /* derived */
  const active = jobs.filter(
    (j) => j.status === 'processing' || j.status === 'queued'
  );
  const completed = jobs.filter((j) => j.status === 'completed');

  return (
    <div className={styles.container}>
      {/* ── header ── */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1>🎬 ONWAVE EditReels Auto</h1>
          {stats && (
            <div className={styles.headerStats}>
              <div className={styles.statBadge} style={{ backgroundColor: '#4ECDC4' }}>
                <span className={styles.statValue}>{stats.processing}</span>
                <span className={styles.statLabel}>Processing</span>
              </div>
              <div className={styles.statBadge} style={{ backgroundColor: '#FFB347' }}>
                <span className={styles.statValue}>{stats.queued}</span>
                <span className={styles.statLabel}>Queued</span>
              </div>
              <div className={styles.statBadge} style={{ backgroundColor: '#10b981' }}>
                <span className={styles.statValue}>{stats.completed}</span>
                <span className={styles.statLabel}>Completed</span>
              </div>
              <div className={styles.statBadge} style={{ backgroundColor: '#FF6B6B' }}>
                <span className={styles.statValue}>{stats.failed}</span>
                <span className={styles.statLabel}>Failed</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {error && <div className={styles.errorBanner}>⚠️ {error}</div>}

      {/* ── tabs ── */}
      <nav className={styles.tabs}>
        {(['active', 'completed', 'stats'] as const).map((t) => (
          <button
            key={t}
            className={`${styles.tab} ${tab === t ? styles.active : ''}`}
            onClick={() => setTab(t)}
          >
            {t === 'active'
              ? `🟡 Active (${active.length})`
              : t === 'completed'
              ? `🟢 Completed (${completed.length})`
              : '📊 Statistics'}
          </button>
        ))}
      </nav>

      {/* ── content ── */}
      <main className={styles.main}>
        {loading && tab === 'active' && (
          <p className={styles.loading}>Loading…</p>
        )}

        {tab === 'active' && (
          <div className={styles.jobsList}>
            {active.length === 0 ? (
              <p className={styles.empty}>No active jobs</p>
            ) : (
              active.map((j) => (
                <JobCard
                  key={j.id}
                  job={j}
                  onCancel={cancelJob}
                  onRetry={retryJob}
                />
              ))
            )}
          </div>
        )}

        {tab === 'completed' && (
          <div className={styles.jobsList}>
            {completed.length === 0 ? (
              <p className={styles.empty}>No completed jobs yet</p>
            ) : (
              completed.map((j) => (
                <JobCard
                  key={j.id}
                  job={j}
                  onCancel={cancelJob}
                  onRetry={retryJob}
                />
              ))
            )}
          </div>
        )}

        {tab === 'stats' && stats && (
          <div className={styles.statsContainer}>
            <div className={styles.statCard}>
              <h3>📊 Overview</h3>
              <p>
                Total Videos <strong>{stats.total_jobs}</strong>
              </p>
              <p>
                Completed <strong>{stats.completed}</strong>
              </p>
              <p>
                Avg Time{' '}
                <strong>
                  {formatTime(stats.average_processing_time_seconds)}
                </strong>
              </p>
              <p>
                Total Output <strong>{stats.total_output_size_mb} MB</strong>
              </p>
            </div>
            <div className={styles.statCard}>
              <h3>⏱️ Performance</h3>
              <p>
                Processing Now <strong>{stats.processing}</strong>
              </p>
              <p>
                Queued <strong>{stats.queued}</strong>
              </p>
              <p>
                Failed <strong>{stats.failed}</strong>
              </p>
            </div>
            <div className={styles.statCard}>
              <h3>💡 Tips</h3>
              <ul>
                <li>Social Media preset is optimised for TikTok / Reels</li>
                <li>Educational preset adds auto-chapters</li>
                <li>Corporate preset uses subtle animations</li>
                <li>Monitor live progress from the Active tab</li>
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
