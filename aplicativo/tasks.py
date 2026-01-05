# aplicativo/tasks.py
from celery import shared_task
from .services.atualizar_noticias_job import atualizar_noticias_job
from .services.indicadores_service import atualizar_dashboard_por_id

@shared_task(bind=True)
def atualizar_noticias_task(self):
    # Se quiser progresso real por fonte, a gente adapta o job depois.
    novas = atualizar_noticias_job()
    return {"novas": novas}


@shared_task(bind=True)
def atualizar_dashboard_task(self, dashboard_id: int):
    def cb(done, total):
        percent = int((done / total) * 100) if total else 100
        self.update_state(
            state="PROGRESS",
            meta={"current": done, "total": total, "percent": percent},
        )

    return atualizar_dashboard_por_id(dashboard_id, progress_cb=cb)
