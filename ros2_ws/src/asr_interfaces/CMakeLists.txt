cmake_minimum_required(VERSION 3.8)
project(asr_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/AudioChunk.msg"
  "msg/AudioSegment.msg"
  "msg/SpeechActivity.msg"
  "msg/WordTimestamp.msg"
  "msg/AsrResult.msg"
  "msg/AsrResultPartial.msg"
  "msg/AsrMetrics.msg"
  "msg/AsrEvent.msg"
  "msg/NodeStatus.msg"
  "msg/SessionStatus.msg"
  "msg/BenchmarkJobStatus.msg"
  "msg/DatasetStatus.msg"
  "msg/ExperimentSummary.msg"
  "msg/ResultArtifactRef.msg"
  "msg/MetricArtifactRef.msg"
  "srv/RecognizeOnce.srv"
  "srv/SetAsrBackend.srv"
  "srv/GetAsrStatus.srv"
  "srv/StartRuntimeSession.srv"
  "srv/StopRuntimeSession.srv"
  "srv/ReconfigureRuntime.srv"
  "srv/ListProfiles.srv"
  "srv/ListBackends.srv"
  "srv/ValidateConfig.srv"
  "srv/RegisterDataset.srv"
  "srv/ListDatasets.srv"
  "srv/GetBenchmarkStatus.srv"
  "action/Transcribe.action"
  "action/StreamSession.action"
  "action/RunBenchmarkExperiment.action"
  "action/ImportDataset.action"
  "action/GenerateReport.action"
  "action/DownloadModel.action"
  DEPENDENCIES std_msgs builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
