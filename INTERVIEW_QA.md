# Interview Questions & Answers
## Explainable Healthcare Risk Intelligence Platform
### Principal AI Architect Level — Google DeepMind Standards

---

## SECTION 1: Machine Learning & Model Design

**Q1: Why did you choose XGBoost, Random Forest, and LightGBM over deep learning for tabular clinical data?**

A: Tabular clinical data has specific characteristics that favor gradient boosting and ensemble tree methods:

1. **Sample efficiency** — Clinical datasets are often small (thousands, not millions). Tree ensembles generalize well with limited data; deep networks overfit without massive datasets.
2. **Feature interpretability** — Tree models natively produce feature importance scores, which are essential for clinical explainability and regulatory compliance.
3. **Handling mixed data types** — Clinical data mixes continuous vitals, binary flags, and categorical variables. Trees handle this natively without extensive preprocessing.
4. **Training speed** — XGBoost and LightGBM train in minutes on CPU; deep networks require GPU hours.
5. **Robustness to missing values** — XGBoost handles NaN natively; clinical data always has missingness.

The ensemble approach averages predictions from all three, reducing variance and improving calibration — critical for medical risk scores.

---

**Q2: How does your hyperparameter tuning with Optuna work, and why Optuna over GridSearch?**

A: Optuna uses **Tree-structured Parzen Estimator (TPE)** — a Bayesian optimization algorithm that builds a probabilistic model of the objective function and samples from regions likely to improve performance.

Advantages over GridSearch:
- **Efficiency**: Optuna evaluates ~50 trials vs. GridSearch's exponential combinations
- **Pruning**: Optuna's MedianPruner stops unpromising trials early (saves 60-70% compute)
- **Continuous search space**: Can optimize over continuous ranges (learning_rate: 0.001-0.3) not just discrete grids
- **Parallelism**: Distributed optimization across multiple workers

In our pipeline, each trial runs 5-fold stratified cross-validation and returns mean AUC-ROC. Optuna learns which hyperparameter regions produce high AUC and focuses sampling there.

---

**Q3: How do you handle class imbalance in disease prediction?**

A: We use a multi-pronged approach:

1. **SMOTE (Synthetic Minority Oversampling Technique)** — Generates synthetic minority class samples by interpolating between existing samples in feature space. Applied only to training data, never test data.
2. **Class weights** — Random Forest and LightGBM use `class_weight='balanced'`, which inversely weights samples by class frequency.
3. **Threshold tuning** — Instead of using 0.5 as the decision threshold, we optimize the threshold on a validation set to maximize F1 or recall (depending on clinical priority — in healthcare, recall/sensitivity is usually more important than precision).
4. **Evaluation metrics** — We use AUC-ROC and Average Precision (AUC-PR) rather than accuracy, since accuracy is misleading on imbalanced data.

---

**Q4: Explain the difference between SHAP TreeExplainer and KernelExplainer. When do you use each?**

A: 

**TreeExplainer** (preferred):
- Exact SHAP values computed in O(TLD²) time where T=trees, L=leaves, D=depth
- Uses the tree structure directly — no sampling needed
- Consistent with the model's actual decision boundaries
- Fast: milliseconds per prediction

**KernelExplainer** (fallback):
- Model-agnostic: works with any black-box model
- Approximates SHAP values by sampling perturbations of the input
- Slow: seconds to minutes per prediction
- Less accurate due to sampling approximation

We use TreeExplainer for XGBoost, Random Forest, and LightGBM (all tree-based). KernelExplainer is the fallback for any model that doesn't support TreeExplainer (e.g., neural networks, SVMs).

---

**Q5: What is the difference between global and local explainability?**

A:

**Global Explainability** — Describes model behavior across the entire population:
- Mean |SHAP| values across all training samples
- Feature importance from the model (Gini impurity reduction for RF)
- Partial Dependence Plots (PDPs)
- Use case: "Which features does the model rely on most overall?"

**Local Explainability** — Describes a single prediction:
- SHAP values for one patient's prediction
- LIME explanation for one instance
- Use case: "Why did the model predict 72% diabetes risk for THIS patient?"

In healthcare, local explainability is critical for clinical decision support — a clinician needs to understand why a specific patient is high-risk, not just which features matter globally.

---

## SECTION 2: LLM Fine-Tuning

**Q6: Explain QLoRA. How does it differ from standard LoRA?**

A:

**LoRA (Low-Rank Adaptation)**:
- Freezes the pre-trained model weights
- Adds trainable low-rank decomposition matrices (A and B) to attention layers
- Weight update: ΔW = BA where B ∈ R^(d×r), A ∈ R^(r×k), r << min(d,k)
- Reduces trainable parameters from billions to millions
- Full precision (FP16/BF16) throughout

**QLoRA (Quantized LoRA)**:
- Quantizes the frozen base model to **4-bit NF4** (Normal Float 4) format
- Reduces memory from ~16GB (FP16) to ~4GB (4-bit) for a 7B model
- Introduces **double quantization** — quantizes the quantization constants themselves
- Uses **paged optimizers** to handle memory spikes during gradient computation
- LoRA adapters remain in FP16 for training precision

Key insight: QLoRA enables fine-tuning 70B parameter models on a single 48GB GPU, which was previously impossible. The quantization error is minimal because NF4 is information-theoretically optimal for normally distributed weights.

---

**Q7: What is PEFT and what problem does it solve?**

A: PEFT (Parameter-Efficient Fine-Tuning) is a HuggingFace library that implements multiple techniques for fine-tuning large models without updating all parameters:

- **LoRA/QLoRA** — Low-rank adapter matrices
- **Prefix Tuning** — Prepends trainable tokens to the input
- **Prompt Tuning** — Learns soft prompt embeddings
- **IA³** — Scales activations with learned vectors

The problem it solves: Full fine-tuning of Llama 3 8B requires ~60GB GPU memory and updates 8 billion parameters. PEFT with QLoRA reduces this to ~6GB and updates only ~0.1% of parameters (8M out of 8B), while achieving comparable performance on domain-specific tasks.

In our platform, we use PEFT to fine-tune Llama 3 on clinical risk explanation data, producing a model that generates accurate, empathetic, evidence-based narratives without catastrophic forgetting of general medical knowledge.

---

**Q8: How do you prevent catastrophic forgetting during fine-tuning?**

A: Several strategies:

1. **LoRA architecture** — By only training adapter matrices and keeping base weights frozen, the model retains its pre-trained knowledge. The adapters learn the delta (domain-specific adjustment) rather than overwriting existing knowledge.
2. **Low learning rate** — We use 2e-4, much lower than pre-training rates, to make small adjustments.
3. **Cosine LR scheduler with warmup** — Gradual learning rate increase prevents large early updates.
4. **Small dataset** — Fine-tuning on a focused clinical dataset (not a massive general corpus) limits the scope of weight changes.
5. **Evaluation on held-out general benchmarks** — Monitor performance on general medical QA to detect forgetting.

---

**Q9: How does your RAG pipeline work end-to-end?**

A:

```
PDF → PyPDFLoader → RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
    → HuggingFace Embeddings (all-MiniLM-L6-v2, 384-dim)
    → ChromaDB (cosine similarity index, HNSW)

Query → Embed query → ChromaDB similarity search (top-k=5)
      → Retrieved chunks → Context assembly
      → Prompt template (context + patient data + question)
      → Fine-tuned Llama 3 → Grounded answer
```

Key design decisions:
- **Chunk overlap (200 chars)** — Prevents context loss at chunk boundaries
- **Cosine similarity** — Better than L2 for semantic similarity of normalized embeddings
- **HNSW index** — Approximate nearest neighbor search, O(log n) query time
- **Sentence Transformers** — Bi-encoder architecture, fast inference vs. cross-encoders
- **Grounding prompt** — Explicitly instructs the LLM to answer only from provided context, reducing hallucination

---

## SECTION 3: System Architecture & Engineering

**Q10: Why FastAPI over Django or Flask for this platform?**

A:

1. **Async-native** — FastAPI is built on Starlette/asyncio. Our ML inference, database queries, and LLM calls are all I/O-bound. Async allows handling hundreds of concurrent requests without thread blocking.
2. **Automatic OpenAPI docs** — Critical for healthcare APIs where documentation is a compliance requirement.
3. **Pydantic validation** — Type-safe request/response validation with automatic error messages. Prevents invalid clinical data from reaching ML models.
4. **Performance** — FastAPI benchmarks at ~3x Flask throughput for async workloads.
5. **Dependency injection** — Clean pattern for database sessions, auth, and service injection.

Django would add unnecessary ORM complexity (we use SQLAlchemy for async support). Flask lacks native async and type validation.

---

**Q11: Explain your JWT + RBAC security architecture.**

A:

**JWT Flow**:
1. User logs in → server verifies bcrypt password hash
2. Server issues short-lived access token (30 min) + long-lived refresh token (7 days)
3. Access token contains: `sub` (user_id), `email`, `role`, `exp`, `iat`
4. Client sends `Authorization: Bearer <token>` on every request
5. FastAPI dependency decodes and validates token on each request
6. Refresh token exchanges for new access token without re-authentication

**RBAC**:
- 5 roles: admin, clinician, researcher, patient, readonly
- Each role maps to a set of permissions (predict:write, patient:read, etc.)
- FastAPI `Depends(require_permission(Permission.PREDICT_WRITE))` enforces at route level
- No permission = 403 Forbidden

**Security hardening**:
- Passwords hashed with bcrypt (cost factor 12)
- PII fields (SSN, DOB) encrypted with Fernet AES-128-CBC before storage
- HTTPS enforced via Kubernetes Ingress + cert-manager
- Rate limiting at Nginx Ingress level

---

**Q12: How does your database schema support HIPAA compliance?**

A:

1. **Encryption at rest** — PostgreSQL data encrypted via AWS RDS encryption (AES-256)
2. **Field-level encryption** — SSN and DOB encrypted with Fernet before storage, even if DB is compromised
3. **Audit logs** — Immutable `audit_logs` table records every access, modification, and deletion with user_id, IP, timestamp
4. **Soft deletes** — Patient records support GDPR right-to-erasure via hard delete with audit trail
5. **Minimum necessary data** — Schema only stores clinically relevant fields, no unnecessary PII
6. **Access controls** — PostgreSQL row-level security + application-level RBAC
7. **Backup encryption** — S3 backups encrypted with KMS

---

**Q13: How do you ensure ML model predictions are reproducible and auditable?**

A:

1. **Prediction snapshots** — Every prediction stores the exact `input_features` JSON at prediction time. If features change, historical predictions remain accurate.
2. **Model versioning** — Each prediction records `model_version`. Multiple model versions can coexist.
3. **Model registry** — `model_registry` table tracks artifact paths, training metrics, deployment dates.
4. **Deterministic inference** — Models loaded from fixed pickle files; no randomness in inference.
5. **SHAP/LIME persistence** — Explanations stored in JSONB alongside predictions for audit.
6. **Audit trail** — All prediction requests logged with user, timestamp, IP.

---

## SECTION 4: MLOps & Deployment

**Q14: Describe your CI/CD pipeline and what happens on a failed deployment.**

A:

**Pipeline stages**:
1. `test-backend` — pytest with coverage, ruff linting, mypy type checking
2. `test-frontend` — TypeScript compilation, Vite build
3. `security-scan` — Trivy scans for CVEs in dependencies and Docker images
4. `build-and-push` — Multi-stage Docker build, push to ECR with SHA tag
5. `deploy` — `kubectl set image` triggers rolling update (maxSurge=1, maxUnavailable=0)
6. Smoke test — curl /health endpoint

**On failure**:
- Rolling update strategy means old pods stay running until new pods pass readiness probes
- If smoke test fails: `kubectl rollout undo` automatically reverts to previous ReplicaSet
- GitHub Actions marks deployment as failed, sends notification
- Zero downtime guaranteed by `maxUnavailable: 0`

---

**Q15: How does your Kubernetes HPA (Horizontal Pod Autoscaler) work?**

A: The HPA monitors CPU and memory metrics via the Kubernetes Metrics Server and scales the deployment between 3-10 replicas:

- Scale up when CPU > 70% or memory > 80% (averaged across pods)
- Scale down when metrics drop below thresholds (with a 5-minute cooldown)
- `minReplicas: 3` ensures high availability across 3 AZs even at low load

For ML workloads, we also consider custom metrics (prediction latency via Prometheus) using the Custom Metrics API. If p99 latency exceeds 2 seconds, we scale up regardless of CPU.

---

**Q16: How do you monitor model drift in production?**

A:

1. **Data drift** — Track input feature distributions over time (mean, std, percentiles). Alert when KL divergence between current and training distributions exceeds threshold.
2. **Prediction drift** — Monitor risk score distribution. If the proportion of "high risk" predictions shifts significantly, investigate.
3. **Performance drift** — For patients with known outcomes (e.g., diagnosed 6 months later), compute retrospective AUC. Schedule monthly retraining if AUC drops >3%.
4. **SHAP drift** — Monitor global SHAP importance. If a previously unimportant feature becomes dominant, it may indicate data quality issues.

Tools: Prometheus for metrics collection, Grafana for dashboards, custom Python scripts for statistical tests (KS test, PSI — Population Stability Index).

---

## SECTION 5: Advanced Topics

**Q17: How would you scale this platform to handle 1 million predictions per day?**

A:

1. **Async inference** — Current FastAPI async architecture handles ~500 req/s per pod. 10 pods = 5000 req/s = 432M/day. Already sufficient.
2. **Model serving** — Move from in-process models to dedicated serving (TorchServe, Triton Inference Server) for GPU-accelerated inference and batching.
3. **Caching** — Cache predictions for identical feature vectors (Redis, TTL=1hr). Many patients have similar profiles.
4. **Read replicas** — PostgreSQL read replicas for prediction history queries.
5. **Async prediction queue** — For non-real-time use cases, use Celery + Redis to queue predictions and return job IDs. Clients poll for results.
6. **CDN** — CloudFront for frontend assets.
7. **Database sharding** — Partition `prediction_records` by `created_at` (monthly partitions) for query performance.

---

**Q18: What are the ethical considerations in deploying AI for healthcare risk prediction?**

A:

1. **Algorithmic bias** — Models trained on historical data may perpetuate disparities. We must evaluate performance across demographic subgroups (age, gender, ethnicity) and ensure AUC is comparable across groups.
2. **Explainability as a right** — Patients and clinicians have the right to understand why a risk score was assigned. SHAP/LIME explanations fulfill this.
3. **Human-in-the-loop** — AI predictions are decision support, not decisions. The platform explicitly states "consult your healthcare provider." No automated treatment decisions.
4. **Calibration** — A model that says 70% risk should be right 70% of the time. Poorly calibrated models mislead clinicians. We use Platt scaling or isotonic regression for calibration.
5. **Consent and data privacy** — HIPAA compliance, data minimization, right to erasure.
6. **Feedback loops** — If high-risk patients receive more interventions, they appear healthier in follow-up data, creating survivorship bias in retraining data.

---

**Q19: How does ChromaDB's HNSW index work for vector similarity search?**

A: HNSW (Hierarchical Navigable Small World) is a graph-based approximate nearest neighbor algorithm:

1. **Multi-layer graph** — Vectors are organized in a hierarchy of graphs. Upper layers have fewer nodes (long-range connections), lower layers have all nodes (short-range connections).
2. **Greedy search** — Start at the top layer, greedily navigate to the nearest neighbor, then descend to the next layer and repeat.
3. **Complexity** — O(log n) query time vs. O(n) for brute force. For 1M documents, HNSW is ~1000x faster.
4. **Approximate** — May miss the true nearest neighbor with small probability (controlled by `ef` parameter). In RAG, approximate is acceptable — we need relevant documents, not the mathematically closest.
5. **Memory** — Stores the graph in memory. For 1M 384-dim embeddings: ~1.5GB.

ChromaDB uses HNSW with cosine similarity (normalized dot product), which is appropriate for semantic similarity of sentence embeddings.

---

**Q20: How would you A/B test a new model version in production?**

A:

1. **Traffic splitting** — Use Kubernetes Ingress or Istio to route X% of traffic to the new model (canary deployment). Start with 5%, monitor, increase to 50%, then 100%.
2. **Shadow mode** — Run the new model in parallel with the current model, log both predictions, but only return the current model's result to users. Compare offline.
3. **Metrics to monitor**:
   - Prediction latency (p50, p95, p99)
   - Risk score distribution (should be similar)
   - Error rate
   - Downstream outcomes (if available)
4. **Statistical significance** — Use a two-sample t-test or Mann-Whitney U test on AUC scores. Require p < 0.05 and practical significance (>1% AUC improvement) before full rollout.
5. **Rollback criteria** — Automatic rollback if error rate > 1% or latency p99 > 3s.

---

## SECTION 6: System Design

**Q21: Design the data pipeline for ingesting real-time EHR data into this platform.**

A:

```
EHR System (HL7 FHIR API)
    → AWS EventBridge (event routing)
    → Kinesis Data Streams (real-time ingestion, 24hr retention)
    → Lambda (FHIR → internal schema transformation)
    → SQS (decoupling, retry logic)
    → Celery Worker (feature engineering + prediction)
    → PostgreSQL (store prediction)
    → SNS (alert clinician if high risk)
```

Key considerations:
- **FHIR R4 standard** — Use FHIR resources (Patient, Observation, Condition) for interoperability
- **Idempotency** — Use patient_id + observation_timestamp as deduplication key
- **Schema validation** — Validate FHIR resources before processing
- **Dead letter queue** — Failed messages go to DLQ for manual review
- **HIPAA** — All data encrypted in transit (TLS 1.3) and at rest (KMS)

---

**Q22: How would you handle a situation where the model gives a wrong prediction that leads to patient harm?**

A: This is a critical question about AI safety in healthcare:

1. **Prevention** (before deployment):
   - Rigorous validation on held-out test sets, including edge cases
   - Clinical validation with domain experts before deployment
   - Calibration testing — ensure predicted probabilities match observed outcomes
   - Bias audits across demographic groups

2. **Detection** (in production):
   - Confidence thresholds — flag predictions with low confidence for human review
   - Out-of-distribution detection — flag inputs that differ significantly from training data
   - Anomaly detection on prediction outputs

3. **Response** (after incident):
   - Immediate audit of the specific prediction using stored input_features and SHAP values
   - Root cause analysis: Was it a data quality issue? Model failure? Edge case?
   - Temporary rollback to previous model version if systemic issue
   - Incident report and regulatory notification if required

4. **Systemic safeguards**:
   - The platform is decision support, not autonomous decision-making
   - All predictions include confidence scores and uncertainty estimates
   - Clinician override is always available and logged
   - Regular model revalidation against new outcome data

---

*This document covers Principal AI Architect-level depth across ML, LLM, system design, MLOps, ethics, and production engineering.*
