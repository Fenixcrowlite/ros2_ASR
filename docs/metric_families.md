# Metric Families

The thesis groups ASR metrics into families because ASR suitability in robotics is multi-objective. A provider with low WER may still be unsuitable for interactive robot control if it has high latency, requires internet access, or cannot run under local hardware constraints.

| Metric family | Main metrics | Research question |
|---|---|---|
| Recognition quality | WER, CER, SER | How accurately does the provider transcribe speech? |
| Performance and real-time behavior | latency p50/p95, end-to-end RTF, provider compute RTF, throughput | Can the provider satisfy real-time or near-real-time ROS2 usage? |
| Noise robustness | WER by SNR, noise degradation | How stable is recognition under degraded acoustic conditions? |
| Resource usage | CPU, RAM, GPU memory, model size | Can the provider run on available local laboratory hardware? |
| Cost and deployment | direct API cost, offline capability, credentials, internet dependency | Is the provider practical for repeated laboratory or robotic use? |
| Scenario suitability | embedded, batch, analytics, dialog scores | Which provider fits which robotic or ASR workflow best? |

## Recognition Quality

Main metrics: WER, CER and SER.

This family answers how accurately each provider transcribes the clean source utterances. Lower WER, CER and SER indicate fewer transcription errors. WER is the primary word-level quality metric, CER gives character-level sensitivity, and SER shows whether whole utterances contain at least one sentence-level error.

The limitation is sample scale. The final thesis benchmark uses 10 clean LibriSpeech source utterances, so quality values are useful for prototype comparison but not for large-scale statistical ASR claims.

## Performance And Real-Time Behavior

Main metrics: final latency p50/p95, end-to-end RTF, provider compute RTF and throughput.

This family answers whether the provider can satisfy real-time or near-real-time ROS2 usage. Lower latency means faster operator-facing response. End-to-end RTF below 1.0 means the full processing path is faster than real time; values above 1.0 indicate slower-than-real-time processing. Provider compute RTF is secondary because it excludes surrounding pipeline overhead.

The limitation is that latency depends on workstation load, network conditions for cloud providers, and the batch-oriented benchmark harness.

## Noise Robustness

Main metrics: WER by SNR and noise degradation in percentage points.

This family answers how stable recognition remains when clean speech is degraded. Lower WER under lower SNR and smaller degradation indicate better robustness.

The limitation is acoustic coverage. The benchmark uses derived synthetic white-noise variants, so the results show robustness trends rather than full real-world laboratory acoustic coverage.

## Resource Usage

Main metrics: CPU, RAM, GPU memory and model size.

This family answers whether local providers can run on available laboratory hardware. Lower RAM, GPU memory and model size are easier to deploy on constrained workstations or embedded-style setups.

The limitation is observability. Some resource values are unavailable or describe host-side benchmark process behavior rather than internal cloud provider infrastructure. Availability flags in the final CSV table identify which resource fields were available.

## Cost And Deployment

Main metrics: direct API cost, offline capability, credential requirements and internet dependency.

This family answers whether a provider is practical for repeated laboratory or robotic use. Local providers have zero direct API cost in the thesis tables, but hardware and maintenance costs are not monetized. Cloud providers may offer strong accuracy, but require connectivity, credentials and potentially paid API usage.

The limitation is that direct API cost is not a complete total cost of ownership model. Missing cloud prices are marked as not estimated rather than inferred.

## Scenario Suitability

Main metrics: embedded, batch, analytics and dialog scores.

This family answers which provider best fits a workflow rather than which provider is universally best. Scenario scores are heuristic normalized decision-support indices derived from quality, performance, robustness, deployment and cost fields. They are not direct benchmark measurements and should not be interpreted as absolute scientific metrics.

The limitation is that the score weights encode thesis-specific priorities. They summarize suitability for decision support; the underlying metric tables remain the primary evidence.
