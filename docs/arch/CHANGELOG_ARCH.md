# Architecture Changelog

## Added

### Nodes
- /asr_gateway_client_bridge
- /asr_gateway_runtime_observer

### Topics
- /asr/runtime/audio/preprocessed
- /asr/runtime/audio/raw
- /asr/runtime/audio/segments
- /asr/runtime/results/final
- /asr/runtime/results/partial
- /asr/runtime/vad/activity
- /asr/status/nodes
- /asr/status/sessions
- /parameter_events
- /rosout

### Services
- /asr_gateway_client_bridge/describe_parameters
- /asr_gateway_client_bridge/get_parameter_types
- /asr_gateway_client_bridge/get_parameters
- /asr_gateway_client_bridge/get_type_description
- /asr_gateway_client_bridge/list_parameters
- /asr_gateway_client_bridge/set_parameters
- /asr_gateway_client_bridge/set_parameters_atomically
- /asr_gateway_runtime_observer/describe_parameters
- /asr_gateway_runtime_observer/get_parameter_types
- /asr_gateway_runtime_observer/get_parameters
- /asr_gateway_runtime_observer/get_type_description
- /asr_gateway_runtime_observer/list_parameters
- /asr_gateway_runtime_observer/set_parameters
- /asr_gateway_runtime_observer/set_parameters_atomically
- /asr_orchestrator_node/describe_parameters
- /asr_orchestrator_node/get_parameter_types
- /asr_orchestrator_node/get_parameters
- /asr_orchestrator_node/get_type_description
- /asr_orchestrator_node/list_parameters
- /asr_orchestrator_node/set_parameters
- /asr_orchestrator_node/set_parameters_atomically
- /audio_input_node/describe_parameters
- /audio_input_node/get_parameter_types
- /audio_input_node/get_parameters
- /audio_input_node/get_type_description
- /audio_input_node/list_parameters
- /audio_input_node/set_parameters
- /audio_input_node/set_parameters_atomically
- /audio_preprocess_node/describe_parameters
- /audio_preprocess_node/get_parameter_types
- /audio_preprocess_node/get_parameters
- /audio_preprocess_node/get_type_description
- /audio_preprocess_node/list_parameters
- /audio_preprocess_node/set_parameters
- /audio_preprocess_node/set_parameters_atomically
- /benchmark_manager_node/describe_parameters
- /benchmark_manager_node/get_parameter_types
- /benchmark_manager_node/get_parameters
- /benchmark_manager_node/get_type_description
- /benchmark_manager_node/list_parameters
- /benchmark_manager_node/set_parameters
- /benchmark_manager_node/set_parameters_atomically
- /vad_segmenter_node/describe_parameters
- /vad_segmenter_node/get_parameter_types
- /vad_segmenter_node/get_parameters
- /vad_segmenter_node/get_type_description
- /vad_segmenter_node/list_parameters
- /vad_segmenter_node/set_parameters
- /vad_segmenter_node/set_parameters_atomically

## Removed

### Nodes
- None

### Topics
- None

### Services
- None

## Changed Types
- service /asr/runtime/audio/reconfigure: ReconfigureRuntime -> asr_interfaces/srv/ReconfigureRuntime
- service /asr/runtime/audio/start_session: StartRuntimeSession -> asr_interfaces/srv/StartRuntimeSession
- service /asr/runtime/audio/stop_session: StopRuntimeSession -> asr_interfaces/srv/StopRuntimeSession
- service /asr/runtime/get_status: GetAsrStatus -> asr_interfaces/srv/GetAsrStatus
- service /asr/runtime/list_backends: ListBackends -> asr_interfaces/srv/ListBackends
- service /asr/runtime/preprocess/reconfigure: ReconfigureRuntime -> asr_interfaces/srv/ReconfigureRuntime
- service /asr/runtime/recognize_once: RecognizeOnce -> asr_interfaces/srv/RecognizeOnce
- service /asr/runtime/reconfigure: ReconfigureRuntime -> asr_interfaces/srv/ReconfigureRuntime
- service /asr/runtime/start_session: StartRuntimeSession -> asr_interfaces/srv/StartRuntimeSession
- service /asr/runtime/stop_session: StopRuntimeSession -> asr_interfaces/srv/StopRuntimeSession
- service /asr/runtime/vad/reconfigure: ReconfigureRuntime -> asr_interfaces/srv/ReconfigureRuntime
- service /benchmark/get_status: GetBenchmarkStatus -> asr_interfaces/srv/GetBenchmarkStatus
- service /config/list_profiles: ListProfiles -> asr_interfaces/srv/ListProfiles
- service /config/validate: ValidateConfig -> asr_interfaces/srv/ValidateConfig
- service /datasets/list: ListDatasets -> asr_interfaces/srv/ListDatasets
- service /datasets/register: RegisterDataset -> asr_interfaces/srv/RegisterDataset

## Connectivity

### Added edges
- action|server|/benchmark_manager_node|/benchmark/run_experiment|asr_interfaces/action/RunBenchmarkExperiment
- action|server|/benchmark_manager_node|/datasets/import|asr_interfaces/action/ImportDataset
- service|server|/asr_gateway_client_bridge|/asr_gateway_client_bridge/describe_parameters|rcl_interfaces/srv/DescribeParameters
- service|server|/asr_gateway_client_bridge|/asr_gateway_client_bridge/get_parameter_types|rcl_interfaces/srv/GetParameterTypes
- service|server|/asr_gateway_client_bridge|/asr_gateway_client_bridge/get_parameters|rcl_interfaces/srv/GetParameters
- service|server|/asr_gateway_client_bridge|/asr_gateway_client_bridge/get_type_description|type_description_interfaces/srv/GetTypeDescription
- service|server|/asr_gateway_client_bridge|/asr_gateway_client_bridge/list_parameters|rcl_interfaces/srv/ListParameters
- service|server|/asr_gateway_client_bridge|/asr_gateway_client_bridge/set_parameters_atomically|rcl_interfaces/srv/SetParametersAtomically
- service|server|/asr_gateway_client_bridge|/asr_gateway_client_bridge/set_parameters|rcl_interfaces/srv/SetParameters
- service|server|/asr_gateway_runtime_observer|/asr_gateway_runtime_observer/describe_parameters|rcl_interfaces/srv/DescribeParameters
- service|server|/asr_gateway_runtime_observer|/asr_gateway_runtime_observer/get_parameter_types|rcl_interfaces/srv/GetParameterTypes
- service|server|/asr_gateway_runtime_observer|/asr_gateway_runtime_observer/get_parameters|rcl_interfaces/srv/GetParameters
- service|server|/asr_gateway_runtime_observer|/asr_gateway_runtime_observer/get_type_description|type_description_interfaces/srv/GetTypeDescription
- service|server|/asr_gateway_runtime_observer|/asr_gateway_runtime_observer/list_parameters|rcl_interfaces/srv/ListParameters
- service|server|/asr_gateway_runtime_observer|/asr_gateway_runtime_observer/set_parameters_atomically|rcl_interfaces/srv/SetParametersAtomically
- service|server|/asr_gateway_runtime_observer|/asr_gateway_runtime_observer/set_parameters|rcl_interfaces/srv/SetParameters
- service|server|/asr_orchestrator_node|/asr/runtime/get_status|asr_interfaces/srv/GetAsrStatus
- service|server|/asr_orchestrator_node|/asr/runtime/list_backends|asr_interfaces/srv/ListBackends
- service|server|/asr_orchestrator_node|/asr/runtime/recognize_once|asr_interfaces/srv/RecognizeOnce
- service|server|/asr_orchestrator_node|/asr/runtime/reconfigure|asr_interfaces/srv/ReconfigureRuntime
- service|server|/asr_orchestrator_node|/asr/runtime/start_session|asr_interfaces/srv/StartRuntimeSession
- service|server|/asr_orchestrator_node|/asr/runtime/stop_session|asr_interfaces/srv/StopRuntimeSession
- service|server|/asr_orchestrator_node|/asr_orchestrator_node/describe_parameters|rcl_interfaces/srv/DescribeParameters
- service|server|/asr_orchestrator_node|/asr_orchestrator_node/get_parameter_types|rcl_interfaces/srv/GetParameterTypes
- service|server|/asr_orchestrator_node|/asr_orchestrator_node/get_parameters|rcl_interfaces/srv/GetParameters
- service|server|/asr_orchestrator_node|/asr_orchestrator_node/get_type_description|type_description_interfaces/srv/GetTypeDescription
- service|server|/asr_orchestrator_node|/asr_orchestrator_node/list_parameters|rcl_interfaces/srv/ListParameters
- service|server|/asr_orchestrator_node|/asr_orchestrator_node/set_parameters_atomically|rcl_interfaces/srv/SetParametersAtomically
- service|server|/asr_orchestrator_node|/asr_orchestrator_node/set_parameters|rcl_interfaces/srv/SetParameters
- service|server|/asr_orchestrator_node|/config/list_profiles|asr_interfaces/srv/ListProfiles
- service|server|/asr_orchestrator_node|/config/validate|asr_interfaces/srv/ValidateConfig
- service|server|/audio_input_node|/asr/runtime/audio/reconfigure|asr_interfaces/srv/ReconfigureRuntime
- service|server|/audio_input_node|/asr/runtime/audio/start_session|asr_interfaces/srv/StartRuntimeSession
- service|server|/audio_input_node|/asr/runtime/audio/stop_session|asr_interfaces/srv/StopRuntimeSession
- service|server|/audio_input_node|/audio_input_node/describe_parameters|rcl_interfaces/srv/DescribeParameters
- service|server|/audio_input_node|/audio_input_node/get_parameter_types|rcl_interfaces/srv/GetParameterTypes
- service|server|/audio_input_node|/audio_input_node/get_parameters|rcl_interfaces/srv/GetParameters
- service|server|/audio_input_node|/audio_input_node/get_type_description|type_description_interfaces/srv/GetTypeDescription
- service|server|/audio_input_node|/audio_input_node/list_parameters|rcl_interfaces/srv/ListParameters
- service|server|/audio_input_node|/audio_input_node/set_parameters_atomically|rcl_interfaces/srv/SetParametersAtomically
- service|server|/audio_input_node|/audio_input_node/set_parameters|rcl_interfaces/srv/SetParameters
- service|server|/audio_preprocess_node|/asr/runtime/preprocess/reconfigure|asr_interfaces/srv/ReconfigureRuntime
- service|server|/audio_preprocess_node|/audio_preprocess_node/describe_parameters|rcl_interfaces/srv/DescribeParameters
- service|server|/audio_preprocess_node|/audio_preprocess_node/get_parameter_types|rcl_interfaces/srv/GetParameterTypes
- service|server|/audio_preprocess_node|/audio_preprocess_node/get_parameters|rcl_interfaces/srv/GetParameters
- service|server|/audio_preprocess_node|/audio_preprocess_node/get_type_description|type_description_interfaces/srv/GetTypeDescription
- service|server|/audio_preprocess_node|/audio_preprocess_node/list_parameters|rcl_interfaces/srv/ListParameters
- service|server|/audio_preprocess_node|/audio_preprocess_node/set_parameters_atomically|rcl_interfaces/srv/SetParametersAtomically
- service|server|/audio_preprocess_node|/audio_preprocess_node/set_parameters|rcl_interfaces/srv/SetParameters
- service|server|/benchmark_manager_node|/benchmark/get_status|asr_interfaces/srv/GetBenchmarkStatus
- service|server|/benchmark_manager_node|/benchmark_manager_node/describe_parameters|rcl_interfaces/srv/DescribeParameters
- service|server|/benchmark_manager_node|/benchmark_manager_node/get_parameter_types|rcl_interfaces/srv/GetParameterTypes
- service|server|/benchmark_manager_node|/benchmark_manager_node/get_parameters|rcl_interfaces/srv/GetParameters
- service|server|/benchmark_manager_node|/benchmark_manager_node/get_type_description|type_description_interfaces/srv/GetTypeDescription
- service|server|/benchmark_manager_node|/benchmark_manager_node/list_parameters|rcl_interfaces/srv/ListParameters
- service|server|/benchmark_manager_node|/benchmark_manager_node/set_parameters_atomically|rcl_interfaces/srv/SetParametersAtomically
- service|server|/benchmark_manager_node|/benchmark_manager_node/set_parameters|rcl_interfaces/srv/SetParameters
- service|server|/benchmark_manager_node|/datasets/list|asr_interfaces/srv/ListDatasets
- service|server|/benchmark_manager_node|/datasets/register|asr_interfaces/srv/RegisterDataset
- service|server|/vad_segmenter_node|/asr/runtime/vad/reconfigure|asr_interfaces/srv/ReconfigureRuntime
- service|server|/vad_segmenter_node|/vad_segmenter_node/describe_parameters|rcl_interfaces/srv/DescribeParameters
- service|server|/vad_segmenter_node|/vad_segmenter_node/get_parameter_types|rcl_interfaces/srv/GetParameterTypes
- service|server|/vad_segmenter_node|/vad_segmenter_node/get_parameters|rcl_interfaces/srv/GetParameters
- service|server|/vad_segmenter_node|/vad_segmenter_node/get_type_description|type_description_interfaces/srv/GetTypeDescription
- service|server|/vad_segmenter_node|/vad_segmenter_node/list_parameters|rcl_interfaces/srv/ListParameters
- service|server|/vad_segmenter_node|/vad_segmenter_node/set_parameters_atomically|rcl_interfaces/srv/SetParametersAtomically
- service|server|/vad_segmenter_node|/vad_segmenter_node/set_parameters|rcl_interfaces/srv/SetParameters
- topic|pub|/asr_gateway_client_bridge|/parameter_events|rcl_interfaces/msg/ParameterEvent
- topic|pub|/asr_gateway_client_bridge|/rosout|rcl_interfaces/msg/Log
- topic|pub|/asr_gateway_runtime_observer|/parameter_events|rcl_interfaces/msg/ParameterEvent
- topic|pub|/asr_gateway_runtime_observer|/rosout|rcl_interfaces/msg/Log
- topic|pub|/asr_orchestrator_node|/asr/runtime/results/final|asr_interfaces/msg/AsrResult
- topic|pub|/asr_orchestrator_node|/asr/runtime/results/partial|asr_interfaces/msg/AsrResultPartial
- topic|pub|/asr_orchestrator_node|/asr/status/nodes|asr_interfaces/msg/NodeStatus
- topic|pub|/asr_orchestrator_node|/asr/status/sessions|asr_interfaces/msg/SessionStatus
- topic|pub|/asr_orchestrator_node|/parameter_events|rcl_interfaces/msg/ParameterEvent
- topic|pub|/asr_orchestrator_node|/rosout|rcl_interfaces/msg/Log
- topic|pub|/audio_input_node|/asr/runtime/audio/raw|asr_interfaces/msg/AudioChunk
- topic|pub|/audio_input_node|/asr/status/nodes|asr_interfaces/msg/NodeStatus
- topic|pub|/audio_input_node|/parameter_events|rcl_interfaces/msg/ParameterEvent
- topic|pub|/audio_input_node|/rosout|rcl_interfaces/msg/Log
- topic|pub|/audio_preprocess_node|/asr/runtime/audio/preprocessed|asr_interfaces/msg/AudioChunk
- topic|pub|/audio_preprocess_node|/asr/status/nodes|asr_interfaces/msg/NodeStatus
- topic|pub|/audio_preprocess_node|/parameter_events|rcl_interfaces/msg/ParameterEvent
- topic|pub|/audio_preprocess_node|/rosout|rcl_interfaces/msg/Log
- topic|pub|/benchmark_manager_node|/parameter_events|rcl_interfaces/msg/ParameterEvent
- topic|pub|/benchmark_manager_node|/rosout|rcl_interfaces/msg/Log
- topic|pub|/vad_segmenter_node|/asr/runtime/audio/segments|asr_interfaces/msg/AudioSegment
- topic|pub|/vad_segmenter_node|/asr/runtime/vad/activity|asr_interfaces/msg/SpeechActivity
- topic|pub|/vad_segmenter_node|/asr/status/nodes|asr_interfaces/msg/NodeStatus
- topic|pub|/vad_segmenter_node|/parameter_events|rcl_interfaces/msg/ParameterEvent
- topic|pub|/vad_segmenter_node|/rosout|rcl_interfaces/msg/Log
- topic|sub|/asr_gateway_runtime_observer|/asr/runtime/results/final|asr_interfaces/msg/AsrResult
- topic|sub|/asr_gateway_runtime_observer|/asr/runtime/results/partial|asr_interfaces/msg/AsrResultPartial
- topic|sub|/asr_gateway_runtime_observer|/asr/status/nodes|asr_interfaces/msg/NodeStatus
- topic|sub|/asr_gateway_runtime_observer|/asr/status/sessions|asr_interfaces/msg/SessionStatus
- topic|sub|/asr_orchestrator_node|/asr/runtime/audio/preprocessed|asr_interfaces/msg/AudioChunk
- topic|sub|/asr_orchestrator_node|/asr/runtime/audio/segments|asr_interfaces/msg/AudioSegment
- topic|sub|/audio_preprocess_node|/asr/runtime/audio/raw|asr_interfaces/msg/AudioChunk
- topic|sub|/vad_segmenter_node|/asr/runtime/audio/preprocessed|asr_interfaces/msg/AudioChunk

### Removed edges
- service|server|/asr_orchestrator_node|/asr/runtime/get_status|GetAsrStatus
- service|server|/asr_orchestrator_node|/asr/runtime/list_backends|ListBackends
- service|server|/asr_orchestrator_node|/asr/runtime/recognize_once|RecognizeOnce
- service|server|/asr_orchestrator_node|/asr/runtime/reconfigure|ReconfigureRuntime
- service|server|/asr_orchestrator_node|/asr/runtime/start_session|StartRuntimeSession
- service|server|/asr_orchestrator_node|/asr/runtime/stop_session|StopRuntimeSession
- service|server|/asr_orchestrator_node|/config/list_profiles|ListProfiles
- service|server|/asr_orchestrator_node|/config/validate|ValidateConfig
- service|server|/audio_input_node|/asr/runtime/audio/reconfigure|ReconfigureRuntime
- service|server|/audio_input_node|/asr/runtime/audio/start_session|StartRuntimeSession
- service|server|/audio_input_node|/asr/runtime/audio/stop_session|StopRuntimeSession
- service|server|/audio_preprocess_node|/asr/runtime/preprocess/reconfigure|ReconfigureRuntime
- service|server|/benchmark_manager_node|/benchmark/get_status|GetBenchmarkStatus
- service|server|/benchmark_manager_node|/datasets/list|ListDatasets
- service|server|/benchmark_manager_node|/datasets/register|RegisterDataset
- service|server|/vad_segmenter_node|/asr/runtime/vad/reconfigure|ReconfigureRuntime

## Runtime Errors
- Count: 0
- See [runtime_errors.md](runtime_errors.md)
