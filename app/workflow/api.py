"""
Workflow API endpoints for real-time monitoring.
"""
import asyncio
import logging
from typing import Dict, Any, Event

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from starlette.events import EventSourceResponse

from app.workflow.engine import workflow_engine, WorkflowState, WorkflowStage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow", tags=["Workflow"])


@router.get("/status")
async def get_workflow_status() -> Dict[str, Any]:
    """
    Get current workflow engine status.
    """
    return workflow_engine.get_status()


@router.post("/start")
async def start_workflow() -> Dict[str, Any]:
    """
    Start the continuous workflow engine.
    """
    if workflow_engine.is_running:
        return {"status": "already_running", "message": "Workflow engine is already running"}
    
    # Start in background
    asyncio.create_task(workflow_engine.start())
    
    return {"status": "started", "message": "Workflow engine started"}


@router.post("/stop")
async def stop_workflow() -> Dict[str, Any]:
    """
    Stop the continuous workflow engine.
    """
    if not workflow_engine.is_running:
        return {"status": "already_stopped", "message": "Workflow engine is not running"}
    
    await workflow_engine.stop()
    
    return {"status": "stopped", "message": "Workflow engine stopped"}


@router.get("/history")
async def get_workflow_history(limit: int = 10) -> Dict[str, Any]:
    """
    Get workflow execution history.
    """
    history = workflow_engine.history[-limit:]
    return {"history": history, "total": len(workflow_engine.history)}


@router.get("/stream")
async def workflow_stream():
    """
    Server-Sent Events endpoint for real-time workflow updates.
    """
    async def event_generator():
        queue = workflow_engine.subscribe()
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {{'type': 'heartbeat', 'time': '{asyncio.get_event_loop().time()}'}}\n\n"
        finally:
            workflow_engine.unsubscribe(queue)
    
    return EventSourceResponse(event_generator())


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time workflow updates.
    """
    await websocket.accept()
    
    queue = workflow_engine.subscribe()
    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        workflow_engine.unsubscribe(queue)


# Simple dashboard HTML
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🔄 Workflow Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh; color: #fff; padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 30px; color: #00d4ff; }
        
        .status-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .status-item {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        
        .status-item .label { color: #888; font-size: 12px; }
        .status-item .value { font-size: 24px; font-weight: bold; color: #00d4ff; }
        
        .progress-bar {
            height: 30px;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            width: 0%;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .stages {
            display: flex;
            justify-content: space-between;
            margin: 30px 0;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .stage {
            background: rgba(0,0,0,0.3);
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 14px;
            opacity: 0.5;
        }
        
        .stage.active {
            background: #00d4ff;
            color: #000;
            opacity: 1;
        }
        
        .stage.completed {
            background: #00ff88;
            color: #000;
            opacity: 1;
        }
        
        .log {
            background: #000;
            padding: 15px;
            border-radius: 10px;
            font-family: monospace;
            height: 300px;
            overflow-y: auto;
            font-size: 12px;
        }
        
        .log-entry { margin: 5px 0; }
        .log-entry.info { color: #00d4ff; }
        .log-entry.success { color: #00ff88; }
        .log-entry.warning { color: #ffaa00; }
        .log-entry.error { color: #ff4444; }
        
        .controls { text-align: center; margin: 20px 0; }
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            margin: 5px;
            transition: transform 0.2s;
        }
        .btn:hover { transform: scale(1.05); }
        .btn-start { background: #00ff88; color: #000; }
        .btn-stop { background: #ff4444; color: #fff; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .running { animation: pulse 1s infinite; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 頂級企業級自動化工作流</h1>
        
        <div class="status-card">
            <div class="status-grid">
                <div class="status-item">
                    <div class="label">狀態</div>
                    <div class="value" id="state">IDLE</div>
                </div>
                <div class="status-item">
                    <div class="label">迭代次數</div>
                    <div class="value" id="iteration">0</div>
                </div>
                <div class="status-item">
                    <div class="label">當前階段</div>
                    <div class="value" id="stage">-</div>
                </div>
                <div class="status-item">
                    <div class="label">進度</div>
                    <div class="value" id="progress">0%</div>
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="progressBar">0%</div>
            </div>
            
            <div class="stages">
                <div class="stage" data-stage="trigger">📥 觸發</div>
                <div class="stage" data-stage="reasoning">🧠 推理</div>
                <div class="stage" data-stage="planning">📋 規劃</div>
                <div class="stage" data-stage="execution">⚙️ 執行</div>
                <div class="stage" data-stage="quality_gates">✅ QA</div>
                <div class="stage" data-stage="deployment">🚀 部署</div>
                <div class="stage" data-stage="monitoring">📊 監控</div>
                <div class="stage" data-stage="notification">📢 回報</div>
            </div>
            
            <div class="controls">
                <button class="btn btn-start" onclick="startWorkflow()">▶ 啟動</button>
                <button class="btn btn-stop" onclick="stopWorkflow()">⏹ 停止</button>
            </div>
        </div>
        
        <div class="status-card">
            <h3>📝 運行日誌</h3>
            <div class="log" id="log"></div>
        </div>
    </div>
    
    <script>
        const eventSource = new EventSource('/api/v1/workflow/stream');
        const log = document.getElementById('log');
        
        function addLog(msg, type = 'info') {
            const time = new Date().toLocaleTimeString();
            log.innerHTML += `<div class="log-entry ${type}">[${time}] ${msg}</div>`;
            log.scrollTop = log.scrollHeight;
        }
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(data);
            
            if (data.type === 'engine_start') {
                document.getElementById('state').textContent = 'RUNNING';
                document.getElementById('state').classList.add('running');
                addLog('🚀 工作流引擎啟動', 'success');
            } else if (data.type === 'engine_stop') {
                document.getElementById('state').textContent = 'PAUSED';
                document.getElementById('state').classList.remove('running');
                addLog('⏸️ 工作流引擎停止', 'warning');
            } else if (data.type === 'stage_change') {
                document.getElementById('iteration').textContent = data.iteration;
                document.getElementById('stage').textContent = data.stage;
                document.getElementById('progress').textContent = data.progress + '%';
                document.getElementById('progressBar').style.width = data.progress + '%';
                document.getElementById('progressBar').textContent = data.progress + '%';
                addLog(`📍 階段: ${data.stage} (${data.progress}%)`, 'info');
                
                // Update stage indicators
                document.querySelectorAll('.stage').forEach(el => {
                    el.classList.remove('active', 'completed');
                });
                document.querySelector(`[data-stage="${data.stage}"]`)?.classList.add('active');
            } else if (data.type === 'error') {
                addLog(`❌ 錯誤: ${data.error}`, 'error');
            } else if (data.type === 'heartbeat') {
                // Keep connection alive
            }
        };
        
        async function startWorkflow() {
            await fetch('/api/v1/workflow/start', { method: 'POST' });
            addLog('▶ 發送啟動指令...', 'info');
        }
        
        async function stopWorkflow() {
            await fetch('/api/v1/workflow/stop', { method: 'POST' });
            addLog('⏹ 發送停止指令...', 'info');
        }
        
        // Initial status
        fetch('/api/v1/workflow/status').then(r => r.json()).then(data => {
            document.getElementById('state').textContent = data.state;
            document.getElementById('iteration').textContent = data.iteration;
            document.getElementById('progress').textContent = data.progress + '%';
            document.getElementById('progressBar').style.width = data.progress + '%';
        });
    </script>
</body>
</html>
"""


@router.get("/dashboard")
async def workflow_dashboard() -> HTMLResponse:
    """Simple workflow dashboard."""
    return HTMLResponse(DASHBOARD_HTML)