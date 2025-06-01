import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

app = Celery("project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


app.conf.beat_schedule = {
    "refresh-all-spotify-tokens": {
        "task": "spotify_integration.tasks.refresh_all_spotify_tokens_task",
        "schedule": settings.REFRESH_ALL_SPOTIFY_TOKENS,  # 25 minutes by default
    },
    "fetch_all_spotify_data_task": {
        "task": "spotify_integration.tasks.fetch_all_spotify_data_task",
        "schedule": settings.FETCH_ALL_SPOTIFY_DATA,  # 30 minutes by default
    },
}
