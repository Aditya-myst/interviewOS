-- ═══════════════════════════════════════════════════════════════════════════
-- InterviewOS — 002_seed.sql
-- Seeds the global vocabulary and the tier-0 resource catalogue.
--
-- GENERATED FILE — do not edit by hand.
--   source: data/taxonomy.yaml (31 skills / 100 subtopics)
--           data/curated.yaml  (39 hand-curated resources)
--   regenerate: python scripts/gen_seed.py
--
-- Run AFTER 001_init.sql. Safe to re-run: every insert is an upsert on the
-- natural key, and nothing user-owned is touched.
--
-- PowerShell: paste into the Supabase SQL editor like 001. From a terminal:
--   psql "$env:DATABASE_URL" -f docs\sql\002_seed.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ── skills ────────────────────────────────────────────────────────────────
insert into public.skills (id, name, category, aliases, interview_relevance) values
  ('python', 'Python', 'Language', array['python3', 'python 3', 'py']::text[], 0.9),
  ('javascript', 'JavaScript', 'Language', array['js', 'ecmascript', 'es6']::text[], 0.5),
  ('typescript', 'TypeScript', 'Language', array['ts', 'type script']::text[], 0.5),
  ('sql', 'SQL', 'Data', array['sq-l', 'structured query language']::text[], 0.8),
  ('postgresql', 'PostgreSQL', 'Data', array['postgres', 'psql', 'postgre sql']::text[], 0.75),
  ('mongodb', 'MongoDB', 'Data', array['mongo', 'mongo db']::text[], 0.4),
  ('redis', 'Redis', 'Data', array['redis-cache', 'redis cache']::text[], 0.5),
  ('vector-db', 'Vector Databases', 'AI', array['pgvector', 'pinecone', 'weaviate', 'qdrant', 'faiss', 'vector store', 'vector database']::text[], 0.85),
  ('fastapi', 'FastAPI', 'Backend', array['fast-api', 'fast api']::text[], 0.9),
  ('django', 'Django', 'Backend', array['django-rest', 'drf', 'django rest framework']::text[], 0.5),
  ('flask', 'Flask', 'Backend', array['flask-api']::text[], 0.3),
  ('nodejs', 'Node.js', 'Backend', array['node', 'node js', 'expressjs', 'express']::text[], 0.5),
  ('rest-api', 'REST API Design', 'Backend', array['rest', 'restful', 'rest apis', 'api design']::text[], 0.85),
  ('react', 'React', 'Frontend', array['reactjs', 'react js', 'jsx']::text[], 0.6),
  ('nextjs', 'Next.js', 'Frontend', array['next js', 'next']::text[], 0.6),
  ('tailwind', 'Tailwind CSS', 'Frontend', array['tailwindcss', 'tailwind css']::text[], 0.3),
  ('docker', 'Docker', 'Infra', array['containerisation', 'containerization', 'dockerfile', 'docker compose']::text[], 0.8),
  ('kubernetes', 'Kubernetes', 'Infra', array['k8s', 'kube']::text[], 0.5),
  ('aws', 'AWS', 'Infra', array['amazon web services', 'ec2', 's3', 'lambda', 'aws cloud']::text[], 0.6),
  ('linux', 'Linux', 'Infra', array['unix', 'bash', 'shell']::text[], 0.5),
  ('git', 'Git', 'Engineering', array['github', 'gitlab', 'version control']::text[], 0.4),
  ('ci-cd', 'CI/CD', 'Engineering', array['cicd', 'github actions', 'continuous integration', 'continuous deployment', 'pipeline']::text[], 0.6),
  ('testing', 'Testing', 'Engineering', array['pytest', 'unittest', 'unit testing', 'integration testing', 'tdd']::text[], 0.7),
  ('data-structures', 'Data Structures', 'Fundamentals', array['dsa', 'data structure', 'hashmap', 'linked list', 'tree']::text[], 0.85),
  ('algorithms', 'Algorithms', 'Fundamentals', array['algorithmic', 'time complexity', 'big-o', 'dynamic programming', 'recursion']::text[], 0.85),
  ('system-design', 'System Design', 'Architecture', array['architecture', 'distributed systems', 'scalability', 'system architecture']::text[], 0.95),
  ('machine-learning', 'Machine Learning', 'AI', array['ml', 'machine learning', 'scikit-learn', 'sklearn', 'supervised learning']::text[], 0.8),
  ('llm-rag', 'LLM & RAG', 'AI', array['rag', 'llm', 'large language model', 'retrieval augmented generation', 'retrieval-augmented generation', 'langchain', 'gpt']::text[], 1.0),
  ('prompt-engineering', 'Prompt Engineering', 'AI', array['prompting', 'prompt design', 'system prompt', 'few-shot']::text[], 0.8),
  ('langgraph', 'LangGraph', 'AI', array['langchain', 'langgraph', 'agent framework', 'agentic workflow']::text[], 0.6),
  ('pandas', 'Pandas', 'Data', array['numpy', 'dataframe', 'dataframes']::text[], 0.5)
on conflict (id) do update set
  name                = excluded.name,
  category            = excluded.category,
  aliases             = excluded.aliases,
  interview_relevance = excluded.interview_relevance;

-- ── skill_subtopics (the curriculum graph; 100 rows) ──────────────
insert into public.skill_subtopics (skill_id, subtopic_id, title, level, objective, order_index) values
  ('python', 'syntax-types', 'Syntax and data types', 'beginner'::public.proficiency_level, 'Explain mutability, truthiness and slicing confidently.', 0),
  ('python', 'functions-scope', 'Functions, closures and scope', 'beginner'::public.proficiency_level, 'Reason about LEGB and default-argument pitfalls.', 1),
  ('python', 'oop-dataclasses', 'OOP and dataclasses', 'intermediate'::public.proficiency_level, 'Choose between classes, dataclasses and plain dicts.', 2),
  ('python', 'async-io', 'Async I/O and the event loop', 'advanced'::public.proficiency_level, 'Know when I/O bound code must be async, and what blocks the loop.', 3),
  ('python', 'typing-testing', 'Type hints and pytest', 'intermediate'::public.proficiency_level, 'Write typed code and test it without a framework fight.', 4),
  ('python', 'packaging', 'Packaging, venvs and dependencies', 'beginner'::public.proficiency_level, 'Own a reproducible environment.', 5),
  ('javascript', 'scope-hoisting', 'Scope, hoisting and closures', 'beginner'::public.proficiency_level, 'Explain let/const/var and closure capture.', 0),
  ('javascript', 'async-js', 'Promises and async/await', 'intermediate'::public.proficiency_level, 'Handle errors and concurrency correctly.', 1),
  ('javascript', 'event-loop', 'Event loop and microtasks', 'advanced'::public.proficiency_level, 'Predict output ordering in tricky snippets.', 2),
  ('typescript', 'ts-basics', 'Types, interfaces and narrowing', 'beginner'::public.proficiency_level, 'Model data without any-casts.', 0),
  ('typescript', 'ts-generics', 'Generics and utility types', 'advanced'::public.proficiency_level, 'Write reusable, safe abstractions.', 1),
  ('sql', 'joins', 'Joins and set operations', 'beginner'::public.proficiency_level, 'Pick the right join and explain NULL behaviour.', 0),
  ('sql', 'aggregation', 'Aggregation and window functions', 'intermediate'::public.proficiency_level, 'Answer analytics questions in one query.', 1),
  ('sql', 'indexing', 'Indexes and query plans', 'advanced'::public.proficiency_level, 'Read an EXPLAIN and justify an index.', 2),
  ('sql', 'transactions', 'Transactions and isolation', 'advanced'::public.proficiency_level, 'Explain dirty reads and deadlocks.', 3),
  ('postgresql', 'pg-schema', 'Schema design and normalisation', 'intermediate'::public.proficiency_level, 'Design tables that survive feature growth.', 0),
  ('postgresql', 'pg-index', 'Indexes, EXPLAIN and performance', 'advanced'::public.proficiency_level, 'Diagnose a slow query with evidence.', 1),
  ('postgresql', 'pg-json', 'JSONB and full-text search', 'intermediate'::public.proficiency_level, 'Know when structured beats document columns.', 2),
  ('postgresql', 'pg-migrations', 'Migrations and zero-downtime changes', 'advanced'::public.proficiency_level, 'Change a table without breaking live traffic.', 3),
  ('mongodb', 'mongo-model', 'Document modelling', 'beginner'::public.proficiency_level, 'Decide embed vs reference.', 0),
  ('mongodb', 'mongo-agg', 'Aggregation pipeline', 'intermediate'::public.proficiency_level, 'Build a multi-stage pipeline.', 1),
  ('redis', 'redis-types', 'Data structures and TTL', 'beginner'::public.proficiency_level, 'Choose the right structure for the access pattern.', 0),
  ('redis', 'redis-patterns', 'Caching patterns and invalidation', 'intermediate'::public.proficiency_level, 'Explain stampede, TTL and consistency tradeoffs.', 1),
  ('vector-db', 'embeddings', 'Embeddings and similarity', 'beginner'::public.proficiency_level, 'Explain cosine similarity and dimensionality.', 0),
  ('vector-db', 'ann-index', 'ANN indexes (HNSW, IVFFlat)', 'advanced'::public.proficiency_level, 'Trade recall against latency and memory.', 1),
  ('vector-db', 'chunking', 'Chunking and metadata filters', 'intermediate'::public.proficiency_level, 'Chunk documents without destroying context.', 2),
  ('fastapi', 'http-fundamentals', 'HTTP fundamentals and status codes', 'beginner'::public.proficiency_level, 'Use verbs and status codes correctly.', 0),
  ('fastapi', 'routing', 'Routing, path and query params', 'beginner'::public.proficiency_level, 'Structure an API surface that stays readable.', 1),
  ('fastapi', 'models-validation', 'Pydantic models and validation', 'intermediate'::public.proficiency_level, 'Validate input and shape output without leaking internals.', 2),
  ('fastapi', 'dependency-injection', 'Dependency injection', 'intermediate'::public.proficiency_level, 'Use Depends for shared logic and test overrides.', 3),
  ('fastapi', 'auth', 'Authentication and authorisation', 'advanced'::public.proficiency_level, 'Implement token auth and explain the flow.', 4),
  ('fastapi', 'async-endpoints', 'Async endpoints and blocking calls', 'advanced'::public.proficiency_level, 'Keep the event loop free under load.', 5),
  ('fastapi', 'db-integration', 'Database integration and pooling', 'intermediate'::public.proficiency_level, 'Manage sessions, transactions and pool limits.', 6),
  ('fastapi', 'fastapi-testing', 'Testing with TestClient', 'intermediate'::public.proficiency_level, 'Test endpoints and override dependencies.', 7),
  ('fastapi', 'fastapi-deploy', 'Deployment and workers', 'advanced'::public.proficiency_level, 'Explain workers, health checks and containerisation.', 8),
  ('django', 'django-orm', 'ORM and query optimisation', 'intermediate'::public.proficiency_level, 'Avoid N+1 and explain select_related.', 0),
  ('django', 'django-migrations', 'Migrations and models', 'intermediate'::public.proficiency_level, 'Evolve a schema safely.', 1),
  ('flask', 'flask-basics', 'App factory and blueprints', 'beginner'::public.proficiency_level, 'Structure a non-trivial Flask app.', 0),
  ('nodejs', 'node-eventloop', 'Event loop, streams and buffers', 'intermediate'::public.proficiency_level, 'Explain non-blocking I/O with real costs.', 0),
  ('nodejs', 'node-api', 'REST APIs with Express', 'beginner'::public.proficiency_level, 'Build and validate an endpoint.', 1),
  ('rest-api', 'resource-modelling', 'Resource modelling and naming', 'beginner'::public.proficiency_level, 'Design predictable URLs.', 0),
  ('rest-api', 'pagination-versioning', 'Pagination, filtering, versioning', 'intermediate'::public.proficiency_level, 'Handle growth without breaking clients.', 1),
  ('rest-api', 'idempotency', 'Idempotency and error contracts', 'advanced'::public.proficiency_level, 'Make retries safe and errors machine-readable.', 2),
  ('react', 'components-state', 'Components, props and state', 'beginner'::public.proficiency_level, 'Lift state correctly and avoid derived-state bugs.', 0),
  ('react', 'hooks', 'Hooks and effects', 'intermediate'::public.proficiency_level, 'Use useEffect without starvation or loops.', 1),
  ('react', 'rendering', 'Rendering, memoisation and keys', 'advanced'::public.proficiency_level, 'Explain re-render causes precisely.', 2),
  ('nextjs', 'routing-layouts', 'App router, layouts and loading states', 'beginner'::public.proficiency_level, 'Structure routes and stream UI.', 0),
  ('nextjs', 'server-client', 'Server vs client components', 'intermediate'::public.proficiency_level, 'Decide where data fetching belongs.', 1),
  ('nextjs', 'data-fetching', 'Caching, revalidation and mutations', 'advanced'::public.proficiency_level, 'Reason about staleness and invalidation.', 2),
  ('tailwind', 'utility-first', 'Utility-first workflow and design tokens', 'beginner'::public.proficiency_level, 'Keep a consistent scale instead of magic numbers.', 0),
  ('docker', 'images-containers', 'Images, containers and layers', 'beginner'::public.proficiency_level, 'Explain the difference crisply.', 0),
  ('docker', 'dockerfile', 'Writing an efficient Dockerfile', 'intermediate'::public.proficiency_level, 'Use layer caching and a slim base image.', 1),
  ('docker', 'compose', 'Compose for app plus database', 'intermediate'::public.proficiency_level, 'Run a local stack reproducibly.', 2),
  ('docker', 'debugging', 'Debugging containers in production', 'advanced'::public.proficiency_level, 'Diagnose work-locally-fails-deployed with evidence.', 3),
  ('docker', 'docker-security', 'Secrets, users and image hygiene', 'advanced'::public.proficiency_level, 'Ship images you would defend in review.', 4),
  ('kubernetes', 'pods-services', 'Pods, deployments and services', 'beginner'::public.proficiency_level, 'Explain the object model.', 0),
  ('kubernetes', 'probes-scaling', 'Probes, resources and autoscaling', 'advanced'::public.proficiency_level, 'Diagnose crashloops and OOM kills.', 1),
  ('aws', 'core-services', 'Compute, storage and networking basics', 'beginner'::public.proficiency_level, 'Pick a service and justify it.', 0),
  ('aws', 'iam', 'IAM and least privilege', 'intermediate'::public.proficiency_level, 'Explain roles, policies and trust.', 1),
  ('aws', 'deployment', 'Deploying a containerised API', 'intermediate'::public.proficiency_level, 'Describe a working deployment path.', 2),
  ('linux', 'processes', 'Processes, signals and systemd', 'beginner'::public.proficiency_level, 'Debug a service that will not start.', 0),
  ('linux', 'networking-tools', 'Networking tools and logs', 'intermediate'::public.proficiency_level, 'Use ss, curl, dig and journalctl with purpose.', 1),
  ('linux', 'permissions', 'Permissions and disk', 'beginner'::public.proficiency_level, 'Fix access and space issues safely.', 2),
  ('git', 'branching', 'Branching, merge and rebase', 'beginner'::public.proficiency_level, 'Explain history rewriting tradeoffs.', 0),
  ('git', 'recovery', 'Recovery and conflict resolution', 'intermediate'::public.proficiency_level, 'Rescue work with reflog and cherry-pick.', 1),
  ('git', 'workflow', 'Review workflow and PR hygiene', 'beginner'::public.proficiency_level, 'Ship reviewable commits.', 2),
  ('ci-cd', 'pipeline-basics', 'Build, test, deploy stages', 'beginner'::public.proficiency_level, 'Design a pipeline that fails fast.', 0),
  ('ci-cd', 'secrets-artifacts', 'Secrets, caching and artifacts', 'intermediate'::public.proficiency_level, 'Keep builds fast and safe.', 1),
  ('ci-cd', 'rollout', 'Rollbacks and blue-green deploys', 'advanced'::public.proficiency_level, 'Explain how a bad deploy is undone.', 2),
  ('testing', 'unit-vs-integration', 'Unit vs integration vs e2e', 'beginner'::public.proficiency_level, 'Choose the cheapest test that would catch the bug.', 0),
  ('testing', 'test-design', 'Fixtures, parametrisation and mocking', 'intermediate'::public.proficiency_level, 'Write tests that survive refactors.', 1),
  ('testing', 'llm-testing', 'Testing non-deterministic systems', 'advanced'::public.proficiency_level, 'Test LLM output with rubrics and eval sets.', 2),
  ('data-structures', 'arrays-hashing', 'Arrays, strings and hashing', 'beginner'::public.proficiency_level, 'Solve two-pointer and counting problems cleanly.', 0),
  ('data-structures', 'stacks-queues', 'Stacks, queues and heaps', 'intermediate'::public.proficiency_level, 'Recognise monotonic and priority patterns.', 1),
  ('data-structures', 'trees-graphs', 'Trees and graph traversal', 'advanced'::public.proficiency_level, 'Choose BFS/DFS and bound complexity.', 2),
  ('algorithms', 'complexity', 'Complexity analysis', 'beginner'::public.proficiency_level, 'State time and space bounds without hand-waving.', 0),
  ('algorithms', 'sorting-searching', 'Sorting and binary search', 'intermediate'::public.proficiency_level, 'Apply search-on-answer patterns.', 1),
  ('algorithms', 'dp-greedy', 'Dynamic programming and greedy', 'advanced'::public.proficiency_level, 'Derive a recurrence and justify it.', 2),
  ('system-design', 'requirements', 'Requirements and back-of-envelope maths', 'beginner'::public.proficiency_level, 'Scope before designing.', 0),
  ('system-design', 'scaling', 'Load balancing, caching and queues', 'intermediate'::public.proficiency_level, 'Explain each primitive''s cost.', 1),
  ('system-design', 'data-consistency', 'Replication, sharding and consistency', 'advanced'::public.proficiency_level, 'Choose a consistency model on purpose.', 2),
  ('system-design', 'reliability', 'Failure modes and observability', 'advanced'::public.proficiency_level, 'Design for partial failure.', 3),
  ('system-design', 'llm-services', 'Designing LLM-backed services', 'advanced'::public.proficiency_level, 'Budget latency, cost and rate limits.', 4),
  ('machine-learning', 'ml-fundamentals', 'Bias, variance and validation', 'beginner'::public.proficiency_level, 'Explain overfitting with an example.', 0),
  ('machine-learning', 'metrics', 'Metrics and class imbalance', 'intermediate'::public.proficiency_level, 'Pick precision/recall/F1 deliberately.', 1),
  ('machine-learning', 'feature-engineering', 'Features and leakage', 'intermediate'::public.proficiency_level, 'Spot leakage before it inflates results.', 2),
  ('llm-rag', 'llm-basics', 'How LLMs work: tokens, context, temperature', 'beginner'::public.proficiency_level, 'Explain generation limits without mysticism.', 0),
  ('llm-rag', 'rag-architecture', 'RAG architecture end to end', 'intermediate'::public.proficiency_level, 'Describe ingest, retrieve, rerank, generate.', 1),
  ('llm-rag', 'retrieval-quality', 'Retrieval quality and reranking', 'advanced'::public.proficiency_level, 'Measure recall@k and improve it.', 2),
  ('llm-rag', 'hallucination', 'Hallucination, grounding and citations', 'advanced'::public.proficiency_level, 'Design a refusal path that works.', 3),
  ('llm-rag', 'rag-evaluation', 'Evaluating a RAG pipeline', 'advanced'::public.proficiency_level, 'Build an eval set and report faithfulness.', 4),
  ('llm-rag', 'llm-cost-latency', 'Cost, latency and streaming', 'advanced'::public.proficiency_level, 'Trade quality against budget explicitly.', 5),
  ('prompt-engineering', 'structured-output', 'Structured outputs and schemas', 'intermediate'::public.proficiency_level, 'Force validated JSON instead of prose.', 0),
  ('prompt-engineering', 'prompt-eval', 'Prompt evaluation and regression', 'advanced'::public.proficiency_level, 'Version prompts and measure changes.', 1),
  ('prompt-engineering', 'injection', 'Prompt injection and safety', 'advanced'::public.proficiency_level, 'Name the attack surface honestly.', 2),
  ('langgraph', 'graph-basics', 'State graphs, nodes and edges', 'beginner'::public.proficiency_level, 'Model a workflow as a graph.', 0),
  ('langgraph', 'checkpointing', 'Checkpointing and resumability', 'intermediate'::public.proficiency_level, 'Resume a workflow after failure.', 1),
  ('langgraph', 'control-flow', 'Conditional routing and retries', 'advanced'::public.proficiency_level, 'Keep agents on a controlled path.', 2),
  ('pandas', 'pd-basics', 'Indexing, groupby and joins', 'beginner'::public.proficiency_level, 'Reshape data without loops.', 0),
  ('pandas', 'pd-performance', 'Vectorisation and memory', 'intermediate'::public.proficiency_level, 'Make a slow pipeline fast.', 1)
on conflict (skill_id, subtopic_id) do update set
  title       = excluded.title,
  level       = excluded.level,
  objective   = excluded.objective,
  order_index = excluded.order_index;

-- ── resources: tier 0, the hand-curated catalogue ────────────────────────
-- curated_skill_id / curated_subtopic_id record which subtopic each row is the
-- canonical answer for. verified_at uses the catalogue's own assembly date
-- (taxonomy.yaml `updated: {stamp}`) for links marked `verified: true` in
-- curated.yaml — it is the date the link was hand-checked, not the date this
-- file ran. Everything else is stamped by the link-check job.
insert into public.resources
  (url, title, provider, kind, is_paid, license, tier,
   curated_skill_id, curated_subtopic_id, verified_at)
values
  ('https://docs.python.org/3/tutorial/introduction.html', 'The Python Tutorial — An Informal Introduction', 'Python Docs', 'docs'::public.resource_kind, false, 'PSF', 0, 'python', 'syntax-types', timestamptz '2026-11-01 00:00:00+00'),
  ('https://exercism.org/tracks/python', 'Python track — hands-on exercises', 'Exercism', 'exercise'::public.resource_kind, false, 'MIT', 0, 'python', 'syntax-types', timestamptz '2026-11-01 00:00:00+00'),
  ('https://docs.python.org/3/library/asyncio-task.html', 'asyncio — Coroutines and Tasks', 'Python Docs', 'docs'::public.resource_kind, false, 'PSF', 0, 'python', 'async-io', timestamptz '2026-11-01 00:00:00+00'),
  ('https://realpython.com/async-io-python/', 'Async IO in Python: A Complete Walkthrough', 'Real Python', 'article'::public.resource_kind, false, null, 0, 'python', 'async-io', timestamptz '2026-11-01 00:00:00+00'),
  ('https://docs.pytest.org/en/stable/getting-started.html', 'pytest — Get Started', 'pytest Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'python', 'typing-testing', timestamptz '2026-11-01 00:00:00+00'),
  ('https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods', 'MDN — HTTP request methods', 'MDN', 'docs'::public.resource_kind, false, 'CC-BY-SA', 0, 'fastapi', 'http-fundamentals', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/tutorial/path-params/', 'FastAPI — Path Parameters', 'FastAPI Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'routing', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/tutorial/query-params/', 'FastAPI — Query Parameters', 'FastAPI Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'routing', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/tutorial/body/', 'FastAPI — Request Body and Pydantic models', 'FastAPI Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'models-validation', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/tutorial/dependencies/', 'FastAPI — Dependencies', 'FastAPI Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'dependency-injection', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/advanced/testing-dependencies/', 'FastAPI — Testing dependencies with overrides', 'FastAPI Docs', 'exercise'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'dependency-injection', timestamptz '2026-11-01 00:00:00+00'),
  ('https://github.com/tiangolo/full-stack-fastapi-template', 'Full Stack FastAPI Template — test suite', 'GitHub', 'repo'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'dependency-injection', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/tutorial/security/', 'FastAPI — Security (OAuth2 and JWT)', 'FastAPI Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'auth', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/async/', 'FastAPI — Concurrency and async / await', 'FastAPI Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'async-endpoints', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/tutorial/sql-databases/', 'FastAPI — SQL (Relational) Databases', 'FastAPI Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'db-integration', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/tutorial/testing/', 'FastAPI — Testing', 'FastAPI Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'fastapi-testing', timestamptz '2026-11-01 00:00:00+00'),
  ('https://fastapi.tiangolo.com/deployment/concepts/', 'FastAPI — Deployment concepts', 'FastAPI Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'fastapi', 'fastapi-deploy', timestamptz '2026-11-01 00:00:00+00'),
  ('https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/', 'Docker — What is an image?', 'Docker Docs', 'docs'::public.resource_kind, false, null, 0, 'docker', 'images-containers', timestamptz '2026-11-01 00:00:00+00'),
  ('https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/', 'Docker — What is a container?', 'Docker Docs', 'docs'::public.resource_kind, false, null, 0, 'docker', 'images-containers', timestamptz '2026-11-01 00:00:00+00'),
  ('https://docs.docker.com/get-started/docker-concepts/building-images/', 'Docker — Building images', 'Docker Docs', 'docs'::public.resource_kind, false, null, 0, 'docker', 'dockerfile', timestamptz '2026-11-01 00:00:00+00'),
  ('https://github.com/docker/awesome-compose', 'Awesome Compose — reference stacks', 'GitHub', 'repo'::public.resource_kind, false, 'Apache-2.0', 0, 'docker', 'compose', timestamptz '2026-11-01 00:00:00+00'),
  ('https://docs.docker.com/reference/cli/docker/container/logs/', 'Docker — Debugging containers', 'Docker Docs', 'docs'::public.resource_kind, false, null, 0, 'docker', 'debugging', null),
  ('https://sqlbolt.com/', 'SQLBolt — Interactive SQL lessons', 'SQLBolt', 'exercise'::public.resource_kind, false, null, 0, 'sql', 'joins', timestamptz '2026-11-01 00:00:00+00'),
  ('https://pgexercises.com/', 'PG Exercises — Indexes and performance', 'PG Exercises', 'exercise'::public.resource_kind, false, null, 0, 'sql', 'indexing', timestamptz '2026-11-01 00:00:00+00'),
  ('https://www.postgresqltutorial.com/postgresql-window-function/', 'PostgreSQL Tutorial — Window functions', 'PostgreSQL Tutorial', 'article'::public.resource_kind, false, null, 0, 'sql', 'aggregation', null),
  ('https://www.postgresql.org/docs/current/using-explain.html', 'PostgreSQL Docs — Using EXPLAIN', 'PostgreSQL Docs', 'docs'::public.resource_kind, false, 'PostgreSQL', 0, 'postgresql', 'pg-index', timestamptz '2026-11-01 00:00:00+00'),
  ('https://www.postgresql.org/docs/current/ddl.html', 'PostgreSQL Docs — Data definition', 'PostgreSQL Docs', 'docs'::public.resource_kind, false, 'PostgreSQL', 0, 'postgresql', 'pg-schema', timestamptz '2026-11-01 00:00:00+00'),
  ('https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview', 'Anthropic — Introduction to prompt design', 'Anthropic Docs', 'docs'::public.resource_kind, false, null, 0, 'llm-rag', 'llm-basics', null),
  ('https://arxiv.org/abs/2005.11401', 'RAG for Knowledge-Intensive NLP Tasks (paper)', 'arXiv', 'paper'::public.resource_kind, false, null, 0, 'llm-rag', 'rag-architecture', timestamptz '2026-11-01 00:00:00+00'),
  ('https://docs.ragas.io/', 'Ragas — evaluation documentation', 'Ragas', 'docs'::public.resource_kind, false, 'Apache-2.0', 0, 'llm-rag', 'rag-evaluation', null),
  ('https://docs.ragas.io/en/stable/getstarted/', 'Ragas — get started', 'Ragas', 'exercise'::public.resource_kind, false, 'Apache-2.0', 0, 'llm-rag', 'rag-evaluation', null),
  ('https://github.com/pgvector/pgvector', 'pgvector — README and index types', 'GitHub', 'repo'::public.resource_kind, false, 'PostgreSQL', 0, 'llm-rag', 'retrieval-quality', timestamptz '2026-11-01 00:00:00+00'),
  ('https://python.langchain.com/docs/tutorials/rag/', 'LangChain — Build a RAG app (grounding patterns)', 'LangChain Docs', 'docs'::public.resource_kind, false, 'MIT', 0, 'llm-rag', 'hallucination', null),
  ('https://github.com/donnemartin/system-design-primer', 'The System Design Primer', 'GitHub', 'repo'::public.resource_kind, false, 'CC-BY-4.0', 0, 'system-design', 'requirements', timestamptz '2026-11-01 00:00:00+00'),
  ('https://github.com/ByteByteGoHq/system-design-101', 'System Design 101 — visual walkthroughs', 'GitHub', 'repo'::public.resource_kind, false, 'CC-BY-4.0', 0, 'system-design', 'scaling', timestamptz '2026-11-01 00:00:00+00'),
  ('https://dataintensive.net/', 'Designing Data-Intensive Applications (book)', 'dataintensive.net', 'book'::public.resource_kind, true, null, 0, 'system-design', 'data-consistency', timestamptz '2026-11-01 00:00:00+00'),
  ('https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell', 'Pro Git — Branching', 'Git SCM', 'docs'::public.resource_kind, false, 'GPL-4.0-docs', 0, 'git', 'branching', timestamptz '2026-11-01 00:00:00+00'),
  ('https://learngitbranching.js.org/', 'Learn Git Branching — interactive', 'learngitbranching.js.org', 'exercise'::public.resource_kind, false, null, 0, 'git', 'branching', timestamptz '2026-11-01 00:00:00+00'),
  ('https://github.com/promptfoo/promptfoo', 'promptfoo — testing and evals for LLM apps', 'GitHub', 'repo'::public.resource_kind, false, 'MIT', 0, 'testing', 'llm-testing', timestamptz '2026-11-01 00:00:00+00')
on conflict (url) do update set
  title               = excluded.title,
  provider            = excluded.provider,
  kind                = excluded.kind,
  is_paid             = excluded.is_paid,
  license             = excluded.license,
  tier                = least(public.resources.tier, excluded.tier),
  curated_skill_id    = excluded.curated_skill_id,
  curated_subtopic_id = excluded.curated_subtopic_id,
  verified_at         = coalesce(public.resources.verified_at, excluded.verified_at),
  updated_at          = now();

commit;

-- ── Post-seed sanity check ────────────────────────────────────────────────
do $do$
declare
  n_skills integer;
  n_subtopics integer;
  n_resources integer;
begin
  select count(*) into n_skills from public.skills;
  select count(*) into n_subtopics from public.skill_subtopics;
  select count(*) into n_resources from public.resources;
  raise notice 'seeded: % skills, % subtopics, % resources', n_skills, n_subtopics, n_resources;
  if n_skills <> 31 then
    raise warning 'expected 31 skills, found % — is the seed out of date? '
      'Run: python scripts/gen_seed.py', n_skills;
  end if;
  if n_subtopics < 100 then
    raise warning 'expected at least 100 subtopics, found % — is the seed out of date?',
      n_subtopics;
  end if;
end;
$do$;
