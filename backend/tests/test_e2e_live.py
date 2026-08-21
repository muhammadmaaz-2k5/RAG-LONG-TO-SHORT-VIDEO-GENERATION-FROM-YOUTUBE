import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_health_live(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert data["embedding_dimensions"] == 384


@pytest.mark.asyncio
async def test_video_submission_and_flow(client: AsyncClient):
    # 1. Submit a popular YouTube video with verified captions (Me at the zoo)
    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    create_res = await client.post("/api/videos", json={"youtube_url": video_url})
    assert create_res.status_code in (200, 201)
    video_data = create_res.json()
    assert "id" in video_data
    video_id = video_data["id"]
    assert video_data["youtube_id"] == "jNQXAC9IVRw"

    # 2. Process video transcript and generate pgvector embeddings
    proc_res = await client.post(f"/api/videos/{video_id}/process")
    if proc_res.status_code != 200:
        print("PROCESS ERROR DETAIL:", proc_res.json())
    assert proc_res.status_code == 200
    proc_data = proc_res.json()
    assert proc_data["status"] == "READY"
    assert proc_data["chunks_created"] > 0

    # 3. Check chunks
    chunks_res = await client.get(f"/api/videos/{video_id}/chunks")
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) > 0
    assert chunks[0]["has_embedding"] is True

    # 4. Generate Shorts using RAG + Groq
    gen_res = await client.post(
        "/api/shorts/generate",
        json={"video_id": video_id, "count": 1, "duration": 60, "style": "VIRAL"},
    )
    assert gen_res.status_code == 201
    gen_data = gen_res.json()
    assert gen_data["status"] == "GENERATED"
    assert len(gen_data["shorts"]) >= 1
    short = gen_data["shorts"][0]
    assert len(short["title"]) > 0
    assert len(short["hook"]) > 0
    assert len(short["script"]) > 0
    short_id = short["id"]

    # 5. Fetch single Short
    get_short_res = await client.get(f"/api/shorts/{short_id}")
    assert get_short_res.status_code == 200
    fetched_short = get_short_res.json()
    assert fetched_short["id"] == short_id
    assert len(fetched_short["sources"]) > 0

    # 6. Regenerate Short
    regen_res = await client.post(
        f"/api/shorts/{short_id}/regenerate",
        json={"style": "EDUCATIONAL", "duration": 45},
    )
    assert regen_res.status_code == 200
    regen_data = regen_res.json()
    assert regen_data["style"] == "EDUCATIONAL"
    assert len(regen_data["script"]) > 0
