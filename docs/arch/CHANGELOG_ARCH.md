# Architecture Changelog

## Added

### Nodes
- /asr_text_output_node

### Topics
- /asr/text/plain
- None

### Services
- /asr_text_output_node/describe_parameters
- /asr_text_output_node/get_parameter_types
- /asr_text_output_node/get_parameters
- /asr_text_output_node/get_type_description
- /asr_text_output_node/list_parameters
- /asr_text_output_node/set_parameters
- /asr_text_output_node/set_parameters_atomically

## Removed

### Nodes
- None

### Topics
- None

### Services
- None

## Changed Types
- None

## Connectivity

### Added edges
- service|server|/asr_text_output_node|/asr_text_output_node/describe_parameters|rcl_interfaces/srv/DescribeParameters
- service|server|/asr_text_output_node|/asr_text_output_node/get_parameter_types|rcl_interfaces/srv/GetParameterTypes
- service|server|/asr_text_output_node|/asr_text_output_node/get_parameters|rcl_interfaces/srv/GetParameters
- service|server|/asr_text_output_node|/asr_text_output_node/get_type_description|type_description_interfaces/srv/GetTypeDescription
- service|server|/asr_text_output_node|/asr_text_output_node/list_parameters|rcl_interfaces/srv/ListParameters
- service|server|/asr_text_output_node|/asr_text_output_node/set_parameters_atomically|rcl_interfaces/srv/SetParametersAtomically
- service|server|/asr_text_output_node|/asr_text_output_node/set_parameters|rcl_interfaces/srv/SetParameters
- topic|pub|/asr_text_output_node|/asr/text/plain|std_msgs/msg/String
- topic|pub|/asr_text_output_node|/parameter_events|rcl_interfaces/msg/ParameterEvent
- topic|pub|/asr_text_output_node|/rosout|rcl_interfaces/msg/Log
- topic|pub|/asr_text_output_node|unknown::topic::pub|String
- topic|sub|/asr_text_output_node|/asr/text|asr_interfaces/msg/AsrResult
- topic|sub|/asr_text_output_node|unknown::topic::sub|AsrResult

### Removed edges
- None

## Runtime Errors
- Count: 0
- See [runtime_errors.md](runtime_errors.md)
