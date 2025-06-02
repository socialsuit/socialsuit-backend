from fastapi import APIRouter, Body
from typing import Optional
from services.ab_testing import run_ab_test  
router = APIRouter()

@router.post("/ab_test")
def ab_test_endpoint(
    content_a: str = Body(...),
    content_b: str = Body(...),
    test_name: Optional[str] = None,
    target_metric: str = "engagement_rate",
    audience_percentage: float = 0.5
):
    return run_ab_test(
        content_a=content_a,
        content_b=content_b,
        test_name=test_name,
        target_metric=target_metric,
        audience_percentage=audience_percentage
    )
