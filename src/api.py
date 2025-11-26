# src/api.py
from flask import Flask, request, jsonify
from src.orchestrator import Orchestrator
from src.scheduler import Scheduler
from config.config import Config
import asyncio
import threading
import logging

app = Flask(__name__)
config = Config()
orchestrator = Orchestrator(config)
scheduler = Scheduler(config, orchestrator)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This will be used to run asyncio tasks from Flask threads
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "running", "project": "Content Creator API"}), 200

@app.route('/api/run_pipeline', methods=['POST'])
def run_pipeline():
    data = request.json
    phase = data.get('phase')
    agent_name = data.get('agent_name')

    if not phase:
        return jsonify({"error": "Phase is required"}), 400

    def _run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if agent_name:
                logger.info(f"Triggering specific agent: {agent_name} in phase {phase}")
                # This needs to be adapted based on how orchestrator triggers specific agents
                # For now, let's assume orchestrator has a method for this or we trigger a full phase
                result = loop.run_until_complete(orchestrator.run_phase(phase))
            else:
                logger.info(f"Triggering full pipeline for phase {phase}")
                result = loop.run_until_complete(orchestrator.run_phase(phase))
            logger.info(f"Pipeline for phase {phase} completed with result: {result}")
        except Exception as e:
            logger.error(f"Error running pipeline for phase {phase}: {e}", exc_info=True)
            # You might want to store error status somewhere accessible via another endpoint
        finally:
            loop.close()

    thread = threading.Thread(target=_run_in_thread)
    thread.start()

    return jsonify({"message": f"Pipeline for phase {phase} initiated in background.", "phase": phase, "agent_name": agent_name}), 202

@app.route('/api/run_scheduled_task', methods=['POST'])
def run_scheduled_task():
    data = request.json
    task_name = data.get('task_name')

    if not task_name:
        return jsonify({"error": "Task name is required"}), 400

    def _run_scheduled_task_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info(f"Attempting to run scheduled task: {task_name}")
            # This needs to call the actual task function from scheduler
            # For simplicity, we can assume a direct mapping or a lookup in scheduler
            if hasattr(scheduler, f'run_{task_name}'): # Assuming tasks are methods like run_market_scan
                 task_func = getattr(scheduler, f'run_{task_name}')
                 result = loop.run_until_complete(task_func())
            else:
                logger.warning(f"No direct method for scheduled task: {task_name}")
                result = {"status": "failed", "reason": "Task not found"}
            logger.info(f"Scheduled task {task_name} completed with result: {result}")
        except Exception as e:
            logger.error(f"Error running scheduled task {task_name}: {e}", exc_info=True)
        finally:
            loop.close()

    thread = threading.Thread(target=_run_scheduled_task_in_thread)
    thread.start()

    return jsonify({"message": f"Scheduled task {task_name} initiated in background.", "task_name": task_name}), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001) # Using a different port to avoid conflict if Agent-Zero uses 5000
