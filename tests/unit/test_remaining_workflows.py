def create_project(client):
    response = client.post(
        "/api/v1/projects/",
        json={
            "title": "End-to-end framework",
            "business_idea": "A workflow for creating and delivering product requirements.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


def approve_proposal(client, project_id, scope=None):
    scope = scope or ["Customer management"]
    created = client.post(
        f"/api/v1/proposals/{project_id}",
        json={
            "title": "Customer management proposal",
            "problem": "Customer data is fragmented.",
            "proposed_outcome": "Improve customer record management.",
            "scope": scope,
        },
    )
    assert created.status_code == 201, created.text
    proposal = created.json()

    submitted = client.post(
        f"/api/v1/proposals/{proposal['proposal_id']}/submit"
    )
    assert submitted.status_code == 200, submitted.text

    stale_version = client.post(
        f"/api/v1/proposals/{proposal['proposal_id']}/approve",
        json={
            "approver_id": "approver-1",
            "approver_role": "PRODUCT_OWNER",
            "version": proposal["version"] + 1,
            "approved_scope": scope,
        },
    )
    assert stale_version.status_code == 409

    approved = client.post(
        f"/api/v1/proposals/{proposal['proposal_id']}/approve",
        json={
            "approver_id": "approver-1",
            "approver_role": "PRODUCT_OWNER",
            "version": proposal["version"],
            "approved_scope": scope,
            "conditions": ["Review after pilot"],
        },
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["approval_history"]
    return proposal["proposal_id"]


def test_refinement_alternatives_experiments_and_feasibility(client):
    project_id = create_project(client)

    brief = {
        "problem": "Customer data is fragmented.",
        "target_users": ["Sales representatives"],
        "primary_outcome": "Improve record completeness.",
        "goals": [{"description": "Increase completeness", "baseline": None, "target": 90}],
        "personas": [
            {
                "name": "Sales user",
                "role": "Representative",
                "needs": ["Fast search"],
                "responsibilities": ["Maintain customer records"],
            }
        ],
        "scope": ["Customer management"],
        "non_goals": ["Billing"],
    }
    created_brief = client.post(
        f"/api/v1/refinement/{project_id}",
        json=brief,
    )
    assert created_brief.status_code == 201, created_brief.text
    assert created_brief.json()["status"] == "DRAFT"
    assert client.get(f"/api/v1/refinement/{project_id}").status_code == 200
    assert client.post(
        f"/api/v1/refinement/{project_id}",
        json={**brief, "problem": ""},
    ).status_code == 422

    alternatives = client.post(
        f"/api/v1/alternatives/{project_id}",
        json={
            "alternatives": [
                {
                    "name": "Improve spreadsheet process",
                    "type": "PROCESS_IMPROVEMENT",
                    "source": "Operations review",
                },
                {
                    "name": "Build customer platform",
                    "type": "BUILD",
                    "source": "Engineering estimate",
                },
            ]
        },
    )
    assert alternatives.status_code == 201, alternatives.text
    assert alternatives.json()["recommendation"] == "PENDING_REVIEW"
    assert len(client.get(f"/api/v1/alternatives/{project_id}").json()) == 1
    invalid_alternative = client.post(
        f"/api/v1/alternatives/{project_id}",
        json={
            "alternatives": [
                {"name": "Unsupported", "type": "CUSTOM", "source": "Research"}
            ]
        },
    )
    assert invalid_alternative.status_code == 422
    assert client.post(
        f"/api/v1/alternatives/{project_id}",
        json={"alternatives": [{"name": "No source", "type": "BUY"}]},
    ).status_code == 422

    experiment = client.post(
        f"/api/v1/experiments/{project_id}",
        json={
            "hypothesis": "A guided workflow improves completeness.",
            "method": "Test with five users.",
            "success_criteria": ["At least four users complete the flow."],
            "failure_criteria": ["Fewer than three users complete the flow."],
        },
    )
    assert experiment.status_code == 201, experiment.text
    assert experiment.json()["status"] == "PLANNED"
    assert len(client.get(f"/api/v1/experiments/{project_id}").json()) == 1
    assert client.post(
        f"/api/v1/experiments/{project_id}",
        json={
            "hypothesis": "Missing failure condition",
            "method": "Test",
            "success_criteria": ["Works"],
            "failure_criteria": [],
        },
    ).status_code == 422

    assessment = client.post(
        f"/api/v1/feasibility/{project_id}",
        json={
            "technical": "Supported by current stack.",
            "operational": "Training is required.",
            "financial": "Within budget.",
            "business": "Aligned with sales goals.",
            "tests": [{"name": "Load test", "status": "FAILED"}],
        },
    )
    assert assessment.status_code == 201, assessment.text
    assert assessment.json()["status"] == "FAILED"
    assessments = client.get(f"/api/v1/feasibility/{project_id}")
    assert len(assessments.json()) == 1
    assert assessments.json()[0]["tests"][0]["status"] == "FAILED"


def test_approval_prd_planning_execution_release_and_outcomes(client):
    project_id = create_project(client)
    scope = ["Customer management"]

    rejected = client.post(
        f"/api/v1/proposals/{project_id}",
        json={
            "title": "Second proposal",
            "problem": "A second problem.",
            "proposed_outcome": "A different result.",
            "scope": scope,
        },
    ).json()
    assert client.post(
        f"/api/v1/proposals/{rejected['proposal_id']}/submit"
    ).status_code == 200
    reject_response = client.post(
        f"/api/v1/proposals/{rejected['proposal_id']}/reject",
        json={
            "approver_id": "approver-2",
            "approver_role": "PRODUCT_OWNER",
            "version": rejected["version"],
            "reason": "Not prioritized",
        },
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "REJECTED"
    assert reject_response.json()["approval_history"]

    unapproved_project_id = create_project(client)
    prd_payload = {
        "project_id": unapproved_project_id,
        "problem_statement": "Customer data is fragmented.",
        "product_vision": "A trusted customer workspace.",
        "goals": ["Improve record completeness."],
        "scope": scope,
        "non_goals": ["Billing."],
        "requirements": [
            {
                "requirement_id": "REQ-1",
                "title": "Search customers",
                "actor": "Sales representative",
                "description": "Search customer records by name.",
                "rationale": "Users need to locate records.",
                "acceptance_criteria": ["Matching records are returned."],
                "priority": "HIGH",
                "phase_id": "PHASE-1",
            }
        ],
    }
    no_approval = client.post(
        f"/api/v1/prd/{unapproved_project_id}/generate",
        json=prd_payload,
    )
    assert no_approval.status_code == 409

    proposal_id = approve_proposal(client, project_id, scope)
    proposals = client.get(f"/api/v1/proposals/{project_id}")
    assert proposals.status_code == 200
    assert any(item["proposal_id"] == proposal_id for item in proposals.json())
    unauthorized_proposal = client.post(
        f"/api/v1/proposals/{proposal_id}/submit"
    )
    assert unauthorized_proposal.status_code == 409

    prd_payload["project_id"] = project_id
    unapproved_scope = {
        **prd_payload,
        "scope": ["Customer management", "Unapproved billing"],
    }
    out_of_scope_prd = client.post(
        f"/api/v1/prd/{project_id}/generate",
        json=unapproved_scope,
    )
    assert out_of_scope_prd.status_code == 409

    generated = client.post(
        f"/api/v1/prd/{project_id}/generate",
        json=prd_payload,
    )
    assert generated.status_code == 201, generated.text
    prd = generated.json()
    prd_id = prd["prd_id"]
    assert prd["validation"]["is_valid"] is True
    assert "## Requirements" in prd["markdown"]
    assert client.get(f"/api/v1/prd/{project_id}").status_code == 200
    assert client.get(f"/api/v1/prd/{project_id}/validate").json()["is_valid"]
    assert len(client.get(f"/api/v1/prd/{prd_id}/versions").json()) == 1

    submitted_prd = client.post(f"/api/v1/prd/{prd_id}/submit")
    assert submitted_prd.status_code == 200, submitted_prd.text
    approved_prd = client.post(
        f"/api/v1/prd/{prd_id}/approve",
        json={
            "approver_id": "approver-1",
            "approver_role": "SPONSOR",
        },
    )
    assert approved_prd.status_code == 200, approved_prd.text
    assert approved_prd.json()["status"] == "APPROVED"

    plan = client.post(f"/api/v1/planning/{prd_id}/generate")
    assert plan.status_code == 201, plan.text
    task = plan.json()["tasks"][0]
    assert len(client.get(f"/api/v1/planning/{project_id}/phases").json()) == 1
    assert len(client.get(f"/api/v1/planning/{project_id}/tasks").json()) == 1

    not_ready = client.post(
        f"/api/v1/execution/tasks/{task['task_id']}/start"
    )
    assert not_ready.status_code == 409
    blocked = client.patch(
        f"/api/v1/tasks/{task['task_id']}/status",
        json={"status": "BLOCKED"},
    )
    assert blocked.status_code == 200
    blocked_to_ready = client.patch(
        f"/api/v1/tasks/{task['task_id']}/status",
        json={"status": "READY"},
    )
    assert blocked_to_ready.status_code == 409
    ready = client.patch(
        f"/api/v1/tasks/{task['task_id']}/status",
        json={"status": "BACKLOG"},
    )
    assert ready.status_code == 200
    ready = client.patch(
        f"/api/v1/tasks/{task['task_id']}/status",
        json={"status": "READY"},
    )
    assert ready.status_code == 200
    started = client.post(f"/api/v1/execution/tasks/{task['task_id']}/start")
    assert started.status_code == 201, started.text
    failed_verification = client.post(
        f"/api/v1/execution/tasks/{task['task_id']}/verification",
        json={"test_results": [], "evidence_ids": []},
    )
    assert failed_verification.status_code == 201
    assert failed_verification.json()["status"] == "FAILED"
    assert client.get(
        f"/api/v1/execution/tasks/{task['task_id']}/history"
    ).status_code == 200

    retry_ready = client.patch(
        f"/api/v1/tasks/{task['task_id']}/status",
        json={"status": "READY"},
    )
    assert retry_ready.status_code == 200
    assert client.post(
        f"/api/v1/execution/tasks/{task['task_id']}/start"
    ).status_code == 201
    evidence = client.post(
        "/api/v1/evidence/",
        json={
            "project_id": project_id,
            "claim": "Automated acceptance checks passed.",
            "evidence_type": "OBSERVED",
            "source": "CI test run",
            "evidence_date": "2026-10-25T10:30:00Z",
        },
    )
    assert evidence.status_code == 201
    verification = client.post(
        f"/api/v1/execution/tasks/{task['task_id']}/verification",
        json={
            "test_results": ["PASSED"],
            "evidence_ids": [evidence.json()["evidence_id"]],
        },
    )
    assert verification.status_code == 201
    assert verification.json()["status"] == "VERIFIED"
    assert client.get(f"/api/v1/planning/{project_id}/tasks").json()[0]["status"] == "DONE"

    release = client.post(
        "/api/v1/releases/",
        json={
            "project_id": project_id,
            "prd_version": 1,
            "build_version": "1.0.0",
            "environment": "staging",
            "verified_tasks": [task["task_id"]],
            "uat_status": "PASSED",
            "migration_status": "NOT_REQUIRED",
            "recovery_plan": "Roll back to 0.9.0.",
            "rollout_strategy": "Pilot then expand.",
        },
    )
    assert release.status_code == 201, release.text
    release_id = release.json()["release_id"]
    assert release.json()["ready_for_review"]
    assert len(client.get(f"/api/v1/releases/{project_id}").json()) == 1

    go = client.post(
        f"/api/v1/releases/{release_id}/go-no-go",
        json={
            "prd_version": 1,
            "decision": "GO",
            "decided_by": "release-approver",
            "role": "EXECUTIVE",
            "rationale": "Readiness checks passed.",
        },
    )
    assert go.status_code == 200, go.text
    result = client.post(
        f"/api/v1/releases/{release_id}/record-result",
        json={
            "build_version": "1.0.0",
            "health_checks": ["PASSED"],
            "outcome": "SUCCEEDED",
        },
    )
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "COMPLETED"

    failed_release = client.post(
        "/api/v1/releases/",
        json={
            "project_id": project_id,
            "prd_version": 1,
            "build_version": "1.0.1",
            "environment": "staging",
            "verified_tasks": [task["task_id"]],
            "uat_status": "PASSED",
            "migration_status": "NOT_REQUIRED",
            "recovery_plan": "Roll back to 1.0.0.",
            "rollout_strategy": "Pilot then expand.",
        },
    )
    assert failed_release.status_code == 201
    failed_release_id = failed_release.json()["release_id"]
    assert client.post(
        f"/api/v1/releases/{failed_release_id}/go-no-go",
        json={
            "prd_version": 1,
            "decision": "GO",
            "decided_by": "release-approver",
            "role": "EXECUTIVE",
            "rationale": "Ready for staging.",
        },
    ).status_code == 200
    failed_health = client.post(
        f"/api/v1/releases/{failed_release_id}/record-result",
        json={
            "build_version": "1.0.1",
            "health_checks": ["FAILED"],
            "outcome": "SUCCEEDED",
        },
    )
    assert failed_health.status_code == 409
    stopped = client.post(
        f"/api/v1/releases/{failed_release_id}/record-result",
        json={
            "build_version": "1.0.1",
            "health_checks": ["FAILED"],
            "outcome": "FAILED",
            "recovery_action": "Rolled back to 1.0.0.",
        },
    )
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "STOPPED"
    assert stopped.json()["result_history"][-1]["recovery_action"]

    metric = client.post(
        f"/api/v1/outcomes/{project_id}/metrics",
        json={
            "name": "Record completeness",
            "unit": "percent",
            "direction": "HIGHER_IS_BETTER",
            "baseline": 50,
            "target": 90,
            "source": "Initial audit",
            "owner": "Sales operations",
        },
    )
    assert metric.status_code == 201, metric.text
    metric_id = metric.json()["metric_id"]
    assert len(client.get(f"/api/v1/outcomes/{project_id}/metrics").json()) == 1
    measurement = client.post(
        f"/api/v1/outcomes/{project_id}/measurements",
        json={
            "metric_id": metric_id,
            "actual": 70,
            "source": "Quarterly audit",
        },
    )
    assert measurement.status_code == 201, measurement.text
    assert measurement.json()["achievement"] == 50
    report = client.get(f"/api/v1/outcomes/{project_id}/report")
    assert report.status_code == 200
    assert report.json()["metrics"][0]["latest_measurement"]["actual"] == 70
    decision = client.post(
        f"/api/v1/outcomes/{project_id}/decision",
        json={
            "decision": "CONTINUE",
            "rationale": "Metric progress is positive.",
            "decided_by": "product-owner",
        },
    )
    assert decision.status_code == 201

    next_version = client.post(
        f"/api/v1/prd/{project_id}/generate",
        json=prd_payload,
    )
    assert next_version.status_code == 201
    assert next_version.json()["version"] == 2
    assert len(client.get(f"/api/v1/prd/{prd_id}/versions").json()) == 2
