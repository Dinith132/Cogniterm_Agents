from fastapi import FastAPI, WebSocket
import json
import uvicorn
from agents.llm_manager import LLMManager
from main import MultiAgentOrchestrator

app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Create LLM + orchestrator per client
    llm = LLMManager(api_key="AIzaSyCO590GfHqyGtSEKaCYtHSA4HhR0G-S12M")
    
    orchestrator = MultiAgentOrchestrator(llm, websocket=websocket)

    try:
        while True:
            # Receive request from this client
            data = await websocket.receive_text()

            request_text = data
            if not request_text:
                await websocket.send_text(json.dumps({"error": "Empty request"}))
                continue

            # Run orchestrator for this request
            summary = await orchestrator.execute_request(request_text)

            # Send final report to this client
            await websocket.send_text(json.dumps({"final_report": summary}))

    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass
    finally:
        await websocket.close()


# Run the server
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
