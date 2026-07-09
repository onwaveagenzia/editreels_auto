// dashboard/pages/index.tsx
import React, { useEffect, useState } from 'react';
import styles from '../styles/Dashboard.module.css';

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

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'active' | 'completed' | 'stats'>('active');

  // Fetch data ogni 2 secondi
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [jobsRes, statsRes] = await Promise.all([
          fetch(`${API_URL}/api/jobs?limit=100`),
          fetch(`${API_URL}/api/stats`)
        ]);

        if (!jobsRes.ok || !statsRes.ok) throw new Error('API error');

        const jobsData = await jobsRes.json();
        const statsData = await statsRes.json();

        setJobs(jobsData.jobs || []);
        setStats(statsData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const activeJobs = jobs.filter(j => j.status === 'processing' || j.status === 'queued');
  const completedJobs = jobs.filter(j => j.status === 'completed');
  const failedJobs = jobs.filter(j => j.status === 'error');

  const getStatusIcon = (status: string) => {
    const icons: Record<string, string> = {
      'queued': '⚪',
      'processing': '🟡',
      'completed': '🟢',
      'error': '🔴',
      'cancelled': '⚫'
    };
    return icons[status] || '❓';
  };

  const getPresetColor = (preset: string) => {
    const colors: Record<string, string> = {
      'social_media': '#FF6B6B',
      'educational': '#4ECDC4',
      'corporate': '#45B7D1',
      'testimonial': '#FFA07A'
    };
    return colors[preset] || '#999';
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString();
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1>🎬 ONWAVE Processing Dashboard</h1>
          <div className={styles.headerStats}>
            {stats && (
              <>
                <div className={styles.statBadge} style={{ backgroundColor: '#4ECDC4' }}>
                  <span className={styles.statValue}>{stats.processing}</span>
                  <span className={styles.statLabel}>Processing</span>
                </div>
                <div className={styles.statBadge} style={{ backgroundColor: '#FFB347' }}>
                  <span className={styles.statValue}>{stats.queued}</span>
                  <span className={styles.statLabel}>Queued</span>
                </div>
                <div className={styles.statBadge} style={{ backgroundColor: '#90EE90' }}>
                  <span className={styles.statValue}>{stats.completed}</span>
                  <span className={styles.statLabel}>Completed</span>
                </div>
                <div className={styles.statBadge} style={{ backgroundColor: '#FF6B6B' }}>
                  <span className={styles.statValue}>{stats.failed}</span>
                  <span className={styles.statLabel}>Failed</span>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      {error && (
        <div className={styles.errorBanner}>
          ⚠️ {error}
        </div>
      )}

      {/* Tabs */}
      <nav className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'active' ? styles.active : ''}`}
          onClick={() => setActiveTab('active')}
        >
          🟡 Active Jobs ({activeJobs.length})
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'completed' ? styles.active : ''}`}
          onClick={() => setActiveTab('completed')}
        >
          🟢 Completed ({completedJobs.length})
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'stats' ? styles.active : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          📊 Statistics
        </button>
      </nav>

      {/* Content */}
      <main className={styles.main}>
        {loading && activeTab === 'active' && <p className={styles.loading}>Loading...</p>}

        {/* Active Jobs */}
        {activeTab === 'active' && (
          <div className={styles.jobsList}>
            {activeJobs.length === 0 ? (
              <p className={styles.empty}>No active jobs</p>
            ) : (
              activeJobs.map(job => <JobCard key={job.id} job={job} />)
            )}
          </div>
        )}

        {/* Completed Jobs */}
        {activeTab === 'completed' && (
          <div className={styles.jobsList}>
            {completedJobs.length === 0 ? (
              <p className={styles.empty}>No completed jobs</p>
            ) : (
              completedJobs.map(job => <JobCard key={job.id} job={job} />)
            )}
          </div>
        )}

        {/* Statistics */}
        {activeTab === 'stats' && stats && (
          <div className={styles.statsContainer}>
            <div className={styles.statCard}>
              <h3>📊 Overview</h3>
              <p>Total Videos: <strong>{stats.total_jobs}</strong></p>
              <p>Completed: <strong>{stats.completed}</strong></p>
              <p>Average Time: <strong>{formatTime(stats.average_processing_time_seconds)}</strong></p>
              <p>Total Output: <strong>{stats.total_output_size_mb} MB</strong></p>
            </div>

            <div className={styles.statCard}>
              <h3>⏱️ Performance</h3>
              <p>Processing Now: <strong>{stats.processing}</strong></p>
              <p>Queued: <strong>{stats.queued}</strong></p>
              <p>Failed: <strong>{stats.failed}</strong></p>
            </div>

            <div className={styles.statCard}>
              <h3>💡 Tips</h3>
              <ul>
                <li>Use Social Media preset for TikTok/Reels</li>
                <li>Educational preset adds auto-chapters</li>
                <li>Corporate preset keeps subtle animations</li>
                <li>Monitor progress from dashboard</li>
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

interface JobCardProps {
  job: Job;
}

function JobCard({ job }: JobCardProps) {
  const isProcessing = job.status === 'processing' || job.status === 'queued';
  const elapsedSeconds = job.started ? 
    (new Date().getTime() - new Date(job.started).getTime()) / 1000 : 0;

  return (
    <div className={styles.jobCard} style={{
      borderLeft: `4px solid ${job.status === 'error' ? '#FF6B6B' : 
                             job.status === 'completed' ? '#90EE90' : 
                             job.status === 'processing' ? '#4ECDC4' : '#FFB347'}`
    }}>
      <div className={styles.jobHeader}>
        <div className={styles.jobTitle}>
          <span className={styles.statusIcon}>
            {job.status === 'queued' ? '⚪' :
             job.status === 'processing' ? '🟡' :
             job.status === 'completed' ? '🟢' :
             job.status === 'error' ? '🔴' : '⚫'}
          </span>
          <div>
            <h3>{job.video_path.split('/').pop()}</h3>
            <p className={styles.jobMeta}>
              Preset: <span style={{ color: getPresetColor(job.preset) }}>
                {job.preset}
              </span> • {new Date(job.created).toLocaleDateString()}
            </p>
          </div>
        </div>
        <span className={styles.jobStatus}>{job.status.toUpperCase()}</span>
      </div>

      {isProcessing && (
        <div className={styles.progressContainer}>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${job.progress}%` }}
            />
          </div>
          <div className={styles.progressText}>
            {job.progress}% • {formatTime(elapsedSeconds)} elapsed
          </div>
        </div>
      )}

      {job.error && (
        <div className={styles.errorMessage}>
          {job.error}
        </div>
      )}

      {job.results.length > 0 && (
        <div className={styles.results}>
          <h4>Results ({job.results.length} files)</h4>
          <div className={styles.resultsList}>
            {job.results.map((file, i) => (
              <div key={i} className={styles.resultItem}>
                📄 {file.split('/').pop()}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={styles.jobFooter}>
        {job.status === 'processing' && (
          <button className={styles.btn} style={{ backgroundColor: '#FF6B6B' }}>
            Cancel
          </button>
        )}
        {job.status === 'error' && (
          <button className={styles.btn} style={{ backgroundColor: '#FFB347' }}>
            Retry
          </button>
        )}
        {job.status === 'completed' && (
          <>
            <button className={styles.btn} style={{ backgroundColor: '#4ECDC4' }}>
              Download
            </button>
            <button className={styles.btn} style={{ backgroundColor: '#45B7D1' }}>
              Share
            </button>
          </>
        )}
      </div>
    </div>
  );
}
