from fastapi import APIRouter
from services.post_recycler import RecyclePostRequest  # ✅ import your model
from services.post_recycler import recycle_post

router = APIRouter(prefix="/api/v1")

@router.post("/recycle")
def recycle_endpoint(request: RecyclePostRequest):
    return recycle_post(
        request.post_id,
        request.platforms,
        request.schedule_time,
        request.optimization_params,
        request.creator_id
    )


