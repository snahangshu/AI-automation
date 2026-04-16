import json
import threading
import websocket
from urllib.parse import urlencode
from config.settings import settings

class STTEngine:
    def __init__(self, on_message, on_error, on_close):
        self.api_key = settings.ASSEMBLYAI_API_KEY
        self.endpoint_base = "wss://streaming.assemblyai.com/v3/ws"
        self.params = {
            "sample_rate": settings.SAMPLE_RATE,
            "format_turns": True
        }
        self.url = f"{self.endpoint_base}?{urlencode(self.params)}"
        
        self.on_message_callback = on_message
        self.on_error_callback = on_error
        self.on_close_callback = on_close
        
        self.ws = None

    def start(self):
        headers = [f"Authorization: {self.api_key}"]
        self.ws = websocket.WebSocketApp(
            self.url,
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message_callback,
            on_error=self.on_error_callback,
            on_close=self.on_close_callback
        )
        
        ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        ws_thread.start()

    def on_open(self, ws):
        print("[DEBUG] AssemblyAI WebSocket connection opened.")

    def send_audio(self, audio_data):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(audio_data, websocket.ABNF.OPCODE_BINARY)

    def stop(self):
        if self.ws:
            try:
                self.ws.send(json.dumps({"type": "Terminate"}))
                self.ws.close()
            except Exception:
                pass
            self.ws = None
