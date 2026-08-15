import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';

const STATS = [
  { value: '90.5%', label: 'Test accuracy' },
  { value: '98.5%', label: 'Recall on positives' },
  { value: '0.962', label: 'ROC AUC' },
];

const PROCESS = [
  {
    n: '01',
    title: 'Load the film',
    body: 'Upload a chest X-ray. JPEG or PNG, any standard PA/AP view.',
  },
  {
    n: '02',
    title: 'The model reads every pixel',
    body: 'An EfficientNet-B3 classifier trained on confirmed pneumonia cases scores the full image.',
  },
  {
    n: '03',
    title: 'Grad-CAM shows its reasoning',
    body: 'A heatmap overlay marks exactly which regions of the film drove the call — no black box.',
  },
  {
    n: '04',
    title: 'Ask, and get a cited answer',
    body: 'Follow up in chat. Every claim traces back to a real clinical reference, not free-floating text.',
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-lightbox">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-cyan-500 text-white">
            <Activity className="h-4.5 w-4.5" />
          </div>
          <span className="font-display text-lg font-semibold text-ink">LungInsight</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">Log in</Button>
          </Link>
          <Link to="/register">
            <Button size="sm">Get started</Button>
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 md:grid-cols-2 md:py-20">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <p className="font-mono text-xs uppercase tracking-widest text-cyan-600">
            Chest X-ray screening, explained
          </p>
          <h1 className="mt-3 font-display text-4xl font-semibold leading-[1.05] text-ink md:text-5xl">
            See what the model sees, on every film.
          </h1>
          <p className="mt-5 max-w-md text-base text-steel">
            LungInsight AI classifies chest X-rays for pneumonia and shows its reasoning as a
            heatmap laid directly over the film — built for clinicians who need to trust, not
            just read, a prediction.
          </p>
          <div className="mt-8 flex items-center gap-3">
            <Link to="/register">
              <Button size="lg">
                Get started
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary" size="lg">Log in</Button>
            </Link>
          </div>

          {/* Real reported eval numbers, not marketing copy */}
          <dl className="mt-10 flex gap-8 border-t border-line pt-6">
            {STATS.map((s) => (
              <div key={s.label}>
                <dt className="font-mono text-[11px] uppercase tracking-wide text-steel-light">{s.label}</dt>
                <dd className="mt-1 font-display text-2xl font-semibold text-ink">{s.value}</dd>
              </div>
            ))}
          </dl>
        </motion.div>

        {/* Signature element: a physical illuminator viewbox, not a generic app screenshot */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="relative"
        >
          {/* Equipment housing */}
          <div className="rounded-xl border border-[#2a3650] bg-gradient-to-b from-[#1b2740] to-[#111a2e] p-3 shadow-[0_20px_50px_-15px_rgba(15,25,45,0.5)]">
            {/* Control strip */}
            <div className="mb-3 flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-cyan-400" />
                <span className="font-mono text-[10px] uppercase tracking-widest text-steel-light">
                  Illuminator · Active
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                {Array.from({ length: 4 }, (_, i) => (
                  <span key={i} className={`h-1.5 w-1.5 rounded-full ${i < 3 ? 'bg-cyan-400/70' : 'bg-[#3a4763]'}`} />
                ))}
              </div>
            </div>

            {/* Film panel */}
            <div className="viewbox-frame viewbox-frame--flag relative overflow-hidden rounded-md border-[#0a1120]">
              <div className="relative flex h-72 items-center justify-center overflow-hidden bg-gradient-to-b from-[#182543] to-[#0a1120]">
                {/* Film clips */}
                <span className="absolute left-4 top-2 h-3 w-6 rounded-sm bg-[#0a1120]" />
                <span className="absolute right-4 top-2 h-3 w-6 rounded-sm bg-[#0a1120]" />

                <svg viewBox="0 0 200 230" className="h-60 w-auto opacity-90" aria-hidden>
                  {/* clavicles */}
                  <path d="M 55 42 Q 82 30 100 40" fill="none" stroke="#5c6b85" strokeWidth="2" />
                  <path d="M 100 40 Q 118 30 145 42" fill="none" stroke="#5c6b85" strokeWidth="2" />
                  {/* lung fields */}
                  <ellipse cx="68" cy="118" rx="40" ry="82" fill="none" stroke="#5c6b85" strokeWidth="2" />
                  <ellipse cx="132" cy="118" rx="40" ry="82" fill="none" stroke="#5c6b85" strokeWidth="2" />
                  {/* spine */}
                  <rect x="95" y="34" width="10" height="164" fill="#5c6b85" opacity="0.55" />
                  {/* ribs */}
                  {Array.from({ length: 7 }, (_, i) => (
                    <g key={i}>
                      <path
                        d={`M ${34 - i * 0.5} ${58 + i * 17} Q 68 ${48 + i * 17} 96 ${60 + i * 17}`}
                        fill="none"
                        stroke="#3d4a63"
                        strokeWidth="1.3"
                      />
                      <path
                        d={`M 104 ${60 + i * 17} Q 132 ${48 + i * 17} ${166 + i * 0.5} ${58 + i * 17}`}
                        fill="none"
                        stroke="#3d4a63"
                        strokeWidth="1.3"
                      />
                    </g>
                  ))}
                </svg>

                {/* Grad-CAM hot region */}
                <div className="pointer-events-none absolute bottom-14 right-16 h-16 w-14 rounded-full bg-flag-500/50 blur-xl" />

                {/* Scanning read-line */}
                <motion.div
                  className="pointer-events-none absolute inset-x-3 h-px bg-cyan-400/80 shadow-[0_0_8px_2px_rgba(23,168,189,0.5)]"
                  animate={{ y: ['0.5rem', '17rem'] }}
                  transition={{ duration: 2.8, repeat: Infinity, ease: 'linear' }}
                />

                {/* Orientation marker, like a real film */}
                <span className="absolute left-4 top-1/2 -translate-y-1/2 font-mono text-xs text-steel-light">R</span>
              </div>
            </div>

            {/* Read-out strip */}
            <div className="mt-3 flex items-center justify-between px-1">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-flag-500/15 px-3 py-1 font-mono text-xs text-flag-400">
                <span className="h-1.5 w-1.5 rounded-full bg-flag-400" />
                Pneumonia · 94.3%
              </span>
              <span className="font-mono text-[10px] text-steel-light">ACC #LI-04821 · PA VIEW</span>
            </div>
          </div>
        </motion.div>
      </section>

      {/* How a read happens — a real sequence, not decorative cards */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <p className="font-mono text-xs uppercase tracking-widest text-cyan-600">How a read happens</p>
        <h2 className="mt-2 font-display text-2xl font-semibold text-ink md:text-3xl">
          Four steps, start to finish.
        </h2>

        <div className="mt-10 grid gap-x-8 gap-y-10 md:grid-cols-4">
          {PROCESS.map((step, i) => (
            <motion.div
              key={step.n}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-80px' }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="relative border-t-2 border-line pt-4"
            >
              <span className="font-mono text-xs text-cyan-600">{step.n}</span>
              <h3 className="mt-2 font-display font-semibold text-ink">{step.title}</h3>
              <p className="mt-2 text-sm text-steel">{step.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <footer className="border-t border-line px-6 py-8 text-center text-xs text-steel-light">
        LungInsight AI — a screening aid, not a diagnostic substitute for clinical judgment.
      </footer>
    </div>
  );
}
