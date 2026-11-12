from datetime import datetime


def test_create_project(client):
    response = client.post(
        "/api/v1/projects/",
        json={
            "title": "Company CRM",
            "business_idea": (
                "Develop a CRM application for "
                "customer relationship management."
            ),
            "product_type": "Internal Software",
            "sponsor": "Sales Manager",
        },
    )

    # Check successful project creation.
    assert response.status_code == 201
    data = response.json()

    # Verify generated project identifier.
    assert data["project_id"].startswith("PRJ-")

    # Verify project information.
    assert data["title"] == "Company CRM"

    # Verify initial status.
    assert data["status"] == "INTAKE"


def test_invalid_project_input(client):
    response = client.post(
        "/api/v1/projects/",
        json={
            "title": "CRM",
            "business_idea": "CRM",
        },
    )

    # Short input should fail schema validation.
    assert response.status_code == 422


def test_get_all_projects(client):
    create_response = client.post(
        "/api/v1/projects/",
        json={
            "title": "Company CRM",
            "business_idea": "A CRM for managing customer relationships.",
        },
    )
    assert create_response.status_code == 201

    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert isinstance(projects, list)
    assert len(projects) == 1
    assert projects[0]["project_id"] == create_response.json()["project_id"]


def test_get_nonexistent_project(client):
    response = client.get("/api/v1/projects/PRJ-NOTFOUND")
    assert response.status_code == 404


def _create_project(client):
    response = client.post(
        "/api/v1/projects/",
        json={
            "title": "Discovery project",
            "business_idea": "A project created to test discovery and evidence.",
        },
    )
    assert response.status_code == 201
    return response.json()["project_id"]


def test_discovery_records_are_saved_and_retrieved(client):
    project_id = _create_project(client)

    created = client.post(
        f"/api/v1/discovery/{project_id}",
        json={
            "target_users": ["Sales representatives"],
            "current_workflow": "Customer data is tracked in spreadsheets.",
            "open_questions": ["Which integrations are required?"],
        },
    )
    assert created.status_code == 201
    assert created.json()["project_id"] == project_id

    retrieved = client.get(f"/api/v1/discovery/{project_id}")
    assert retrieved.status_code == 200
    assert len(retrieved.json()) == 1
    assert retrieved.json()[0]["target_users"] == ["Sales representatives"]


def test_discovery_requires_a_project_and_some_content(client):
    missing_project = client.post(
        "/api/v1/discovery/PRJ-NOTFOUND",
        json={"notes": "Discovery notes"},
    )
    assert missing_project.status_code == 404

    project_id = _create_project(client)
    empty_discovery = client.post(
        f"/api/v1/discovery/{project_id}",
        json={},
    )
    assert empty_discovery.status_code == 422


def test_evidence_is_saved_and_provenance_is_immutable(client):
    project_id = _create_project(client)
    evidence_date = "2026-10-25T10:30:00Z"

    created = client.post(
        "/api/v1/evidence/",
        json={
            "project_id": project_id,
            "claim": "Users rely on manual customer tracking.",
            "evidence_type": "USER_REPORTED",
            "source": "Interview with sales manager",
            "evidence_date": evidence_date,
            "limitations": ["One interview"],
        },
    )
    assert created.status_code == 201
    evidence = created.json()

    listed = client.get(f"/api/v1/evidence/{project_id}")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["source"] == "Interview with sales manager"

    updated = client.patch(
        f"/api/v1/evidence/{evidence['evidence_id']}",
        json={"claim": "Sales staff report manual customer tracking."},
    )
    assert updated.status_code == 200
    assert updated.json()["claim"] == "Sales staff report manual customer tracking."
    assert updated.json()["source"] == "Interview with sales manager"
    persisted_evidence_date = datetime.fromisoformat(
        updated.json()["evidence_date"].replace("Z", "+00:00")
    )
    expected_evidence_date = datetime.fromisoformat(
        evidence_date.replace("Z", "+00:00")
    )
    assert persisted_evidence_date == expected_evidence_date

    provenance_update = client.patch(
        f"/api/v1/evidence/{evidence['evidence_id']}",
        json={
            "source": "Different source",
            "evidence_date": "2026-11-01T10:30:00Z",
        },
    )
    assert provenance_update.status_code == 422


def test_invalid_evidence_type_and_unknown_project_are_rejected(client):
    project_id = _create_project(client)
    payload = {
        "project_id": project_id,
        "claim": "Users rely on manual customer tracking.",
        "evidence_type": "MADE_UP",
        "source": "Interview",
        "evidence_date": "2026-10-25T10:30:00Z",
    }

    invalid_type = client.post("/api/v1/evidence/", json=payload)
    assert invalid_type.status_code == 422

    payload["evidence_type"] = "OBSERVED"
    payload["project_id"] = "PRJ-NOTFOUND"
    unknown_project = client.post("/api/v1/evidence/", json=payload)
    assert unknown_project.status_code == 404


def test_conflicting_evidence_is_preserved_and_unknown_evidence_is_404(client):
    project_id = _create_project(client)
    common = {
        "project_id": project_id,
        "evidence_type": "OBSERVED",
        "source": "Workflow observation",
        "evidence_date": "2026-10-25T10:30:00Z",
    }
    for claim in (
        "Customers wait too long for responses.",
        "Customers receive responses within one hour.",
    ):
        response = client.post(
            "/api/v1/evidence/",
            json={**common, "claim": claim},
        )
        assert response.status_code == 201

    retrieved = client.get(f"/api/v1/evidence/{project_id}")
    assert len(retrieved.json()) == 2
    assert {item["claim"] for item in retrieved.json()} == {
        "Customers wait too long for responses.",
        "Customers receive responses within one hour.",
    }

    missing = client.patch(
        "/api/v1/evidence/EVID-NOTFOUND",
        json={"claim": "An updated claim"},
    )
    assert missing.status_code == 404
