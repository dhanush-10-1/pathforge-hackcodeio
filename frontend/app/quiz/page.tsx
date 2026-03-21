'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import styles from './page.module.css'
import { getQuizSession } from '@/lib/api'

interface Question {
  id: string
  skill_id: string
  skill_name: string
  question: string
  options: string[]
  difficulty: number
}

export default function QuizPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [questions, setQuestions] = useState<Question[]>([])
  const [sessionId, setSessionId] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [returnUrl, setReturnUrl] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    const startQuiz = async () => {
      const querySessionId = searchParams.get('session_id') || ''
      const queryRole = searchParams.get('role') || ''
      const queryReturnUrl = searchParams.get('return_url') || ''
      if (queryRole) {
        sessionStorage.setItem('pathforge_role', queryRole)
      }
      if (queryReturnUrl) {
        setReturnUrl(queryReturnUrl)
      }

      const role = queryRole || sessionStorage.getItem('pathforge_role') || ''

      try {
        if (querySessionId) {
          const existing = await getQuizSession(querySessionId)
          setSessionId(existing.session_id)
          setQuestions(existing.questions)
          setTargetRole(existing.target_role || role)
          if (existing.target_role) {
            sessionStorage.setItem('pathforge_role', existing.target_role)
          }
          return
        }

        if (!role) {
          router.push('/onboarding')
          return
        }

        const res = await fetch(`${API_URL}/api/quiz/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_role: role }),
        })

        if (!res.ok) throw new Error('Failed to start quiz')

        const data = await res.json()
        setSessionId(data.session_id)
        setQuestions(data.questions)
        setTargetRole(data.target_role || role)
      } catch (err: any) {
        setError(err.message || 'Failed to load quiz')
      } finally {
        setLoading(false)
      }
    }

    startQuiz()
  }, [API_URL, router, searchParams])

  const currentQ = questions[currentIndex]
  const progress = questions.length > 0 ? ((currentIndex + 1) / questions.length) * 100 : 0

  const handleSelect = (optIndex: number) => {
    setSelectedOption(optIndex)
  }

  const handleNext = () => {
    if (selectedOption === null || !currentQ) return

    const newAnswers = { ...answers, [currentQ.id]: selectedOption }
    setAnswers(newAnswers)
    setSelectedOption(null)

    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1)
    } else {
      handleSubmit(newAnswers)
    }
  }

  const handleSubmit = async (finalAnswers: Record<string, number>) => {
    setSubmitting(true)
    try {
      const res = await fetch(`${API_URL}/api/quiz/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, answers: finalAnswers }),
      })

      if (!res.ok) throw new Error('Failed to submit quiz')

      const results = await res.json()
      sessionStorage.setItem('pathforge_session_id', sessionId)
      sessionStorage.setItem('pathforge_quiz_results', JSON.stringify(results))
      if (returnUrl) {
        const sep = returnUrl.includes('?') ? '&' : '?'
        window.location.href = `${returnUrl}${sep}session_id=${encodeURIComponent(sessionId)}`
      } else {
        router.push('/pathway')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit quiz')
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingState}>
          <div className={styles.loadingSpinner}></div>
          <h2>Generating Your Quiz...</h2>
          <p>Creating targeted questions based on your skills and target role.</p>
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
            Go Back
          </button>
        </div>
      </div>
    )
  }

  if (submitting) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingState}>
          <div className={styles.loadingSpinner}></div>
          <h2>Analyzing Your Responses...</h2>
          <p>Verifying skill levels and preparing your adaptive pathway.</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      {/* Top Bar */}
      <div className={styles.quizHeader}>
        <div className={styles.quizMeta}>
          <span className="badge badge-primary">
            Question {currentIndex + 1} of {questions.length}
          </span>
          {targetRole && (
            <span className="badge badge-success">{targetRole}</span>
          )}
          {currentQ && (
            <span className="badge badge-warning">
              {currentQ.skill_name}
            </span>
          )}
        </div>
        <div className="progress-bar" style={{ maxWidth: 400 }}>
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
      </div>

      {/* Question Card */}
      {currentQ && (
        <div className="container">
          <div className={styles.questionCard} key={currentQ.id}>
            <div className={styles.difficultyBadge}>
              {'⭐'.repeat(currentQ.difficulty)}
            </div>
            <h2 className={styles.questionText}>{currentQ.question}</h2>

            <div className={styles.optionsGrid}>
              {currentQ.options.map((option, idx) => (
                <button
                  key={idx}
                  className={`${styles.optionBtn} ${selectedOption === idx ? styles.optionSelected : ''}`}
                  onClick={() => handleSelect(idx)}
                  id={`option-${idx}`}
                >
                  <span className={styles.optionLetter}>
                    {String.fromCharCode(65 + idx)}
                  </span>
                  <span className={styles.optionText}>{option}</span>
                </button>
              ))}
            </div>

            <div className={styles.quizActions}>
              <span className={styles.quizHint}>
                {selectedOption === null ? 'Select an answer to continue' : ''}
              </span>
              <button
                className="btn btn-primary btn-lg"
                onClick={handleNext}
                disabled={selectedOption === null}
                id="next-question-btn"
              >
                {currentIndex === questions.length - 1 ? 'Submit Quiz ✓' : 'Next →'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
