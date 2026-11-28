import { Link } from 'react-router-dom'
import { useEffect, type ReactNode } from 'react'
import '../styles/about.css'

const REPO_URL = 'https://github.com/thaseenabbut/Sift'
const CURRENT_YEAR = new Date().getFullYear()

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

const RRF_FORMULA = (
  <figure className="arch-excerpt">
    <figcaption>
      Reciprocal Rank Fusion with k&nbsp;=&nbsp;60.
      Each retriever contributes 1/(k + rank) per document, and the totals are
      sorted to produce one final ranking without comparing raw scores.
    </figcaption>
    <pre
      className="arch-code"
      tabIndex={0}
      role="region"
      aria-label="RRF formula"
    >
      <code>
        {`score(d) = Σ  1 / (k + rank_i(d))
              i ∈ {keyword, semantic}`}
      </code>
    </pre>
  </figure>
)

const BUILD_STAGES: readonly Stage[] = [
  {
    title: 'Discover & crawl',
    files: ['crawler.py'],
    body: (
      <>
        SiftBot starts with seed URLs and walks links breadth-first, staying
        within their registered domains. Before fetching a page it checks
        <code>robots.txt</code>; it also normalises URLs, removes common
        tracking parameters, retries transient failures, and reconciles
        redirects and canonical aliases.
      </>
    ),
  },
  {
    title: 'Parse & store pages',
    files: ['document_parser.py'],
    body: (
      <>
        BeautifulSoup extracts the title, description, headings and readable
        text while removing scripts, navigation, headers, footers and other
        page furniture. The resulting page document is stored in MongoDB
        with a SHA-256 content hash, so unchanged content can be skipped and
        incomplete indexing can be repaired on a later crawl.
      </>
    ),
  },
  {
    title: 'Build the keyword index',
    files: ['indexer.py', 'tokenizer.py', 'stemmer.py'],
    hinge: true,
    body: (
      <>
        Clean text is tokenised and Porter-stemmed, then written as a MongoDB
        inverted index. For every stem, Sift records the pages that contain
        it, its per-page frequency and every word position. Index statistics
        retain document lengths and the corpus average needed for BM25.
      </>
    ),
    excerpt: INDEX_ENTRY,
  },
  {
    title: 'Build the semantic index',
    files: ['embeddings/chunker.py', 'embeddings/model.py', 'embeddings/processor.py', 'indexing_pipeline.py'],
    body: (
      <>
        The same page text is split into 256-token chunks with a 40-token
        overlap using <code>RecursiveCharacterTextSplitter</code>. Sift embeds
        those chunks with the multilingual{' '}
        <code>intfloat/multilingual-e5-small</code> model and stores the
        vectors alongside their page IDs in MongoDB Atlas for vector search.
        A unified <code>PageIndexingPipeline</code> orchestrates both the BM25
        and vector paths, tracking content hashes to skip unchanged pages.
      </>
    ),
  },
]

const QUERY_STAGES: readonly Stage[] = [
  {
    title: 'Parse the query',
    files: ['query_parser.py'],
    body: (
      <>
        A query goes through the same tokenizer and stemmer as the
        documents, so both sides share one vocabulary. Operators are pulled
        out first: <code>+required</code> and <code>-excluded</code> terms,
        exact <code>"phrases"</code>, <code>site:</code>,{' '}
        <code>intitle:</code>, <code>inurl:</code> and <code>related:</code>.
      </>
    ),
  },
  {
    title: 'Retrieve & rank keywords',
    files: ['retrieval/keyword.py', 'retriever.py', 'ranker.py'],
    body: (
      <>
        Matching stems produce candidate pages, then filters narrow them.
        Exact phrases are verified from stored positions, not substring
        matching. BM25 scores the remaining pages, with a proximity bonus for
        query terms that appear close together.
      </>
    ),
    excerpt: BM25_FORMULA,
  },
  {
    title: 'Retrieve semantic matches',
    files: ['retrieval/semantic.py', 'embeddings/model.py'],
    body: (
      <>
        The query is embedded with the same E5 model and fired against
        MongoDB Atlas Vector Search to find similar stored chunks.
        Their parent pages are added as semantic candidates, then pass through
        the same operator filters and exact-phrase checks.
      </>
    ),
  },
  {
    title: 'Fuse & rank with RRF',
    files: ['retrieval/hybrid.py', 'retrieval/fusion.py'],
    hinge: true,
    body: (
      <>
        Reciprocal Rank Fusion combines the keyword and semantic rankings
        without comparing their raw scores. Each retriever contributes a rank-based
        weight per document, producing one unified ranking that respects both
        lexical precision and semantic understanding.
      </>
    ),
    excerpt: RRF_FORMULA,
  },
  {
    title: 'Format, cache & serve',
    files: ['results.py', 'cache.py', 'api/routes.py', 'ratelimiter.py'],
    body: (
      <>
        Sift generates a focused text snippet for each page and caches the
        finished result set in Redis for five minutes. A token-bucket rate
        limiter protects the FastAPI endpoint, which paginates results for
        the React interface.
      </>
    ),
  },
]

const AI_OVERVIEW_STAGES: readonly Stage[] = [
  {
    title: 'Retrieve relevant chunks',
    files: ['ai_overview/retriever.py', 'retrieval/semantic.py'],
    body: (
      <>
        A parallel vector search retrieves up to 50 of the most relevant
        chunks for the query. Each chunk is enriched with its source page
        title and URL from MongoDB, so every claim can be traced back.
      </>
    ),
  },
  {
    title: 'Build grounded context',
    files: ['ai_overview/context.py'],
    body: (
      <>
        The <code>ContextBuilder</code> deduplicates chunks, ranks them by
        similarity score, and packs them into numbered{' '}
        <code>&lt;document&gt;</code> blocks within a 3 000-token budget.
        Source URLs are collected for citation display.
      </>
    ),
  },
  {
    title: 'Generate with Groq LLM',
    files: ['ai_overview/prompt.py', 'ai_overview/llm.py'],
    body: (
      <>
        A system prompt instructs the model to answer only from the retrieved
        context, never invent facts, and treat document content as untrusted.
        Sift calls Groq's async API with low temperature and reasoning effort
        to produce a concise, Google-style AI Overview with bolded key terms.
      </>
    ),
  },
  {
    title: 'Cite & deliver',
    files: ['ai_overview/service.py'],
    body: (
      <>
        The <code>AIOverviewService</code> orchestrates the full RAG pipeline:
        retrieve → build context → generate. Sources are attached alongside
        the generated overview so the React interface can render clickable
        citation links back to the original web pages.
      </>
    ),
  },
]

const ROADMAP = [
  {
    number: '01',
    title: 'Relevance',
    desc: 'Improving retrieval and ranking so the most useful pages come first. Sift already combines BM25 keyword results with semantic matches via Reciprocal Rank Fusion; tuning weights and evaluation remain ongoing.',
  },
  {
    number: '02',
    title: 'Understanding',
    desc: 'Strengthening the semantic path so a query and a page that share meaning, but not exact words, can still find each other reliably.',
  },
  {
    number: '03',
    title: 'AI Overviews',
    desc: 'RAG-powered AI-generated answers grounded in retrieved web pages, with citation links back to the sources they came from. The first version is live and uses Groq for fast inference.',
  },
] as const

/* ═══════════════════════════════════════════════════════
   Architecture map — the big SVG
   ═══════════════════════════════════════════════════════ */

function ArchitectureMap() {
  return (
    <figure className="system-map" aria-labelledby="system-map-caption">
      <figcaption id="system-map-caption" className="system-map-caption">
        The end-to-end Sift pipeline. Solid arrows show the primary data flow;
        dashed arrows show index lookups during a search. The{' '}
        <span className="system-map-label--ai">green path</span> is the RAG
        pipeline powering AI Overviews.
      </figcaption>
      <div className="system-map-scroll" tabIndex={0}>
        <svg
          className="system-map-svg"
          viewBox="0 0 1400 820"
          role="img"
          aria-labelledby="system-map-title system-map-desc"
        >
          <title id="system-map-title">Sift search architecture</title>
          <desc id="system-map-desc">
            Pages are crawled, parsed and stored before being indexed for both
            keyword and semantic retrieval. A search query is parsed, routed through
            both retrieval paths, fused with RRF, cached and returned. A parallel
            RAG branch retrieves chunks, builds grounded context and generates an
            AI Overview with citations.
          </desc>
          <defs>
            <marker id="arch-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" className="system-map-arrow" />
            </marker>
            <marker id="arch-arrow-ai" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" className="system-map-arrow--ai" />
            </marker>
          </defs>

          {/* ── Lane labels ─────────────────────────── */}
          <text x="40" y="38" className="system-map-lane">Index ahead of time</text>
          <text x="40" y="330" className="system-map-lane">Search request</text>
          <text x="40" y="650" className="system-map-lane">AI Overview (RAG)</text>

          {/* ── Index-time arrows ────────────────────── */}
          <path className="system-map-line" markerEnd="url(#arch-arrow)" d="M180 116H220" />
          <path className="system-map-line" markerEnd="url(#arch-arrow)" d="M360 116H400" />
          <path className="system-map-line system-map-line--keyword" markerEnd="url(#arch-arrow)" d="M540 116H574V86H610" />
          <path className="system-map-line system-map-line--semantic" markerEnd="url(#arch-arrow)" d="M540 116H574V205H610" />

          {/* ── Search-time arrows ───────────────────── */}
          <path className="system-map-line" markerEnd="url(#arch-arrow)" d="M180 412H220" />
          <path className="system-map-line" markerEnd="url(#arch-arrow)" d="M360 412H400" />
          <path className="system-map-line system-map-line--keyword" markerEnd="url(#arch-arrow)" d="M540 412H576V382H610" />
          <path className="system-map-line system-map-line--semantic" markerEnd="url(#arch-arrow)" d="M540 412H576V505H610" />
          <path className="system-map-line system-map-line--keyword" markerEnd="url(#arch-arrow)" d="M750 382H782V442H810" />
          <path className="system-map-line system-map-line--semantic" markerEnd="url(#arch-arrow)" d="M750 505H782V442H810" />
          <path className="system-map-line" markerEnd="url(#arch-arrow)" d="M950 442H990" />
          <path className="system-map-line" markerEnd="url(#arch-arrow)" d="M1130 442H1170" />

          {/* ── Index lookup dashed lines ────────────── */}
          <path className="system-map-link system-map-link--keyword" markerEnd="url(#arch-arrow)" d="M680 127V292H680V352" />
          <path className="system-map-link system-map-link--semantic" markerEnd="url(#arch-arrow)" d="M680 246V292H680V475" />

          {/* ── RAG pipeline arrows ──────────────────── */}
          <path className="system-map-line system-map-line--ai" markerEnd="url(#arch-arrow-ai)" d="M540 412H560V690H610" />
          <path className="system-map-line system-map-line--ai" markerEnd="url(#arch-arrow-ai)" d="M750 710H810" />
          <path className="system-map-line system-map-line--ai" markerEnd="url(#arch-arrow-ai)" d="M950 710H990" />
          <path className="system-map-line system-map-line--ai" markerEnd="url(#arch-arrow-ai)" d="M1130 710H1170" />

          {/* ── RAG ← Vector index dashed lookup ─────── */}
          <path className="system-map-link system-map-link--ai" markerEnd="url(#arch-arrow-ai)" d="M680 246V590H680V670" />

          {/* ═══ NODES ═══════════════════════════════ */}

          {/* Index-time row */}
          <g className="system-map-node">
            <rect x="40" y="76" width="140" height="80" rx="8" />
            <text x="60" y="108">Seed URLs</text><text x="60" y="132" className="system-map-detail">allowed domains</text>
          </g>
          <g className="system-map-node">
            <rect x="220" y="76" width="140" height="80" rx="8" />
            <text x="240" y="108">SiftBot crawl</text><text x="240" y="132" className="system-map-detail">robots + canonical URLs</text>
          </g>
          <g className="system-map-node">
            <rect x="400" y="76" width="140" height="80" rx="8" />
            <text x="420" y="108">Page store</text><text x="420" y="132" className="system-map-detail">clean text + content hash</text>
          </g>
          <g className="system-map-node system-map-node--keyword">
            <rect x="610" y="46" width="140" height="80" rx="8" />
            <text x="630" y="78">Keyword index</text><text x="630" y="102" className="system-map-detail">stems + positions</text>
          </g>
          <g className="system-map-node system-map-node--semantic">
            <rect x="610" y="165" width="140" height="80" rx="8" />
            <text x="630" y="197">Vector index</text><text x="630" y="221" className="system-map-detail">chunks + embeddings</text>
          </g>

          {/* Search-time row */}
          <g className="system-map-node">
            <rect x="40" y="372" width="140" height="80" rx="8" />
            <text x="60" y="404">Search query</text><text x="60" y="428" className="system-map-detail">operators + phrases</text>
          </g>
          <g className="system-map-node">
            <rect x="220" y="372" width="140" height="80" rx="8" />
            <text x="240" y="404">Parse &amp; filter</text><text x="240" y="428" className="system-map-detail">shared vocabulary</text>
          </g>
          <g className="system-map-node">
            <rect x="400" y="372" width="140" height="80" rx="8" />
            <text x="420" y="404">Hybrid search</text><text x="420" y="428" className="system-map-detail">keyword + semantic</text>
          </g>
          <g className="system-map-node system-map-node--keyword">
            <rect x="610" y="342" width="140" height="80" rx="8" />
            <text x="630" y="374">BM25 retrieval</text><text x="630" y="398" className="system-map-detail">+ proximity score</text>
          </g>
          <g className="system-map-node system-map-node--semantic">
            <rect x="610" y="465" width="140" height="80" rx="8" />
            <text x="630" y="497">Semantic retrieval</text><text x="630" y="521" className="system-map-detail">vector similarity</text>
          </g>
          <g className="system-map-node system-map-node--fusion">
            <rect x="810" y="402" width="140" height="80" rx="8" />
            <text x="830" y="434">RRF fusion</text><text x="830" y="458" className="system-map-detail">one ranked list</text>
          </g>
          <g className="system-map-node">
            <rect x="990" y="402" width="140" height="80" rx="8" />
            <text x="1010" y="434">API + Redis</text><text x="1010" y="458" className="system-map-detail">snippets + pagination</text>
          </g>
          <g className="system-map-node system-map-node--output">
            <rect x="1170" y="402" width="140" height="80" rx="8" />
            <text x="1190" y="434">React UI</text><text x="1190" y="458" className="system-map-detail">ranked results</text>
          </g>

          {/* RAG row */}
          <g className="system-map-node system-map-node--ai">
            <rect x="610" y="670" width="140" height="80" rx="8" />
            <text x="630" y="702">Chunk retrieval</text><text x="630" y="726" className="system-map-detail">top-50 vectors</text>
          </g>
          <g className="system-map-node system-map-node--ai">
            <rect x="810" y="670" width="140" height="80" rx="8" />
            <text x="830" y="702">Context builder</text><text x="830" y="726" className="system-map-detail">3 000-token window</text>
          </g>
          <g className="system-map-node system-map-node--ai">
            <rect x="990" y="670" width="140" height="80" rx="8" />
            <text x="1010" y="702">Groq LLM</text><text x="1010" y="726" className="system-map-detail">grounded generation</text>
          </g>
          <g className="system-map-node system-map-node--ai">
            <rect x="1170" y="670" width="140" height="80" rx="8" />
            <text x="1190" y="702">AI Overview</text><text x="1190" y="726" className="system-map-detail">answer + citations</text>
          </g>

          {/* ── Legend ───────────────────────────────── */}
          <g className="system-map-legend" transform="translate(40 760)">
            <path className="system-map-line system-map-line--keyword" d="M0 0H20" />
            <text x="28" y="5">Keyword path</text>
            <path className="system-map-line system-map-line--semantic" d="M120 0H140" />
            <text x="148" y="5">Semantic path</text>
            <path className="system-map-line system-map-line--ai" d="M260 0H280" />
            <text x="288" y="5">RAG path</text>
            <path className="system-map-link" d="M360 0H380" />
            <text x="388" y="5">Index lookup</text>
          </g>
        </svg>
      </div>
    </figure>
  )
}

function ArchPhase({
  id,
  title,
  intro,
  stages,
  variant,
}: {
  id: string
  title: string
  intro: string
  stages: readonly Stage[]
  variant?: 'default' | 'ai'
}) {
  return (
    <div className={`arch-phase${variant === 'ai' ? ' arch-phase--ai' : ''}`} role="group" aria-labelledby={id}>
      <div className="arch-phase-head">
        <h3 id={id} className="arch-phase-title">
          {variant === 'ai' && <span className="arch-phase-badge">RAG</span>}
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

/* ═══════════════════════════════════════════════════════
   Tech stack badge strip
   ═══════════════════════════════════════════════════════ */

const TECH_STACK = [
  { name: 'Python',     role: 'Backend + pipelines' },
  { name: 'FastAPI',    role: 'REST API' },
  { name: 'MongoDB',    role: 'Pages + inverted index' },
  { name: 'Atlas Vector Search', role: 'Semantic retrieval' },
  { name: 'Redis',      role: 'Cache + rate limit' },
  { name: 'E5-small',   role: 'Embedding model' },
  { name: 'Groq',       role: 'LLM inference' },
  { name: 'React + TS', role: 'Frontend' },
] as const

function TechStack() {
  return (
    <div className="tech-stack" role="list" aria-label="Technology stack">
      {TECH_STACK.map((t) => (
        <div key={t.name} className="tech-badge" role="listitem">
          <span className="tech-badge-name">{t.name}</span>
          <span className="tech-badge-role">{t.role}</span>
        </div>
      ))}
    </div>
  )
}

/* ═══════════════════════════════════════════════════════
   Page component
   ═══════════════════════════════════════════════════════ */

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
              Sift is an open-source search engine built from scratch — from the
              web crawler and inverted index to hybrid retrieval with RAG-powered
              AI Overviews. Every piece is handcrafted, nothing is a black box.
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
              crawling the web to returning ranked results — and now, to generating
              AI-powered answers grounded in those results.
            </p>
            <p>
              The project explores how web pages are discovered, how their content
              is processed and organized, how documents are indexed for efficient
              retrieval, how results are ranked by relevance, and how a language
              model can synthesise those results into a concise overview without
              hallucinating.
            </p>
          </div>
        </div>
      </section>

      {/* ── Architecture map (SVG) ──────────────────── */}
      <section className="about-system-map" aria-labelledby="about-map-heading">
        <div className="about-section">
          <span className="about-section-label">System Architecture</span>
          <h2 id="about-map-heading" className="about-section-heading">
            Three pipelines, one search.
          </h2>
          <div className="about-section-body">
            <p>
              Everything Sift does flows through three parallel pipelines. The
              indexing pipeline runs ahead of time. When someone searches, the
              query splits into a keyword path and a semantic path, fused by
              Reciprocal Rank Fusion. A third RAG pipeline retrieves relevant
              chunks, builds grounded context, and calls a language model to
              generate an AI Overview with citations.
            </p>
          </div>
          <ArchitectureMap />
        </div>
      </section>

      {/* ── Tech stack ──────────────────────────────── */}
      <section className="about-tech" aria-labelledby="about-tech-heading">
        <div className="about-section">
          <span className="about-section-label">Built With</span>
          <h2 id="about-tech-heading" className="about-section-heading">
            The stack behind Sift.
          </h2>
          <TechStack />
        </div>
      </section>

      {/* ── How Sift Works (detailed stages) ─────────── */}
      <section className="about-arch" aria-labelledby="about-arch-heading">
        <div className="about-section">
          <span className="about-section-label">How It Works</span>
          <h2 id="about-arch-heading" className="about-section-heading">
            Behind every search.
          </h2>
          <div className="about-section-body">
            <p>
              Sift works in three phases. Ahead of time, it crawls pages, cleans
              them up and files every word into a keyword index while simultaneously
              embedding chunks into a vector store. When someone searches, hybrid
              retrieval runs both paths and fuses them. And now, a RAG pipeline
              generates AI Overviews grounded entirely in the retrieved pages.
            </p>
            <p>
              Each stage below links to its source code on GitHub.
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
            <ArchPhase
              id="arch-ai-heading"
              title="AI Overview generation"
              intro="When enabled, a parallel RAG pipeline retrieves chunks from the vector index, builds a grounded context, and generates a cited AI Overview."
              stages={AI_OVERVIEW_STAGES}
              variant="ai"
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
              Sift combines lexical retrieval, semantic search and RAG-powered
              AI Overviews in a single pipeline. The work ahead is about sharpening
              relevance, deepening semantic understanding, and making those
              AI-generated answers even more accurate and useful.
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
          <h2 id="about-os-heading" className="about-section-heading">
            Built in the open.
          </h2>
          <div className="about-section-body">
            <p>
              Sift is an open-source project exploring search architecture,
              information retrieval, ranking algorithms, RAG pipelines, and the
              systems that make web search possible. The entire codebase is
              publicly available.
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
            &copy; {CURRENT_YEAR} Sift. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default About
