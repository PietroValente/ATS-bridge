import os

import grpc

import klaaryo_pb2
import klaaryo_pb2_grpc
from adapters.protocol import NormalizedApplication


def _stub() -> klaaryo_pb2_grpc.TalentPoolStub:
    host = os.environ.get("TALENT_POOL_HOST", "talent_pool")
    port = os.environ.get("TALENT_POOL_PORT", "50051")
    channel = grpc.insecure_channel(f"{host}:{port}")
    return klaaryo_pb2_grpc.TalentPoolStub(channel)


def upsert_candidate(n: NormalizedApplication) -> None:
    _stub().UpsertCandidate(
        klaaryo_pb2.NormalizedCandidate(
            external_id=n.external_id,
            ats_source=n.ats_source,
            first_name=n.first_name,
            last_name=n.last_name,
            email=n.email,
            phone=n.phone,
            age=n.age,
            job_external_id=n.job_external_id,
            internal_status=n.internal_status,
            applied_at=n.applied_at,
        )
    )
