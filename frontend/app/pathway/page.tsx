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

interface ReasoningTraceItem {
  skill: string
  current_level: number
  required_level: number
  gap: number
  importance_weight: number
  relevance_tier: string
  priority_score: number
  included_in_path: boolean
  decision: string
}

interface PathwayData {
  pathway_id: string
  role: string
  total_modules: number
  estimated_hours: number
  modules: Module[]
  message?: string
  reasoning_trace?: ReasoningTraceItem[]
  summary?: {
    total_evaluated: number
    in_pathway: number
    excluded: number
    role: string
    formula: string
  }
}

export default function PathwayPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [pathway, setPathway] = useState<PathwayData | null>(null)
  const [quizResults, setQuizResults] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedModule, setExpandedModule] = useState<number | null>(null)
  const [showTrace, setShowTrace] = useState(false)

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

        {/* FEATURE 4: Reasoning Trace Panel - Toggle */}
        <div className={styles.section}>
          <button
            className="btn btn-outline"
            onClick={() => setShowTrace(!showTrace)}
            style={{ marginBottom: '1rem' }}
          >
            {showTrace ? '🔍 Hide Reasoning Trace' : '🔍 Show Reasoning Trace'}
          </button>

          {/* Reasoning Trace Panel */}
          {showTrace && pathway.reasoning_trace && pathway.reasoning_trace.length > 0 && (
            <div className={styles.reasoningPanel}>
              <h3 className={styles.sectionTitle}>Adaptive Engine — Reasoning Trace</h3>
              <p className={styles.formula}>
                <strong>Formula:</strong> priority = gap×0.5 + importance×0.3 + relevance×0.2
              </p>

              <div className={styles.traceTableWrapper}>
                <table className={styles.traceTable}>
                  <thead>
                    <tr>
                      <th>Skill</th>
                      <th>Current</th>
                      <th>Required</th>
                      <th>Gap</th>
                      <th>Importance</th>
                      <th>Relevance</th>
                      <th>Priority</th>
                      <th>Decision</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pathway.reasoning_trace.map((item, i) => (
                      <tr
                        key={i}
                        className={item.included_in_path ? styles.included : styles.excluded}
                      >
                        <td className={styles.skillName}>{item.skill.replace(/_/g, ' ')}</td>
                        <td>{item.current_level}/5</td>
                        <td>{item.required_level}/5</td>
                        <td>{item.gap}</td>
                        <td>{(item.importance_weight * 100).toFixed(0)}%</td>
                        <td>
                          <span className={`badge badge-${item.relevance_tier === 'critical' ? 'error' : item.relevance_tier === 'important' ? 'warning' : 'info'}`}>
                            {item.relevance_tier}
                          </span>
                        </td>
                        <td>{item.priority_score.toFixed(4)}</td>
                        <td>
                          <span className={item.included_in_path ? styles.includedLabel : styles.excludedLabel}>
                            {item.included_in_path ? '✅ In pathway' : '❌ Excluded'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {pathway.summary && (
                <p className={styles.traceSummary}>
                  <strong>Summary:</strong> {pathway.summary.in_pathway} skills in pathway •
                  {pathway.summary.excluded} excluded •
                  {pathway.summary.total_evaluated} total evaluated
                </p>
              )}
            </div>
          )}

          {showTrace && (!pathway.reasoning_trace || pathway.reasoning_trace.length === 0) && (
            <div className={styles.reasoningEmpty}>
              Reasoning trace is not available for this pathway yet. Regenerate your pathway to load the decision tree.
            </div>
          )}
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
