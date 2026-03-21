'use client'

import { useRouter } from 'next/navigation'
import styles from './page.module.css'

export default function Home() {
  const router = useRouter()

  return (
    <div className={styles.landing}>
      {/* ── Nav ── */}
      <nav className={styles.nav}>
        <div className={`container ${styles.navInner}`}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>◆</span>
            <span className={styles.logoText}>PathForge</span>
          </div>
          <div className={styles.navLinks}>
            <a href="#features" className={styles.navLink}>Features</a>
            <a href="#how" className={styles.navLink}>How It Works</a>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => router.push('/onboarding')}
              id="nav-get-started"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className={styles.hero}>
        <div className="container">
          <div className={styles.heroBadge}>
            <span className={styles.heroBadgeDot}></span>
            AI-Powered Adaptive Learning
          </div>
          <h1 className={styles.heroTitle}>
            Your skills. <span className="text-gradient">Verified.</span><br />
            Your path. <span className="text-gradient">Personalized.</span>
          </h1>
          <p className={styles.heroSubtitle}>
            We parse what you claim, prove what you actually know,
            and only then generate your learning path from scratch
            — not from a pre-authored menu.
          </p>
          <div className={styles.heroCta}>
            <button
              className="btn btn-primary btn-lg"
              onClick={() => router.push('/onboarding')}
              id="hero-start-btn"
            >
              Start Your Journey
              <span className={styles.ctaArrow}>→</span>
            </button>
            <a href="#how" className="btn btn-ghost btn-lg">
              See How It Works
            </a>
          </div>

          {/* Stats */}
          <div className={styles.stats}>
            <div className={styles.stat}>
              <span className={styles.statNumber}>3</span>
              <span className={styles.statLabel}>AI Models</span>
            </div>
            <div className={styles.statDivider}></div>
            <div className={styles.stat}>
              <span className={styles.statNumber}>6</span>
              <span className={styles.statLabel}>Role Profiles</span>
            </div>
            <div className={styles.statDivider}></div>
            <div className={styles.stat}>
              <span className={styles.statNumber}>30+</span>
              <span className={styles.statLabel}>Skills Tracked</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className={styles.features}>
        <div className="container">
          <h2 className={styles.sectionTitle}>
            Two Gaps We <span className="text-gradient">Solve</span>
          </h2>
          <div className={styles.featureGrid}>
            <div className={`card ${styles.featureCard}`}>
              <div className={styles.featureIcon}>🧠</div>
              <h3>Resume → Skill Profile</h3>
              <p className={styles.featureDesc}>
                Most platforms take your resume at face value. We use a fine-tuned
                BERT model to extract skills, experience levels, and your domain.
              </p>
              <span className="badge badge-primary">Gap 1 — Black Box Solved</span>
            </div>
            <div className={`card ${styles.featureCard}`}>
              <div className={styles.featureIcon}>✅</div>
              <h3>Diagnostic Verification</h3>
              <p className={styles.featureDesc}>
                No platform verifies what you claim. We run a short adaptive quiz
                to confirm your actual skill levels before generating any path.
              </p>
              <span className="badge badge-primary">Gap 2 — Verification Added</span>
            </div>
            <div className={`card ${styles.featureCard}`}>
              <div className={styles.featureIcon}>🛤️</div>
              <h3>Adaptive Pathway</h3>
              <p className={styles.featureDesc}>
                Gap calculator × Priority scorer × Topological sort.
                Every module tells you exactly why it's in your path.
              </p>
              <span className="badge badge-success">100% Original Logic</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section id="how" className={styles.howItWorks}>
        <div className="container">
          <h2 className={styles.sectionTitle}>
            How <span className="text-gradient">PathForge</span> Works
          </h2>
          <div className={styles.steps}>
            <div className={styles.step}>
              <div className={styles.stepNumber}>01</div>
              <div className={styles.stepContent}>
                <h4>Upload Your Resume</h4>
                <p>Paste or upload your resume. Our BERT NER model extracts your skills and builds a structured profile.</p>
              </div>
            </div>
            <div className={styles.stepConnector}></div>
            <div className={styles.step}>
              <div className={styles.stepNumber}>02</div>
              <div className={styles.stepContent}>
                <h4>Select Target Role</h4>
                <p>Choose your target role. We map it to competency requirements using sentence-transformers + O*NET.</p>
              </div>
            </div>
            <div className={styles.stepConnector}></div>
            <div className={styles.step}>
              <div className={styles.stepNumber}>03</div>
              <div className={styles.stepContent}>
                <h4>Take Diagnostic Quiz</h4>
                <p>Short MCQ quiz to verify your actual skill levels. No faking — we test what you claim.</p>
              </div>
            </div>
            <div className={styles.stepConnector}></div>
            <div className={styles.step}>
              <div className={styles.stepNumber}>04</div>
              <div className={styles.stepContent}>
                <h4>Get Your Personalized Path</h4>
                <p>AI generates your optimal learning pathway with prioritized modules and clear reasoning.</p>
              </div>
            </div>
          </div>

          <div style={{ textAlign: 'center', marginTop: '3rem' }}>
            <button
              className="btn btn-primary btn-lg"
              onClick={() => router.push('/onboarding')}
              id="how-start-btn"
            >
              Begin Now →
            </button>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className={styles.footer}>
        <div className="container">
          <div className={styles.footerInner}>
            <div className={styles.footerBrand}>
              <span className={styles.logoIcon}>◆</span> PathForge
            </div>
            <p className={styles.footerText}>
              Built for HackCode.io 2026 — AI-Driven Adaptive Onboarding Engine
            </p>
            <div className={styles.footerCitations}>
              <span>BERT (Devlin et al., 2018)</span>
              <span>•</span>
              <span>Sentence-Transformers (Reimers & Gurevych, 2019)</span>
              <span>•</span>
              <span>O*NET (onetonline.org)</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
