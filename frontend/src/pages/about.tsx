import { Link } from 'react-router-dom'
import { useEffect, type ReactNode } from 'react'
import '../styles/about.css'

const REPO_URL = 'https://github.com/thaseenabbut/Sift'

const sourceUrl = (file: string) => `${REPO_URL}/blob/main/src/${file}`

type Stage = {
  title: string
  files: readonly string[]
  body: ReactNode
  excerpt?: ReactNode
  hinge?: boolean
}

const INDEX_ENTRY = (
  <figure className="arch-excerpt">
    <figcaption>
      One entry in the index, with illustrative values. The stem{' '}
      <code>engin</code> covers engine, engines and engineering.
    </figcaption>
    <pre
      className="arch-code"
      tabIndex={0}
      role="region"
      aria-label="Illustrative index entry"
    >
      <code>
        <span className="arch-hl">engin</span>
        {`   df 2
  example.org/a   tf 3   positions 4, 19, 52
  example.org/b   tf 1   positions 8`}
      </code>
    </pre>
  </figure>
)

const BM25_FORMULA = (
  <figure className="arch-excerpt">
    <figcaption>
      BM25, summed over the terms in the query. N is the number of indexed
      pages; Sift uses k1&nbsp;=&nbsp;1.2 and b&nbsp;=&nbsp;0.75.
    </figcaption>
    <pre
      className="arch-code"
      tabIndex={0}
      role="region"
      aria-label="BM25 scoring formula"
    >
      <code>
        {`idf   = ln(1 + (N − df + 0.5) / (df + 0.5))
norm  = 1 − b + b · (length / avg length)
score = Σ idf · tf · (k1 + 1) / (tf + k1 · norm)`}
      </code>
    </pre>
  </figure>
)

const BUILD_STAGES: readonly Stage[] = [
  {
    title: 'Crawl',
    files: ['crawler.py'],
    body: (
      <>
        A Python crawler, SiftBot, starts from seed URLs and follows links
        breadth-first, staying within the seed domains. It reads each
        site’s robots.txt first, strips tracking parameters, and resolves
        redirects and canonical links so the same page isn’t indexed twice.
      </>
    ),
  },
  {
    title: 'Process',
    files: ['document_parser.py', 'tokenizer.py', 'stemmer.py'],
    body: (
      <>
        BeautifulSoup pulls out each page’s title, description and
        headings and discards navigation, scripts and other page furniture.
        The remaining text is lowercased, split into tokens, stripped of
        common stop words and reduced to stems with the Porter stemmer, so
        “searching” and “searches” both become “search”.
      </>
    ),
  },
  {
    title: 'Index',
    files: ['indexer.py'],
    hinge: true,
    body: (
      <>
        The result is an inverted index, like the one at the back of a
        book. For every stem it records which pages contain it (document
        frequency), how often it appears in each (term frequency) and at
        which word positions. It lives in MongoDB. Each page also gets a
        SHA-256 content hash, so a refresh skips pages that haven’t changed
        and replaces the entries of those that have.
      </>
    ),
    excerpt: INDEX_ENTRY,
  },
]

const QUERY_STAGES: readonly Stage[] = [
  {
    title: 'Read the query',
    files: ['query_parser.py'],
    body: (
      <>
        A query goes through the same tokenizer and stemmer as the
        documents, so both sides share one vocabulary. Operators are pulled
        out first: <code>+required</code> and <code>-excluded</code> terms,{' '}
        <code>“exact phrases”</code>, <code>site:</code>,{' '}
        <code>intitle:</code> and <code>inurl:</code>.
      </>
    ),
  },
  {
    title: 'Retrieve',
    files: ['retriever.py'],
    body: (
      <>
        Every stem in the query is looked up in the index with a single
        MongoDB query. Pages containing any of the terms become candidates,
        and the operators then narrow them. For exact phrases, the stored
        word positions confirm that the words sit next to each other, in
        order.
      </>
    ),
  },
  {
    title: 'Rank',
    files: ['ranker.py'],
    body: (
      <>
        BM25 scores each candidate against the query, and the pages are
        sorted by that score. Rare terms count for more than common ones,
        repeated mentions help but with diminishing returns, and long pages
        are normalised so length alone doesn’t win.
      </>
    ),
    excerpt: BM25_FORMULA,
  },
]

const ROADMAP = [
  {
    number: '01',
    title: 'Relevance',
    desc: 'Improving retrieval and ranking so the most useful pages come first. Today that means BM25 over exact keywords, and there is plenty of room to tune and extend it.',
  },
  {
    number: '02',
    title: 'Understanding',
    desc: 'Exploring semantic search and vector embeddings to go beyond exact keyword matching, so a query and a page that share meaning but not words can still find each other.',
  },
  {
    number: '03',
    title: 'Synthesis',
    desc: 'Exploring AI-generated answers grounded in retrieved web pages, with links back to the sources they came from.',
  },
] as const

function ArchPhase({
  id,
  title,
  intro,
  stages,
}: {
  id: string
  title: string
  intro: string
  stages: readonly Stage[]
}) {
  return (
    <div className="arch-phase" role="group" aria-labelledby={id}>
      <div className="arch-phase-head">
        <h3 id={id} className="arch-phase-title">
          {title}
        </h3>
        <p className="arch-phase-intro">{intro}</p>
      </div>

      <ol className="arch-stages" role="list">
        {stages.map((stage) => (
          <li
            key={stage.title}
            className={stage.hinge ? 'arch-stage arch-stage--hinge' : 'arch-stage'}
          >
            <span className="arch-node" aria-hidden="true" />
            <div className="arch-stage-head">
              <h4 className="arch-stage-title">{stage.title}</h4>
              <div className="arch-files">
                {stage.files.map((file) => (
                  <a
                    key={file}
                    className="arch-file"
                    href={sourceUrl(file)}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`View ${file} on GitHub`}
                  >
                    {file}
                  </a>
                ))}
              </div>
            </div>
            <div className="arch-stage-body">
              <p>{stage.body}</p>
              {stage.excerpt}
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}

function GitHubIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.009-.866-.013-1.7-2.782.603-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836a9.59 9.59 0 012.504.337c1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
    </svg>
  )
}

function ExternalIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M6.5 3.5h-3a1 1 0 00-1 1v8a1 1 0 001 1h8a1 1 0 001-1v-3m-4-7h5m0 0v5m0-5L7 9"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function About() {
  useEffect(() => {
    document.title = 'About \u2013 Sift'
  }, [])

  return (
    <div className="sift about-page">
      {/* ── Navigation ──────────────────────────────── */}
      <nav className="about-nav" aria-label="About navigation">
        <Link to="/" className="about-nav-wordmark">
          Sift
        </Link>
        <div className="about-nav-links">
          <Link to="/about">About</Link>
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms</Link>
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────── */}
      <section className="about-hero" aria-labelledby="about-hero-heading">
        <div className="about-section">
          <h1 id="about-hero-heading" className="about-hero-headline">
            Search, reimagined.
          </h1>
          <div className="about-hero-desc">
            <p>
              Sift is an open-source search engine built from scratch, designed to
              make finding information on the web simpler, faster, and more
              transparent.
            </p>
          </div>
          <a
            href={REPO_URL}
            className="about-hero-link"
            target="_blank"
            rel="noopener noreferrer"
          >
            Explore Sift's Source Code
            <ExternalIcon />
          </a>
        </div>
      </section>

      {/* ── Why Sift Exists ─────────────────────────── */}
      <section className="about-why" aria-labelledby="about-why-heading">
        <div className="about-section">
          <span className="about-section-label">Why Sift Exists</span>
          <h2 id="about-why-heading" className="about-section-heading">
            Search should be understandable.
          </h2>
          <div className="about-section-body">
            <p>
              Sift began as an effort to understand and build search technology from
              the ground up. Rather than relying on existing search APIs or
              third-party indexes, Sift develops its own search pipeline from
              crawling the web to returning ranked results.
            </p>
            <p>
              The project explores how web pages are discovered, how their content
              is processed and organized, how documents are indexed for efficient
              retrieval, and how results are ranked by relevance to a query.
            </p>
          </div>
        </div>
      </section>

      {/* ── How Sift Works ─────────────────────────── */}
      <section className="about-arch" aria-labelledby="about-arch-heading">
        <div className="about-section">
          <span className="about-section-label">How It Works</span>
          <h2 id="about-arch-heading" className="about-section-heading">
            Behind every search.
          </h2>
          <div className="about-section-body">
            <p>
              Sift works in two halves. Ahead of time, it crawls pages, cleans
              them up and files every word into an index. When someone
              searches, it reads the query the same way, looks the words up in
              that index and ranks whatever matches.
            </p>
            <p>
              This is the pipeline as it exists in the repository today. Each
              stage links to its source, and the larger marker is the index,
              where the two halves meet.
            </p>
          </div>

          <div className="arch">
            <ArchPhase
              id="arch-build-heading"
              title="Before a search"
              intro="Pages are collected, cleaned and indexed ahead of time, not while you wait."
              stages={BUILD_STAGES}
            />
            <ArchPhase
              id="arch-query-heading"
              title="At search time"
              intro="A FastAPI endpoint runs these steps for every query and returns a page of ranked results with snippets, which the React and TypeScript interface displays."
              stages={QUERY_STAGES}
            />
          </div>
        </div>
      </section>

      {/* ── The Road Ahead ─────────────────────────── */}
      <section className="about-future" aria-labelledby="about-future-heading">
        <div className="about-section">
          <span className="about-section-label">The road ahead</span>
          <h2 id="about-future-heading" className="about-section-heading">
            Search is only the beginning.
          </h2>
          <div className="about-section-body">
            <p>
              Today, Sift matches the words you type. The work ahead is about
              what comes after a match: finding more relevant pages,
              understanding what a query means and explaining what was found.
              These are directions Sift is exploring, not features available
              today.
            </p>
          </div>

          <ol className="road" role="list">
            {ROADMAP.map((item) => (
              <li className="road-item" key={item.title}>
                <span className="road-number" aria-hidden="true">
                  {item.number}
                </span>
                <h3 className="road-title">{item.title}</h3>
                <p className="road-desc">{item.desc}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ── Open Source ─────────────────────────────── */}
      <section className="about-opensource" aria-labelledby="about-os-heading">
        <div className="about-section">
          <span className="about-section-label">Open Source</span>
          <h2 id="about-os-heading" className="about-section-heading">
            Built in the open.
          </h2>
          <div className="about-section-body">
            <p>
              Sift is an open-source project exploring search architecture,
              information retrieval, ranking algorithms, and the systems that make
              web search possible. The entire codebase is publicly available.
            </p>
          </div>
          <a
            href={REPO_URL}
            className="about-source-btn"
            target="_blank"
            rel="noopener noreferrer"
          >
            <GitHubIcon />
            Explore the source code
          </a>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────── */}
      <footer className="about-footer">
        <div className="about-footer-inner">
          <div className="about-footer-brand">
            <p className="about-footer-wordmark">Sift</p>
          </div>

          <nav className="about-footer-nav" aria-label="Footer">
            <Link to="/about">About</Link>
            <Link to="/privacy">Privacy</Link>
            <Link to="/terms">Terms</Link>
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </nav>

          <p className="about-footer-copy">
            &copy; {new Date().getFullYear()} Sift. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default About