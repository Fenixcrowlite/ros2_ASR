# Safe Refactor Sequence

1. Completed low risk, high value
   - expanded tests around profile resolution, provider construction, benchmark artifact semantics
   - added benchmark-core CLI wrapper
   - redirected `make bench` away from `asr_benchmark.runner`
   - redirected `make report` to canonical benchmark summary artifacts
2. Next low/medium risk
   - wire GUI profile or mark it deprecated explicitly
   - publish a single documented benchmark operator flow and de-emphasize direct legacy runner usage
3. Medium risk
   - move `asr_ros` and `asr_benchmark` under explicit compatibility packaging/docs
   - stop referencing old launch files in beginner/operator docs
4. Medium/high risk
   - port any remaining useful logic from legacy `MetricsCollector` into canonical benchmark core
   - add explicit pipeline latency and resource metrics in canonical benchmark path
5. High risk
   - remove legacy services/messages only after compatibility tests and docs are migrated
