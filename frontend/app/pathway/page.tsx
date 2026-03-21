'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import styles from './page.module.css'

interface Module {
  order: number
  skill_id: string
  skill_name: string
  current_level: number
  target_level: number
  gap: number
  priority_score: number
  estimated_hours: number
  reason: string
  resources: string[]
}

interface PathwayData {
  pathway_id: string
  role: string
  total_modules: number
  estimated_hours: number
  modules: Module[]
  message?: string
}

export default function PathwayPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [pathway, setPathway] = useState<PathwayData | null>(null)
  const [quizResults, setQuizResults] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedModule, setExpandedModule] = useState<number | null>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    const generatePathway = async () => {
      const querySessionId = searchParams.get('session_id')
      const sessionId = querySessionId || sessionStorage.getItem('pathforge_session_id')
      const storedResults = sessionStorage.getItem('pathforge_quiz_results')

      if (!sessionId) {
        router.push('/onboarding')
        return
      }

      sessionStorage.setItem('pathforge_session_id', sessionId)

      let resultsPayload: any = null
      if (storedResults) {
        resultsPayload = JSON.parse(storedResults)
      } else {
        try {
          const resultsRes = await fetch(`${API_URL}/api/quiz/${sessionId}/results`)
          if (resultsRes.ok) {
            resultsPayload = await resultsRes.json()
            sessionStorage.setItem('pathforge_quiz_results', JSON.stringify(resultsPayload))
          }
        } catch {
          // Pathway generation can still run; results panel will remain hidden.
        }
      }

      if (resultsPayload) setQuizResults(resultsPayload)

      try {
        const res = await fetch(`${API_URL}/api/pathway/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId }),
        })

        if (!res.ok) throw new Error('Failed to generate pathway')
        const data = await res.json()
        setPathway(data)
      } catch (err: any) {
        setError(err.message || 'Failed to generate pathway')
      } finally {
        setLoading(false)
      }
    }

    generatePathway()
  }, [API_URL, router, searchParams])

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingState}>
          <div className={styles.loadingSpinner}></div>
          <h2>Forging Your Path...</h2>
          <p>Running adaptive engine: gap calculator → priority scorer → topological sort</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingState}>
          <h2>⚠️ Error</h2>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={() => router.push('/onboarding')}>
            Start Over
          </button>
        </div>
      </div>
    )
  }

  if (!pathway) return null

  const totalGap = pathway.modules.reduce((sum, m) => sum + m.gap, 0)

  return (
    <div className={styles.page}>
      {/* Header */}
      <nav className={styles.topBar}>
        <a href="/" className={styles.backLink}>◆ PathForge</a>
        <span className="badge badge-success">✓ Pathway Generated</span>
      </nav>

      <div className="container">
        {/* Hero Stats */}
        <div className={styles.dashboardHeader}>
          <div>
            <h1 className={styles.dashTitle}>
              Your <span className="text-gradient">{pathway.role}</span> Path
            </h1>
            {pathway.message ? (
              <p className={styles.dashSubtitle}>{pathway.message}</p>
            ) : (
              <p className={styles.dashSubtitle}>
                Personalized learning pathway with {pathway.total_modules} modules
                based on your verified skill levels.
              </p>
            )}
          </div>
        </div>

        {/* Stats Cards */}
        <div className={styles.statsGrid}>
          <div className={`card ${styles.statCard}`}>
            <span className={styles.statIcon}>📚</span>
            <span className={styles.statValue}>{pathway.total_modules}</span>
            <span className={styles.statLabel}>Modules</span>
          </div>
          <div className={`card ${styles.statCard}`}>
            <span className={styles.statIcon}>⏰</span>
            <span className={styles.statValue}>{pathway.estimated_hours}h</span>
            <span className={styles.statLabel}>Estimated</span>
          </div>
          <div className={`card ${styles.statCard}`}>
            <span className={styles.statIcon}>📊</span>
            <span className={styles.statValue}>{totalGap}</span>
            <span className={styles.statLabel}>Total Gap</span>
          </div>
          <div className={`card ${styles.statCard}`}>
            <span className={styles.statIcon}>🎯</span>
            <span className={styles.statValue}>
              {quizResults ? `${quizResults.total_score}/${quizResults.max_score}` : '—'}
            </span>
            <span className={styles.statLabel}>Quiz Score</span>
          </div>
        </div>

        {/* Quiz Results Breakdown */}
        {quizResults && (
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Skill Verification Results</h3>
            <div className={styles.skillResults}>
              {Object.entries(quizResults.skill_scores).map(([skillId, scores]: [string, any]) => (
                <div key={skillId} className={styles.skillResult}>
                  <span className={styles.skillResultName}>{skillId.replace(/_/g, ' ')}</span>
                  <div className={styles.skillResultBar}>
                    <div
                      className={styles.skillResultFill}
                      style={{ width: `${(scores.verified_level / 5) * 100}%` }}
                    ></div>
                  </div>
                  <span className={styles.skillResultLevel}>
                    {scores.correct}/{scores.total} — Lvl {scores.verified_level}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Module Timeline */}
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Learning Pathway</h3>
          <div className={styles.timeline}>
            {pathway.modules.map((module, idx) => (
              <div
                key={module.skill_id}
                className={`${styles.moduleCard} ${expandedModule === idx ? styles.moduleExpanded : ''}`}
                onClick={() => setExpandedModule(expandedModule === idx ? null : idx)}
              >
                <div className={styles.moduleHeader}>
                  <div className={styles.moduleOrder}>{module.order}</div>
                  <div className={styles.moduleInfo}>
                    <h4 className={styles.moduleName}>{module.skill_name}</h4>
                    <div className={styles.moduleMeta}>
                      <span className={`badge ${module.gap >= 3 ? 'badge-error' : module.gap >= 2 ? 'badge-warning' : 'badge-primary'}`}>
                        Gap: {module.gap}
                      </span>
                      <span className={styles.moduleHours}>~{module.estimated_hours}h</span>
                      <span className={styles.modulePriority}>
                        Priority: {(module.priority_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className={styles.levelDisplay}>
                    <span className={styles.levelCurrent}>{module.current_level}</span>
                    <span className={styles.levelArrow}>→</span>
                    <span className={styles.levelTarget}>{module.target_level}</span>
                  </div>
                </div>

                {expandedModule === idx && (
                  <div className={styles.moduleDetails}>
                    <div className={styles.moduleReason}>
                      <strong>💡 Why:</strong> {module.reason}
                    </div>
                    <div className={styles.moduleResources}>
                      <strong>📖 Suggested Resources:</strong>
                      <ul>
                        {module.resources.map((res, i) => (
                          <li key={i}>{res}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className={styles.actions}>
          <button
            className="btn btn-ghost"
            onClick={() => router.push('/onboarding')}
          >
            ← Try Different Role
          </button>
          <button
            className="btn btn-primary"
            onClick={() => window.print()}
          >
            📄 Export Pathway
          </button>
        </div>
      </div>
    </div>
  )
}
