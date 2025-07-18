from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
import os

BASE_DIR = os.path.dirname(__file__)

template_dir = os.path.join(BASE_DIR, "templates")

template = Jinja2Templates(directory=template_dir)

app = APIRouter()

DEFAULT_VISITORS_LIST = []

class TrackVisitsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, save_to=None):
        super().__init__(app)
        self.save_to = save_to if save_to is not None else DEFAULT_VISITORS_LIST

    async def dispatch(self, request: Request, call_next):
        """save_to should be the exact name that is used in the StatsRouter"""
        visitor = f"{request.client.host} - {request.headers.get("user-agent")}"
        if isinstance(self.save_to, list):
            if visitor not in self.save_to:
                self.save_to.append(visitor)
        elif isinstance(self.save_to, str):
            with open(self.save_to, "a+") as file:
                file.seek(0)
                visitors = [line.strip() for line in file.readlines()]
                if visitor not in visitors:
                    file.write(visitor + "\n")

        response = await call_next(request)
        return response

class StatsRouter:
    def __init__(self, title, get_from=None):
        self.router = APIRouter(
            prefix="/stats",
            tags=["stats"]
        )
        self._add_routes()
        self.title = title
        self.get_from = get_from if get_from is not None else DEFAULT_VISITORS_LIST

    def _add_routes(self):
        @self.router.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def get_stats(request: Request):
            if isinstance(self.get_from, list):
                visitors = self.get_from.copy()
            elif isinstance(self.get_from, str):
                try:
                    with open(self.get_from, "r") as file:
                        visitors = [line.strip() for line in file.readlines()]
                except FileNotFoundError:
                    visitors = []
            return template.TemplateResponse("stats.html", context={"request": request, "title": self.title, "visitors": visitors})
