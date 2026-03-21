'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'
import { buildExternalQuizUrl, startAdaptiveQuizSession } from '@/lib/api'

const ROLES = [
  { id: 'backend_engineer', title: 'Backend Engineer', icon: 'API', desc: 'APIs, databases, server-side logic' },
  { id: 'frontend_engineer', title: 'Frontend Engineer', icon: 'UI', desc: 'UI/UX, React, interactive interfaces' },
  { id: 'fullstack_engineer', title: 'Full Stack Engineer', icon: 'FS', desc: 'End-to-end application development' },
  { id: 'data_engineer', title: 'Data Engineer', icon: 'DE', desc: 'Pipelines, warehousing, data infra' },
  { id: 'ml_engineer', title: 'ML Engineer', icon: 'ML', desc: 'Models, training, AI systems' },
  { id: 'devops_engineer', title: 'DevOps Engineer', icon: 'OPS', desc: 'CI/CD, infrastructure, reliability' },
]

const SAMPLE_RESUME = `John Doe - Software Developer
3+ years of experience in full-stack web development.

Skills: Python, JavaScript, React, Node.js, PostgreSQL, Docker, Git, REST API design
Experience with FastAPI and Django for backend development.
Built and deployed microservices using Docker and AWS.
Familiar with machine learning basics and data analysis with pandas.
Proficient in HTML, CSS, and Tailwind CSS.
Worked in Agile teams using Scrum methodology.`

const DEMO_USER_ID = 'demo-user'
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type ExtractedSkill = {
  skill_id: string
  name: string
  level: number
  category: string
  relevance?: 'critical' | 'important' | 'peripheral' | 'irrelevant' | 'unknown'
}

type ExtractedProfile = {
  resume_id: string
  skills: ExtractedSkill[]
  experience_years?: number
  domain?: string
  skill_experience?: Record<string, number>
}

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [selectedRole, setSelectedRole] = useState('')
  const [inputMode, setInputMode] = useState<'upload' | 'text'>('upload')
  const [resumeText, setResumeText] = useState('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [extractedProfile, setExtractedProfile] = useState<ExtractedProfile | null>(null)
  const [quizSessionId, setQuizSessionId] = useState('')
  const [externalQuizUrl, setExternalQuizUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const resumeWordCount = useMemo(() => {
    return resumeText.trim() ? resumeText.trim().split(/\s+/).length : 0
  }, [resumeText])

  const resumeCharCount = resumeText.length

  const moveToResumeStep = () => {
    if (!selectedRole) {
      setError('Please select a target role before continuing.')
      return
    }
    sessionStorage.setItem('pathforge_role', selectedRole)
    setError('')
    setStep(2)
  }

  const buildClaimedLevels = (skills: ExtractedSkill[]) => {
    const claimed: Record<string, number> = {}
    for (const s of skills) {
      claimed[s.skill_id] = s.level
    }
    return claimed
  }

  const handleResumeSubmit = async (fileToUpload?: File) => {
    const file = fileToUpload || resumeFile
    if (!resumeText.trim() && !file) {
      setError('Please paste your resume text or upload a file.')
      return
    }

    if (!selectedRole) {
      setError('Please select a role first.')
      setStep(1)
      return
    }

    setLoading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('user_id', DEMO_USER_ID)
      formData.append('target_role', selectedRole)
      if (file) {
        formData.append('file', file)
      }
      if (resumeText.trim()) {
        formData.append('resume_text', resumeText)
      }

      const uploadRes = await fetch(`${API_URL}/api/resume/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!uploadRes.ok) {
        const errData = await uploadRes.json().catch(() => ({}))
        throw new Error(errData.detail || 'Failed to process resume')
      }

      const profile: ExtractedProfile = await uploadRes.json()
      setExtractedProfile(profile)

      const quizSession = await startAdaptiveQuizSession(
        selectedRole,
        DEMO_USER_ID,
        profile.experience_years ?? null,
        buildClaimedLevels(profile.skills || [])
      )

      const returnUrl = `${window.location.origin}/pathway`
      const quizUrl = buildExternalQuizUrl({
        sessionId: quizSession.session_id,
        role: selectedRole,
        returnUrl,
      })

      setQuizSessionId(quizSession.session_id)
      setExternalQuizUrl(quizUrl)

      sessionStorage.setItem('pathforge_session_id', quizSession.session_id)
      sessionStorage.setItem('pathforge_skills', JSON.stringify(profile))

      setStep(3)
    } catch (err: any) {
      setError(err.message || 'Failed to process onboarding flow. Ensure backend and ML services are running.')
    } finally {
      setLoading(false)
    }
  }

  const copyQuizLink = async () => {
    if (!externalQuizUrl) return
    try {
      await navigator.clipboard.writeText(externalQuizUrl)
    } catch {
      setError('Unable to copy link. Please copy it manually from the input field.')
    }
  }

  return (
    <div className={styles.page}>
      <nav className={styles.topBar}>
        <a href='/' className={styles.backLink}>Back to PathForge</a>
        <div className={styles.progressSteps}>
          <div className={`${styles.progressStep} ${step >= 1 ? styles.active : ''}`}>
            <span className={styles.progressDot}>1</span> Role
          </div>
          <div className={styles.progressLine}></div>
          <div className={`${styles.progressStep} ${step >= 2 ? styles.active : ''}`}>
            <span className={styles.progressDot}>2</span> Resume
          </div>
          <div className={styles.progressLine}></div>
          <div className={`${styles.progressStep} ${step >= 3 ? styles.active : ''}`}>
            <span className={styles.progressDot}>3</span> Quiz Link
          </div>
        </div>
      </nav>

      <div className={styles.stepContent}>
        {step === 1 && (
          <div>
            <div className={styles.stepHeader}>
              <h1>Select Your Target Role</h1>
              <p className={styles.stepDesc}>Pick your target role first. Resume and skill assessment come next.</p>
            </div>

            <div className={styles.roleSelectWrap}>
              <label htmlFor='role-select' className='label'>Choose a role from the dropdown</label>
              <select
                id='role-select'
                className={`${styles.roleSelect} input`}
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
              >
                <option value=''>Select target role...</option>
                {ROLES.map((role) => (
                  <option key={role.id} value={role.title}>{role.title}</option>
                ))}
              </select>
            </div>

            <div className={styles.roleGrid}>
              {ROLES.map((role) => (
                <button
                  key={role.id}
                  type='button'
                  className={`${styles.roleCard} ${selectedRole === role.title ? styles.roleSelected : ''}`}
                  onClick={() => setSelectedRole(role.title)}
                >
                  <span className={styles.roleIcon}>{role.icon}</span>
                  <span className={styles.roleTitle}>{role.title}</span>
                  <span className={styles.roleDesc}>{role.desc}</span>
                </button>
              ))}
            </div>

            <div className={styles.stepActions}>
              <span></span>
              <button className='btn btn-primary btn-lg' type='button' onClick={moveToResumeStep} disabled={!selectedRole}>
                Continue to Resume
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <div className={styles.stepHeader}>
              <span className='badge badge-primary'>Role: {selectedRole}</span>
              <h1>Upload Resume for Skill Assessment</h1>
              <p className={styles.stepDesc}>We will extract your skills and experience, then generate your quiz link.</p>
            </div>

            <div className={styles.modeSwitch}>
              <button
                type='button'
                className={`${styles.modeButton} ${inputMode === 'upload' ? styles.modeButtonActive : ''}`}
                onClick={() => setInputMode('upload')}
              >
                Upload file
              </button>
              <button
                type='button'
                className={`${styles.modeButton} ${inputMode === 'text' ? styles.modeButtonActive : ''}`}
                onClick={() => setInputMode('text')}
              >
                Paste text
              </button>
            </div>

            {inputMode === 'upload' && (
              <>
                <div
                  className={`${styles.dropZone} ${isDragging ? styles.dragging : ''}`}
                  onDragOver={(e) => {
                    e.preventDefault()
                    setIsDragging(true)
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={(e) => {
                    e.preventDefault()
                    setIsDragging(false)
                    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                      setResumeFile(e.dataTransfer.files[0])
                    }
                  }}
                  onClick={() => document.getElementById('file-upload')?.click()}
                >
                  {resumeFile ? (
                    <>
                      <p>File selected: <strong>{resumeFile.name}</strong></p>
                      <p className={styles.dropHint}>Size: {(resumeFile.size / 1024 / 1024).toFixed(2)} MB</p>
                    </>
                  ) : (
                    <>
                      <p>Drag and drop your resume here, or click to browse</p>
                      <p className={styles.dropHint}>Supported: .pdf .txt .png .jpg .jpeg .webp</p>
                    </>
                  )}
                  <input
                    id='file-upload'
                    type='file'
                    accept='.pdf,.txt,.png,.jpg,.jpeg,.webp'
                    style={{ display: 'none' }}
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        setResumeFile(e.target.files[0])
                      }
                    }}
                  />
                </div>

                <div className={styles.divider}><span>OR</span></div>
              </>
            )}

            {inputMode === 'text' && (
              <>
                <textarea
                  className='input'
                  placeholder='Paste your resume content here...'
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  rows={10}
                  id='resume-textarea'
                />
                <div className={styles.textMetaRow}>
                  <span className={styles.textMeta}>{resumeWordCount} words</span>
                  <span className={styles.textMeta}>{resumeCharCount} characters</span>
                </div>
              </>
            )}

            <div className={styles.resumeActions}>
              <div className={styles.textActions}>
                <button
                  className='btn btn-ghost btn-sm'
                  type='button'
                  onClick={() => {
                    setResumeText(SAMPLE_RESUME)
                    setInputMode('text')
                  }}
                >
                  Use sample resume
                </button>
                <button className='btn btn-ghost btn-sm' type='button' onClick={() => setResumeText('')} disabled={!resumeText}>
                  Clear text
                </button>
              </div>

              <button className='btn btn-primary' type='button' onClick={() => handleResumeSubmit()} disabled={loading}>
                {loading ? 'Analyzing...' : 'Assess Skills and Generate Quiz Link'}
              </button>
            </div>

            <div className={styles.stepActions}>
              <button className='btn btn-ghost' type='button' onClick={() => setStep(1)}>
                Back
              </button>
            </div>
          </div>
        )}

        {step === 3 && extractedProfile && (
          <div>
            <div className={styles.stepHeader}>
              <span className='badge badge-success'>Skills Assessed</span>
              <h1>Quiz Ready</h1>
              <p className={styles.stepDesc}>Your adaptive quiz has been prepared using extracted skills and experience.</p>
            </div>

            <div className={styles.skillsGrid}>
              {extractedProfile.skills?.map((skill) => (
                <div key={skill.skill_id} className={styles.skillChip}>
                  <span className={styles.skillName}>{skill.name}</span>
                  <span className={styles.skillLevel}>{'●'.repeat(skill.level)}{'○'.repeat(5 - skill.level)}</span>
                  <span className={`${styles.relevanceBadge} ${styles[`rel_${skill.relevance || 'unknown'}`]}`}>
                    {skill.relevance === 'critical' && '🟢 Critical'}
                    {skill.relevance === 'important' && '🟡 Important'}
                    {skill.relevance === 'peripheral' && '🔵 Peripheral'}
                    {skill.relevance === 'irrelevant' && '⚪ Less Important'}
                    {(!skill.relevance || skill.relevance === 'unknown') && '⚫ Unknown'}
                  </span>
                </div>
              ))}
            </div>

            <p className={styles.experienceTag}>
              Experience: {extractedProfile.experience_years ?? 'Not detected'} years
              {'  '}|{'  '}
              Domain: {extractedProfile.domain || 'General'}
            </p>

            <div className={styles.resumeActions}>
              <a
                className='btn btn-primary btn-lg'
                href={externalQuizUrl}
                target='_blank'
                rel='noreferrer'
              >
                Open Quiz at localhost:8900
              </a>
              <button className='btn btn-ghost' type='button' onClick={copyQuizLink}>
                Copy Quiz Link
              </button>
            </div>

            <div className={styles.roleSelectWrap} style={{ marginTop: '1rem', maxWidth: '100%' }}>
              <label className='label'>Quiz URL</label>
              <input className='input' value={externalQuizUrl} readOnly />
            </div>

            <div className={styles.stepActions}>
              <button className='btn btn-ghost' type='button' onClick={() => setStep(2)}>
                Back
              </button>
              <button
                className='btn btn-secondary'
                type='button'
                onClick={() => {
                  if (quizSessionId) {
                    router.push(`/pathway?session_id=${encodeURIComponent(quizSessionId)}`)
                  }
                }}
                disabled={!quizSessionId}
              >
                Check Results / Pathway
              </button>
            </div>
          </div>
        )}

        {error && <div className={styles.error}>{error}</div>}
      </div>
    </div>
  )
}
