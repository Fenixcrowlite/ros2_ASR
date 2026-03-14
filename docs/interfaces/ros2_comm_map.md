# ROS2 Communication Map

## Topics
- `/asr/runtime/audio/raw` (`AudioChunk`)
- `/asr/runtime/audio/preprocessed` (`AudioChunk`)
- `/asr/runtime/vad/activity` (`SpeechActivity`)
- `/asr/runtime/audio/segments` (`AudioSegment`)
- `/asr/runtime/results/partial` (`AsrResultPartial`)
- `/asr/runtime/results/final` (`AsrResult`)
- `/asr/status/nodes` (`NodeStatus`)
- `/asr/status/sessions` (`SessionStatus`)
- `/benchmark/status` (`BenchmarkJobStatus`)

## Services
- `/asr/runtime/start_session`
- `/asr/runtime/stop_session`
- `/asr/runtime/reconfigure`
- `/asr/runtime/recognize_once`
- `/config/list_profiles`
- `/asr/runtime/list_backends`
- `/config/validate`
- `/datasets/register`
- `/datasets/list`
- `/benchmark/get_status`

## Actions
- `/benchmark/run_experiment` (`RunBenchmarkExperiment`)
- `/datasets/import` (`ImportDataset`)
- Runtime stream/report actions are defined in interfaces and reserved for next expansion stage.
