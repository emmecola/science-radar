import json
from datetime import datetime

import httpx

from crewai.llms.hooks.base import BaseInterceptor

captured_impacts: list[dict] = []
current_step: str = ""


def set_current_step(step: str) -> None:
    global current_step
    current_step = step


class MeliousEnvImpactInterceptor(BaseInterceptor[httpx.Request, httpx.Response]):
    def on_outbound(self, message: httpx.Request) -> httpx.Request:
        return message

    def on_inbound(self, message: httpx.Response) -> httpx.Response:
        if "application/json" in message.headers.get("content-type", ""):
            message.read()
            try:
                data = json.loads(message.content)
                if "environment_impact" in data:
                    captured_impacts.append({
                        "timestamp": datetime.now().isoformat(),
                        "step": current_step,
                        "value": data["environment_impact"],
                    })
            except Exception:
                pass
        return message
