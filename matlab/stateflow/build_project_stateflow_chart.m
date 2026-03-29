function modelName = build_project_stateflow_chart(varargin)
%BUILD_PROJECT_STATEFLOW_CHART Build a full-project hierarchical Stateflow chart.
%   MODELNAME = BUILD_PROJECT_STATEFLOW_CHART() creates/overwrites a Simulink
%   model and fills one Stateflow chart with architecture details collected from:
%   - docs/arch/merged_graph.json
%   - repository folder structure (ros2_ws, web_ui, scripts, tools, etc.)
%
%   Name-value options:
%     'RepoRoot'              - repository root path
%     'GraphJson'             - path to merged architecture graph JSON
%     'ModelName'             - Simulink model name (default: 'asr_project_stateflow')
%     'MaxStatesPerContainer' - max generated substates per container (default: 80)
%     'OpenModel'             - open model after generation (default: true)
%     'RefreshArchviz'        - run ./archviz all before reading JSON (default: false)
%
%   Example:
%     build_project_stateflow_chart('RefreshArchviz', true, ...
%         'ModelName', 'asr_project_full_stateflow');

opts = parseOptions(varargin{:});
ensureStateflowAvailable();

if opts.RefreshArchviz
    refreshArchvizGraph(opts.RepoRoot);
end

graph = readMergedGraph(opts.GraphJson);
chart = createChartModel(opts.ModelName);

addChartAnnotation(chart, sprintf([ ...
    'Auto-generated from %s\\n', ...
    'Repo root: %s\\n', ...
    'Generated: %s'], ...
    opts.GraphJson, opts.RepoRoot, datestr(now, 'yyyy-mm-dd HH:MM:SS')));

[topStates, flowStates] = createTopStates(chart);

populateRosWorkspace(topStates.ROS2_Workspace, graph, opts);
populateWebUi(topStates.Web_UI, opts);
populateScripts(topStates.Scripts_CLI, opts);
populateTools(topStates.Tools_Archviz_Docsbot, opts);
populateInterfaces(topStates.Interfaces_and_Contracts, graph);
populateRuntimeFlow(topStates.Runtime_Flow, flowStates);
populateProjectAssets(topStates.Project_Assets, opts);
populateErrors(topStates.Errors_and_Recovery, opts);

wireTopTransitions(chart, topStates);

save_system(opts.ModelName);
if opts.OpenModel
    open_system(opts.ModelName);
else
    close_system(opts.ModelName);
end

modelName = opts.ModelName;
end

function opts = parseOptions(varargin)
thisFile = mfilename('fullpath');
repoRootDefault = fileparts(fileparts(fileparts(thisFile)));

defaultGraph = fullfile(repoRootDefault, 'docs', 'arch', 'merged_graph.json');

parser = inputParser;
parser.FunctionName = mfilename;
addParameter(parser, 'RepoRoot', repoRootDefault, @isTextScalar);
addParameter(parser, 'GraphJson', defaultGraph, @isTextScalar);
addParameter(parser, 'ModelName', 'asr_project_stateflow', @isTextScalar);
addParameter(parser, 'MaxStatesPerContainer', 80, @(x) isnumeric(x) && isscalar(x) && x > 0);
addParameter(parser, 'OpenModel', true, @(x) islogical(x) || isnumeric(x));
addParameter(parser, 'RefreshArchviz', false, @(x) islogical(x) || isnumeric(x));
parse(parser, varargin{:});

opts = parser.Results;
opts.RepoRoot = char(string(opts.RepoRoot));
opts.GraphJson = char(string(opts.GraphJson));
opts.ModelName = char(string(opts.ModelName));
opts.OpenModel = logical(opts.OpenModel);
opts.RefreshArchviz = logical(opts.RefreshArchviz);
opts.MaxStatesPerContainer = double(opts.MaxStatesPerContainer);
end

function tf = isTextScalar(value)
tf = ischar(value) || (isstring(value) && isscalar(value));
end

function ensureStateflowAvailable()
if isempty(ver('simulink'))
    error('Simulink toolbox is required.');
end
if isempty(ver('stateflow'))
    error('Stateflow toolbox is required.');
end
end

function refreshArchvizGraph(repoRoot)
cmd = sprintf('cd "%s" && ./archviz all --ws ros2_ws --out docs/arch --profile full --timeout-sec 20', repoRoot);
[status, output] = system(cmd);
if status ~= 0
    error('archviz refresh failed:\n%s', output);
end
end

function graph = readMergedGraph(graphPath)
if ~exist(graphPath, 'file')
    error('Merged graph file not found: %s', graphPath);
end
raw = fileread(graphPath);
graph = jsondecode(raw);
end

function chart = createChartModel(modelName)
if bdIsLoaded(modelName)
    close_system(modelName, 0);
end
if exist([modelName '.slx'], 'file') == 2
    delete([modelName '.slx']);
end

new_system(modelName);
open_system(modelName);

chartBlockPath = [modelName '/ASR_Project_Chart'];
add_block('sflib/Chart', chartBlockPath, 'Position', [80 80 360 260]);

rt = sfroot;
machines = rt.find('-isa', 'Stateflow.Machine', 'Name', modelName);
if isempty(machines)
    error('Unable to find Stateflow machine for model %s', modelName);
end
machine = machines(1);
charts = machine.find('-isa', 'Stateflow.Chart');
if isempty(charts)
    error('Unable to find Stateflow chart in model %s', modelName);
end
chart = charts(1);
chart.Name = 'ASR_Project_Chart';
end

function addChartAnnotation(chart, text)
annotation = Stateflow.Annotation(chart);
annotation.Position = [30 30 980 55];
annotation.Text = text;
end

function [top, flowStates] = createTopStates(chart)
stateDefs = {
    'Init', ...
    'ROS2_Workspace', ...
    'Web_UI', ...
    'Scripts_CLI', ...
    'Tools_Archviz_Docsbot', ...
    'Interfaces_and_Contracts', ...
    'Runtime_Flow', ...
    'Project_Assets', ...
    'Errors_and_Recovery', ...
    'Shutdown'
};

pos = layoutGrid(numel(stateDefs), 30, 110, 5, 225, 155, 25, 25);
for i = 1:numel(stateDefs)
    label = sprintf('entry: activate_%s;', lower(stateDefs{i}));
    st = addStateSafe(chart, stateDefs{i}, {label}, pos(i, :));
    top.(matlab.lang.makeValidName(stateDefs{i})) = st;
end

flowStates = createRuntimeFlowSkeleton(top.Runtime_Flow);

addTransitionSafe(chart, top.Init, top.ROS2_Workspace, 'env_ok');
addTransitionSafe(chart, top.Init, top.Web_UI, 'ui_mode');
addTransitionSafe(chart, top.Web_UI, top.Runtime_Flow, 'job_started');
addTransitionSafe(chart, top.ROS2_Workspace, top.Runtime_Flow, 'nodes_ready');
addTransitionSafe(chart, top.Runtime_Flow, top.Interfaces_and_Contracts, 'contracts_active');
addTransitionSafe(chart, top.Interfaces_and_Contracts, top.Project_Assets, 'artifacts_written');
addTransitionSafe(chart, top.Project_Assets, top.Shutdown, 'stop_requested');

addTransitionSafe(chart, top.Runtime_Flow, top.Errors_and_Recovery, 'exception');
addTransitionSafe(chart, top.Errors_and_Recovery, top.Runtime_Flow, 'recovered');
end

function flow = createRuntimeFlowSkeleton(runtimeState)
steps = {
    'Config_Load', 'Load YAML config + overlays + profile overrides';
    'Launch_Bringup', 'ros2 launch asr_ros bringup.launch.py ...';
    'Capture_Audio', 'audio_capture_node publishes /asr/audio_chunks';
    'Select_Backend', 'asr_server_node -> asr_core.factory.create_backend';
    'Recognize_Stream_or_Once', 'core/service/action runtime recognition path';
    'Publish_Text_Metrics', '/asr/text, /asr/metrics, /asr/text/plain';
    'Persist_Artifacts', 'results/, runtime_configs/, logs/, reports';
    'Idle', 'polling + waiting for next request';
};

pos = layoutGrid(size(steps, 1), 15, 20, 2, 180, 62, 15, 12);
for i = 1:size(steps, 1)
    st = addStateSafe(runtimeState, steps{i, 1}, {steps{i, 2}}, pos(i, :));
    flow.(matlab.lang.makeValidName(steps{i, 1})) = st;
end

fields = fieldnames(flow);
for i = 1:(numel(fields) - 1)
    addTransitionSafe(runtimeState, flow.(fields{i}), flow.(fields{i + 1}), 'ok');
end
addTransitionSafe(runtimeState, flow.Idle, flow.Capture_Audio, 'new_audio');
end

function populateRosWorkspace(parentState, graph, opts)
packages = getStructArray(graph, 'packages');
if isempty(packages)
    addStateSafe(parentState, 'No_Packages', {'No package data in merged_graph.json'}, [20 35 220 80]);
    return;
end

pos = layoutGrid(numel(packages), 15, 20, 3, 170, 95, 12, 12);
for i = 1:numel(packages)
    pkg = packages(i);
    pkgName = fieldAsText(pkg, 'name', sprintf('package_%d', i));
    pkgPath = fieldAsText(pkg, 'path', '');
    deps = summarizeList(toCellStr(fieldValue(pkg, 'dependencies', {})), 4);
    lines = {
        sprintf('path: %s', tailPath(pkgPath, 5));
        sprintf('deps: %s', deps)
    };

    pkgState = addStateSafe(parentState, pkgName, lines, pos(i, :));
    populateSinglePackage(pkgState, pkg, graph, opts);
end
end

function populateSinglePackage(pkgState, pkg, graph, opts)
pkgName = fieldAsText(pkg, 'name', 'pkg');
pkgPath = fieldAsText(pkg, 'path', '');

childPos = layoutGrid(5, 12, 20, 3, 138, 66, 10, 8);
metaState = addStateSafe(pkgState, 'Metadata', packageMetadataLines(pkg), childPos(1, :));
launchState = addStateSafe(pkgState, 'Launches', {'launch files + args + spawned nodes'}, childPos(2, :));
nodeState = addStateSafe(pkgState, 'Nodes', {'node params + pubs/subs/srv/actions/timers'}, childPos(3, :));
ifaceState = addStateSafe(pkgState, 'Interfaces', {'msg/srv/action contracts'}, childPos(4, :));
fileState = addStateSafe(pkgState, 'Source_Files', {'python + interfaces + launch files'}, childPos(5, :));

populateLaunches(launchState, pkgName, graph, opts);
populateNodes(nodeState, pkgName, graph, opts);
populatePackageInterfaces(ifaceState, pkg);
populateFiles(fileState, pkgPath, opts.MaxStatesPerContainer, {'.py', '.msg', '.srv', '.action', '.xml', '.cfg', '.launch.py'});

addTransitionSafe(pkgState, metaState, launchState, 'package_loaded');
addTransitionSafe(pkgState, launchState, nodeState, 'launch_started');
addTransitionSafe(pkgState, nodeState, ifaceState, 'contracts_bound');
addTransitionSafe(pkgState, ifaceState, fileState, 'trace_to_source');
end

function lines = packageMetadataLines(pkg)
deps = toCellStr(fieldValue(pkg, 'dependencies', {}));
entryPoints = toCellStr(fieldValue(pkg, 'entry_points', {}));
launchFiles = toCellStr(fieldValue(pkg, 'launch_files', {}));

lines = {
    sprintf('deps_count: %d', numel(deps));
    sprintf('entry_points: %s', summarizeList(entryPoints, 3));
    sprintf('launch_files: %s', summarizeList(launchFiles, 3))
};
end

function populateLaunches(parentState, pkgName, graph, opts)
launches = getStructArray(graph, 'launches');
selected = struct([]);
for i = 1:numel(launches)
    if strcmp(fieldAsText(launches(i), 'package', ''), pkgName)
        selected = appendStruct(selected, launches(i));
    end
end

if isempty(selected)
    addStateSafe(parentState, 'No_Launches', {'No launch records for this package'}, [10 12 120 45]);
    return;
end

selected = truncateStructArray(selected, opts.MaxStatesPerContainer);
pos = layoutGrid(numel(selected), 10, 12, 2, 122, 48, 8, 6);
for i = 1:numel(selected)
    item = selected(i);
    args = toCellStr(fieldValue(item, 'declared_args', {}));
    nodes = getStructArray(item, 'nodes');
    nodeNames = {};
    for j = 1:numel(nodes)
        nodeNames{end + 1} = fieldAsText(nodes(j), 'name', sprintf('node_%d', j)); %#ok<AGROW>
    end

    lines = {
        sprintf('file: %s', fieldAsText(item, 'file', 'unknown'));
        sprintf('args: %s', summarizeList(args, 4));
        sprintf('nodes: %s', summarizeList(nodeNames, 4))
    };
    addStateSafe(parentState, sprintf('launch_%d', i), lines, pos(i, :));
end
end

function populateNodes(parentState, pkgName, graph, opts)
nodes = getStructArray(graph, 'nodes');
selected = struct([]);
for i = 1:numel(nodes)
    if strcmp(fieldAsText(nodes(i), 'package', ''), pkgName)
        selected = appendStruct(selected, nodes(i));
    end
end

if isempty(selected)
    addStateSafe(parentState, 'No_Nodes', {'No node records for this package'}, [10 12 120 45]);
    return;
end

selected = truncateStructArray(selected, opts.MaxStatesPerContainer);
pos = layoutGrid(numel(selected), 10, 12, 2, 122, 58, 8, 6);
for i = 1:numel(selected)
    node = selected(i);
    nodeName = fieldAsText(node, 'name', sprintf('node_%d', i));
    nodeId = fieldAsText(node, 'id', ['/' nodeName]);
    params = toCellStr(fieldValue(node, 'parameters', {}));

    lines = {
        sprintf('exec: %s', fieldAsText(node, 'executable', 'unknown'));
        sprintf('params: %s', summarizeList(params, 4));
        sprintf('state: %s', fieldAsText(node, 'state', 'unknown'))
    };

    nodeState = addStateSafe(parentState, nodeName, lines, pos(i, :));
    populateNodeEdges(nodeState, nodeId, graph, opts.MaxStatesPerContainer);
end
end

function populateNodeEdges(nodeState, nodeId, graph, maxStates)
edges = getStructArray(graph, 'edges');
selected = struct([]);
for i = 1:numel(edges)
    if strcmp(fieldAsText(edges(i), 'node', ''), nodeId)
        selected = appendStruct(selected, edges(i));
    end
end

if isempty(selected)
    addStateSafe(nodeState, 'No_Edges', {'No edges for node'}, [8 8 100 35]);
    return;
end

selected = truncateStructArray(selected, maxStates);
pos = layoutGrid(numel(selected), 8, 8, 2, 98, 35, 6, 4);
for i = 1:numel(selected)
    edge = selected(i);
    lines = {
        sprintf('%s %s', upper(fieldAsText(edge, 'direction', '?')), fieldAsText(edge, 'kind', '?'));
        sprintf('name: %s', fieldAsText(edge, 'name', '?'));
        sprintf('type: %s', fieldAsText(edge, 'type', '?'))
    };
    addStateSafe(nodeState, sprintf('edge_%d', i), lines, pos(i, :));
end
end

function populatePackageInterfaces(parentState, pkg)
ifaces = getStructArray(pkg, 'interfaces');
if isempty(ifaces)
    addStateSafe(parentState, 'No_Interfaces', {'No interface declarations'}, [10 12 120 45]);
    return;
end

pos = layoutGrid(numel(ifaces), 10, 12, 2, 122, 50, 8, 6);
for i = 1:numel(ifaces)
    iface = ifaces(i);
    kind = fieldAsText(iface, 'kind', 'iface');
    name = fieldAsText(iface, 'name', sprintf('iface_%d', i));

    detailFields = {'fields', 'request_fields', 'response_fields', 'goal_fields', 'result_fields', 'feedback_fields'};
    detail = {};
    for d = 1:numel(detailFields)
        value = toCellStr(fieldValue(iface, detailFields{d}, {}));
        if ~isempty(value)
            detail{end + 1} = sprintf('%s: %s', detailFields{d}, summarizeList(value, 2)); %#ok<AGROW>
        end
    end
    if isempty(detail)
        detail = {'fields: -'};
    end

    lines = [{sprintf('kind: %s', kind)} detail];
    addStateSafe(parentState, sprintf('%s_%s', kind, name), lines, pos(i, :));
end
end

function populateWebUi(parentState, opts)
repoRoot = opts.RepoRoot;
backendPath = fullfile(repoRoot, 'ros2_ws', 'src', 'asr_gateway', 'asr_gateway');
frontendPath = fullfile(repoRoot, 'web_ui', 'frontend');
mainPyPath = fullfile(backendPath, 'api.py');

childPos = layoutGrid(4, 10, 16, 2, 170, 80, 10, 10);
backendState = addStateSafe(parentState, 'Gateway_API', {'FastAPI gateway over ROS/runtime/benchmark/storage'}, childPos(1, :));
frontendState = addStateSafe(parentState, 'Frontend_Web_UI', {'index.html + js/ + styles.css'}, childPos(2, :));
routesState = addStateSafe(parentState, 'API_Routes', {'auto-extracted from @app.<method>(...)'}, childPos(3, :));
runtimeState = addStateSafe(parentState, 'Runtime_Files', {'configs + uploads + logs + artifacts'}, childPos(4, :));

populateFiles(backendState, backendPath, opts.MaxStatesPerContainer, {'.py'});
populateFiles(frontendState, frontendPath, opts.MaxStatesPerContainer, {'.js', '.html', '.css'});
populateFastApiRoutes(routesState, mainPyPath, opts.MaxStatesPerContainer);

runtimeRoots = {
    fullfile(repoRoot, 'configs'), ...
    fullfile(repoRoot, 'data', 'sample', 'uploads'), ...
    fullfile(repoRoot, 'logs'), ...
    fullfile(repoRoot, 'artifacts')
};
populateMultiRootSummary(runtimeState, runtimeRoots, {'*.yaml', '*.log', '*.txt', '*.wav', '*.csv', '*.json'});

addTransitionSafe(parentState, backendState, routesState, 'route_dispatch');
addTransitionSafe(parentState, frontendState, routesState, 'fetch_api');
addTransitionSafe(parentState, routesState, runtimeState, 'write_artifacts');
end

function populateFastApiRoutes(parentState, mainPyPath, maxStates)
if ~exist(mainPyPath, 'file')
    addStateSafe(parentState, 'Routes_Not_Found', {'asr_gateway/api.py not found'}, [10 12 120 45]);
    return;
end

content = fileread(mainPyPath);
pattern = '@app\.(get|post|put|delete|patch)\("([^"]+)"\)';
matches = regexp(content, pattern, 'tokens');
if isempty(matches)
    addStateSafe(parentState, 'No_Routes', {'No route decorators found'}, [10 12 120 45]);
    return;
end

if numel(matches) > maxStates
    matches = matches(1:maxStates);
end

pos = layoutGrid(numel(matches), 10, 12, 2, 122, 45, 8, 6);
for i = 1:numel(matches)
    token = matches{i};
    method = upper(token{1});
    path = token{2};
    lines = {
        sprintf('method: %s', method), ...
        sprintf('path: %s', path)
    };
    addStateSafe(parentState, sprintf('route_%d', i), lines, pos(i, :));
end
end

function populateScripts(parentState, opts)
scriptsPath = fullfile(opts.RepoRoot, 'scripts');
childPos = layoutGrid(2, 10, 18, 2, 170, 82, 10, 10);
cliState = addStateSafe(parentState, 'Operational_Scripts', {'run_demo / run_benchmarks / live_sample_eval / release'}, childPos(1, :));
utilState = addStateSafe(parentState, 'Utility_Scripts', {'setup_env / secret_scan / make_dist / reporting'}, childPos(2, :));

populateFiles(cliState, scriptsPath, opts.MaxStatesPerContainer, {'.py', '.sh'});
populateFiles(utilState, scriptsPath, opts.MaxStatesPerContainer, {'.py', '.sh'});

addTransitionSafe(parentState, cliState, utilState, 'postprocess');
end

function populateTools(parentState, opts)
toolsPath = fullfile(opts.RepoRoot, 'tools');
archvizPath = fullfile(toolsPath, 'archviz');
docsbotPath = fullfile(toolsPath, 'docsbot');

childPos = layoutGrid(3, 10, 16, 2, 170, 80, 10, 10);
archvizState = addStateSafe(parentState, 'Archviz_Pipeline', {'static/runtime extract + merge + render + diff'}, childPos(1, :));
docsbotState = addStateSafe(parentState, 'Docsbot_Pipeline', {'index + plan + write + QA'}, childPos(2, :));
toolingState = addStateSafe(parentState, 'Support_Tooling', {'root launchers and helpers'}, childPos(3, :));

populateFiles(archvizState, archvizPath, opts.MaxStatesPerContainer, {'.py', '.yaml'});
populateFiles(docsbotState, docsbotPath, opts.MaxStatesPerContainer, {'.py', '.md', '.toml', '.service', '.sh'});
populateFiles(toolingState, toolsPath, opts.MaxStatesPerContainer, {'.py', '.md', '.toml'});

addTransitionSafe(parentState, archvizState, docsbotState, 'docs_sync');
addTransitionSafe(parentState, docsbotState, toolingState, 'qa_done');
end

function populateInterfaces(parentState, graph)
childPos = layoutGrid(3, 10, 16, 3, 145, 118, 8, 10);
topicsState = addStateSafe(parentState, 'Topics', {'publisher/subscriber contracts'}, childPos(1, :));
servicesState = addStateSafe(parentState, 'Services', {'client/server contracts'}, childPos(2, :));
actionsState = addStateSafe(parentState, 'Actions', {'action client/server contracts'}, childPos(3, :));

populateInterfaceStates(topicsState, getStructArray(graph, 'topics'), getStructArray(graph, 'edges'), 'topic', {'pub', 'sub'});
populateInterfaceStates(servicesState, getStructArray(graph, 'services'), getStructArray(graph, 'edges'), 'service', {'server', 'client'});
populateInterfaceStates(actionsState, getStructArray(graph, 'actions'), getStructArray(graph, 'edges'), 'action', {'server', 'client'});

addTransitionSafe(parentState, topicsState, servicesState, 'sync');
addTransitionSafe(parentState, servicesState, actionsState, 'sync');
end

function populateInterfaceStates(parentState, interfaces, edges, kind, directions)
if isempty(interfaces)
    addStateSafe(parentState, 'No_Data', {'No records in merged graph'}, [8 8 118 50]);
    return;
end

maxCount = min(numel(interfaces), 40);
interfaces = interfaces(1:maxCount);
pos = layoutGrid(numel(interfaces), 8, 8, 2, 118, 50, 6, 4);
for i = 1:numel(interfaces)
    item = interfaces(i);
    name = fieldAsText(item, 'name', sprintf('%s_%d', kind, i));
    type = fieldAsText(item, 'type', 'unknown');

    related = filterEdgesByKindName(edges, kind, name);
    srcNodes = uniqueNodesByDirection(related, directions{1});
    dstNodes = uniqueNodesByDirection(related, directions{2});

    lines = {
        sprintf('type: %s', type), ...
        sprintf('%s: %s', directions{1}, summarizeList(srcNodes, 2)), ...
        sprintf('%s: %s', directions{2}, summarizeList(dstNodes, 2))
    };

    addStateSafe(parentState, sprintf('%s_%d', kind, i), lines, pos(i, :));
end
end

function populateRuntimeFlow(parentState, flow)
if isfield(flow, 'Capture_Audio') && isfield(flow, 'Recognize_Stream_or_Once')
    addTransitionSafe(parentState, flow.Capture_Audio, flow.Recognize_Stream_or_Once, 'audio_chunk_ready');
end
if isfield(flow, 'Recognize_Stream_or_Once') && isfield(flow, 'Publish_Text_Metrics')
    addTransitionSafe(parentState, flow.Recognize_Stream_or_Once, flow.Publish_Text_Metrics, 'result_ready');
end
if isfield(flow, 'Publish_Text_Metrics') && isfield(flow, 'Persist_Artifacts')
    addTransitionSafe(parentState, flow.Publish_Text_Metrics, flow.Persist_Artifacts, 'record_metrics');
end
end

function populateProjectAssets(parentState, opts)
repoRoot = opts.RepoRoot;
childPos = layoutGrid(4, 10, 16, 2, 170, 80, 10, 10);

cfgState = addStateSafe(parentState, 'Configs', {'base/commercial/live profiles and overrides'}, childPos(1, :));
dataState = addStateSafe(parentState, 'Data', {'sample WAVs + transcript manifests'}, childPos(2, :));
docState = addStateSafe(parentState, 'Docs', {'architecture + wiki + run guides'}, childPos(3, :));
testState = addStateSafe(parentState, 'Tests', {'unit + integration test suites'}, childPos(4, :));

populateFiles(cfgState, fullfile(repoRoot, 'configs'), 40, {'.yaml', '.yml'});
populateFiles(dataState, fullfile(repoRoot, 'data'), 60, {'.wav', '.csv', '.txt'});
populateFiles(docState, fullfile(repoRoot, 'docs'), 80, {'.md', '.mmd', '.json'});
populateFiles(testState, fullfile(repoRoot, 'tests'), 80, {'.py'});

addTransitionSafe(parentState, cfgState, dataState, 'config_select');
addTransitionSafe(parentState, dataState, testState, 'dataset_for_validation');
addTransitionSafe(parentState, testState, docState, 'report_documented');
end

function populateErrors(parentState, opts)
errorDefs = {
    'Invalid_Parameter_Type', 'ROS param type mismatch (e.g. INTEGER vs DOUBLE).', 'Normalize literals in launch/UI; dynamic typing + coercion in nodes.';
    'Missing_Config_File', 'Config/runtime YAML path does not exist.', 'Validate path in API; fallback to defaults.';
    'Mic_Unavailable', 'Microphone capture fails at runtime.', 'Fallback to file mode; notify operator.';
    'Backend_Credentials_Missing', 'Cloud backend selected without credentials.', 'Preflight checks + explicit backend status service.';
    'ROS_Node_Crash', 'Node process exits with non-zero code.', 'Job logs + restart bringup + inspect tracebacks.';
    'Request_Timeout', 'Service/action/live processing timed out.', 'Tune chunk sizes/timeouts; inspect backend latency.'
};

pos = layoutGrid(size(errorDefs, 1), 10, 12, 2, 168, 58, 8, 6);
for i = 1:size(errorDefs, 1)
    lines = {
        sprintf('symptom: %s', errorDefs{i, 2}), ...
        sprintf('recovery: %s', errorDefs{i, 3})
    };
    addStateSafe(parentState, errorDefs{i, 1}, lines, pos(i, :));
end

runtimeErrorsFile = fullfile(opts.RepoRoot, 'docs', 'arch', 'runtime_errors.md');
if exist(runtimeErrorsFile, 'file')
    txt = fileread(runtimeErrorsFile);
    if contains(lower(txt), 'no runtime errors were recorded')
        addStateSafe(parentState, 'Runtime_Extractor_Status', {'docs/arch/runtime_errors.md: no runtime extraction errors'}, [10 180 344 42]);
    end
end
end

function wireTopTransitions(chart, top)
addTransitionSafe(chart, top.Init, top.Shutdown, 'fatal_startup_error');
addTransitionSafe(chart, top.Web_UI, top.Errors_and_Recovery, 'api_exception');
addTransitionSafe(chart, top.ROS2_Workspace, top.Errors_and_Recovery, 'launch_failure');
addTransitionSafe(chart, top.Project_Assets, top.Init, 'reload_profile');
end

function populateFiles(parentState, rootPath, maxStates, allowedExtensions)
if nargin < 4
    allowedExtensions = {'.py'};
end

if isempty(rootPath) || exist(rootPath, 'dir') ~= 7
    addStateSafe(parentState, 'Path_Not_Found', {sprintf('missing: %s', rootPath)}, [8 8 120 45]);
    return;
end

files = listFilesRecursive(rootPath, allowedExtensions);
if isempty(files)
    addStateSafe(parentState, 'No_Files', {'No matching files found'}, [8 8 120 45]);
    return;
end

if numel(files) > maxStates
    shown = files(1:maxStates);
    omittedCount = numel(files) - maxStates;
else
    shown = files;
    omittedCount = 0;
end

pos = layoutGrid(numel(shown), 8, 8, 3, 108, 34, 6, 4);
for i = 1:numel(shown)
    rel = shown{i};
    ext = lower(getFileExtension(rel));
    lines = {
        sprintf('file: %s', rel), ...
        sprintf('ext: %s', ext)
    };
    addStateSafe(parentState, sprintf('file_%d', i), lines, pos(i, :));
end

if omittedCount > 0
    addStateSafe(parentState, 'Files_Truncated', {sprintf('omitted_files: %d', omittedCount)}, [8 210 180 36]);
end
end

function populateMultiRootSummary(parentState, roots, patterns)
lines = {};
for i = 1:numel(roots)
    root = roots{i};
    count = 0;
    if exist(root, 'dir') == 7
        files = dir(fullfile(root, '**', '*'));
        for j = 1:numel(files)
            if files(j).isdir
                continue;
            end
            if matchesAnyPattern(files(j).name, patterns)
                count = count + 1;
            end
        end
    end
    lines{end + 1} = sprintf('%s: %d', tailPath(root, 2), count); %#ok<AGROW>
end

addStateSafe(parentState, 'Runtime_Storage_Summary', lines, [8 8 160 55]);
end

function yes = matchesAnyPattern(fileName, patterns)
yes = false;
for i = 1:numel(patterns)
    if ~isempty(regexp(fileName, globToRegex(patterns{i}), 'once'))
        yes = true;
        return;
    end
end
end

function regex = globToRegex(glob)
regex = regexptranslate('wildcard', glob);
end

function relFiles = listFilesRecursive(rootPath, allowedExtensions)
entries = dir(fullfile(rootPath, '**', '*'));
relFiles = {};
for i = 1:numel(entries)
    item = entries(i);
    if item.isdir
        continue;
    end
    [~, ~, ext] = fileparts(item.name);
    keep = any(strcmpi(ext, allowedExtensions));
    if ~keep && endsWith(item.name, '.launch.py')
        keep = any(strcmpi('.launch.py', allowedExtensions));
    end
    if keep
        absPath = fullfile(item.folder, item.name);
        relFiles{end + 1} = erasePrefix(absPath, [rootPath filesep]); %#ok<AGROW>
    end
end
relFiles = sort(relFiles);
end

function out = erasePrefix(text, prefix)
if startsWith(text, prefix)
    out = text((length(prefix) + 1):end);
else
    out = text;
end
end

function ext = getFileExtension(pathText)
[~, ~, ext] = fileparts(pathText);
if endsWith(pathText, '.launch.py')
    ext = '.launch.py';
end
end

function out = tailPath(pathText, level)
if isempty(pathText)
    out = '-';
    return;
end
parts = split(string(pathText), filesep);
parts = parts(parts ~= "");
if isempty(parts)
    out = '-';
    return;
end
n = min(level, numel(parts));
out = char(strjoin(parts(end - n + 1:end), filesep));
end

function out = summarizeList(list, maxItems)
if nargin < 2
    maxItems = 4;
end
if isempty(list)
    out = '-';
    return;
end
if numel(list) <= maxItems
    out = strjoin(list, ', ');
else
    out = sprintf('%s ... (+%d)', strjoin(list(1:maxItems), ', '), numel(list) - maxItems);
end
end

function out = toCellStr(value)
if isempty(value)
    out = {};
    return;
end
if ischar(value)
    out = {value};
    return;
end
if isstring(value)
    out = cellstr(value(:));
    return;
end
if iscell(value)
    out = {};
    for i = 1:numel(value)
        if ischar(value{i})
            out{end + 1} = value{i}; %#ok<AGROW>
        elseif isstring(value{i})
            out{end + 1} = char(value{i}); %#ok<AGROW>
        elseif isnumeric(value{i}) || islogical(value{i})
            out{end + 1} = char(string(value{i})); %#ok<AGROW>
        elseif isstruct(value{i})
            out{end + 1} = jsonencode(value{i}); %#ok<AGROW>
        else
            out{end + 1} = char(string(value{i})); %#ok<AGROW>
        end
    end
    return;
end
if isnumeric(value) || islogical(value)
    out = {char(string(value))};
    return;
end
if isstruct(value)
    out = {jsonencode(value)};
    return;
end
out = {char(string(value))};
end

function value = fieldValue(s, fieldName, fallback)
if isstruct(s) && isfield(s, fieldName)
    value = s.(fieldName);
else
    value = fallback;
end
end

function txt = fieldAsText(s, fieldName, fallback)
value = fieldValue(s, fieldName, fallback);
if isempty(value)
    txt = fallback;
    return;
end
if ischar(value)
    txt = value;
elseif isstring(value)
    txt = char(value);
elseif isnumeric(value) || islogical(value)
    txt = char(string(value));
else
    txt = char(string(value));
end
end

function arr = getStructArray(s, fieldName)
arr = struct([]);
if ~isstruct(s) || ~isfield(s, fieldName)
    return;
end
value = s.(fieldName);
if isempty(value)
    return;
end
if isstruct(value)
    arr = value;
end
end

function out = appendStruct(in, item)
if isempty(in)
    out = item;
else
    out = [in item]; %#ok<AGROW>
end
end

function out = truncateStructArray(in, maxCount)
if numel(in) > maxCount
    out = in(1:maxCount);
else
    out = in;
end
end

function filtered = filterEdgesByKindName(edges, kind, name)
filtered = struct([]);
for i = 1:numel(edges)
    if strcmp(fieldAsText(edges(i), 'kind', ''), kind) && strcmp(fieldAsText(edges(i), 'name', ''), name)
        filtered = appendStruct(filtered, edges(i));
    end
end
end

function nodes = uniqueNodesByDirection(edges, direction)
nodes = {};
for i = 1:numel(edges)
    if strcmp(fieldAsText(edges(i), 'direction', ''), direction)
        node = fieldAsText(edges(i), 'node', '');
        if ~isempty(node)
            nodes{end + 1} = node; %#ok<AGROW>
        end
    end
end
nodes = unique(nodes);
end

function st = addStateSafe(parent, displayName, detailLines, position)
if nargin < 3
    detailLines = {};
end
if ischar(detailLines) || isstring(detailLines)
    detailLines = {char(string(detailLines))};
end

detailLines = normalizeLines(detailLines);
baseName = matlab.lang.makeValidName(displayName);
if isempty(baseName)
    baseName = 'State';
end
stateName = uniqueStateName(parent, baseName);

st = Stateflow.State(parent);
st.Name = stateName;

if isempty(detailLines)
    st.LabelString = displayName;
else
    st.LabelString = sprintf('%s\n%s', displayName, strjoin(detailLines, newline));
end
st.Position = position;
end

function lines = normalizeLines(lines)
out = {};
for i = 1:numel(lines)
    line = lines{i};
    if isstring(line)
        line = char(line);
    end
    if isnumeric(line) || islogical(line)
        line = char(string(line));
    end
    if isempty(line)
        continue;
    end
    out{end + 1} = line; %#ok<AGROW>
end
lines = out;
end

function name = uniqueStateName(parent, baseName)
name = baseName;
idx = 2;
while true
    found = parent.find('-isa', 'Stateflow.State', 'Name', name);
    if isempty(found)
        return;
    end
    name = sprintf('%s_%d', baseName, idx);
    idx = idx + 1;
end
end

function transition = addTransitionSafe(container, sourceState, destinationState, label)
transition = [];
try
    transition = Stateflow.Transition(container);
    transition.Source = sourceState;
    transition.Destination = destinationState;
    transition.SourceOClock = 3;
    transition.DestinationOClock = 9;
    if nargin >= 4 && ~isempty(label)
        transition.LabelString = label;
    end
catch
    % Ignore transition drawing issues to keep chart generation robust.
end
end

function positions = layoutGrid(count, startX, startY, cols, width, height, xGap, yGap)
positions = zeros(count, 4);
for i = 1:count
    row = floor((i - 1) / cols);
    col = mod((i - 1), cols);
    positions(i, :) = [ ...
        startX + col * (width + xGap), ...
        startY + row * (height + yGap), ...
        width, ...
        height ...
    ];
end
end
