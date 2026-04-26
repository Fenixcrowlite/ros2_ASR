# Capabilities Matrix

| Backend | recognize_once | streaming | timestamps | confidence | cloud |
|---|---|---|---|---|---|
| mock | yes | native | yes | yes | no |
| vosk | yes | native | yes | yes | no |
| whisper | yes | none | yes | yes | no |
| google | yes | native | yes | yes | yes |
| aws | yes | native | yes | yes | yes |
| azure | yes | native | yes | yes | yes |

## Как это используется

- `GetAsrStatus` отдаёт capability flags: [[02_ROS2/Service_Get_Status]]
- fallback logic внутри [[03_Core/Backend_Interface]]
