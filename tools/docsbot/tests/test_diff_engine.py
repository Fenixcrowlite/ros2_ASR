from docsbot.indexer.models import Endpoint, NodeInfo, ProjectIndex, RepoMeta
from docsbot.planner.diff_engine import compute_diff


def _index_with_topic(topic: str) -> ProjectIndex:
    node = NodeInfo(
        node_id="asr_ros:AsrServerNode",
        package="asr_ros",
        file="/tmp/asr_server_node.py",
        class_name="AsrServerNode",
        publishers=[
            Endpoint(name=topic, type_name="asr_interfaces/msg/AsrResult", direction="pub")
        ],
    )
    return ProjectIndex(
        repo=RepoMeta(
            repo_name="ros2ws",
            repo_root="/repo",
            workspace_root="/repo/ros2_ws",
            commit="deadbeef",
        ),
        nodes=[node],
    )


def test_diff_detects_added_topic() -> None:
    old = _index_with_topic("/asr/text")
    new = _index_with_topic("/asr/live_text")
    diff = compute_diff(old, new)

    assert "/asr/live_text" in diff.topics.added
    assert "/asr/text" in diff.topics.removed


def test_diff_bootstrap_mode() -> None:
    new = _index_with_topic("/asr/text")
    diff = compute_diff(None, new)

    assert "/asr/text" in diff.topics.added
    assert diff.nodes.added == ["asr_ros:AsrServerNode"]
