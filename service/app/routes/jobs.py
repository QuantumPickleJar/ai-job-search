"""Reserved for authenticated job routes in a later Phase 3 task."""

from fastapi import APIRouter


router = APIRouter(prefix="/jobs", tags=["jobs"])
