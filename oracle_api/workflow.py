"""Issue-aware, evidence-ranked investigation workflow built with LangGraph."""

from __future__ import annotations

import re
from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from oracle.softcomputing.bayes_hypothesis import update_hypothesis_probability
from oracle.softcomputing.fuzzy_risk import assess_fuzzy_risk
from oracle.softcomputing.ga_test_priority import prioritize_tests
from oracle.softcomputing.log_classifier import classify_log_text

from .analyzer import analyze_repository
from .llm import explain_findings
from .rag import retrieve_for_hypothesis

GitHubJson = Callable[[str, str], dict]
STOP_WORDS = {
    "after", "again", "about", "before", "being", "cannot", "could", "during",
    "from", "have", "into", "issue", "when", "where", "which", "while", "with",
    "would", "your", "that", "this", "then", "than", "there", "their", "they",
    "them", "what", "were", "will", "been", "does", "doesn", "error", "started",
}
class InvestigationState(TypedDict, total=False):
    issue_report: str
    log_text: str
    scan_result: dict
    hypotheses: list[dict]
    riskAssessment: dict | None
    aiAnalysis: dict
    logAnalysis: dict
    testPlan: dict
    investigation: dict


def _tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9_]{3,}", text.lower())
        if token not in STOP_WORDS
    }


def _rank_hypotheses(issue_report: str, findings: list[dict], log_analysis: dict | None = None) -> list[dict]:
    log_context = " ".join(
        item.get("message", "")
        for item in (log_analysis or {}).get("classifications", [])
    )
    issue_terms = _tokens(f"{issue_report} {log_context}")
    hypotheses = []
    for finding in findings:
        finding_terms = _tokens(" ".join((
            finding.get("title", ""), finding.get("file", ""),
            finding.get("evidence", ""), finding.get("category", ""),
        )))
        matched_terms = sorted(issue_terms & finding_terms)
        severity = finding.get("severity", "low")
        confidence = float(finding.get("confidence", 0.0))
        bayesian = update_hypothesis_probability(
            confidence, len(matched_terms), len(issue_terms)
        )
        fuzzy_risk = assess_fuzzy_risk(severity, confidence, bayesian["posterior"])

        hypotheses.append({
            "id": f"hypothesis:{finding.get('id', finding.get('file', 'finding'))}",
            "title": f"{finding.get('title', 'Source finding')} in {finding.get('file', 'unknown file')} may contribute to the issue.",
            "file": finding.get("file", ""),
            "line": finding.get("line", 0),
            "severity": severity,
            "confidence": confidence,
            "priorityScore": bayesian["posterior"],
            "bayesian": bayesian,
            "riskAssessment": fuzzy_risk,
            "matchedTerms": matched_terms,
            "evidence": finding.get("evidence", ""),
            "suggestion": finding.get("suggestion", "Review this source finding."),
            "reason": bayesian["reason"],
            "findingId": finding.get("id", ""),
        })

    return sorted(
        hypotheses,
        key=lambda item: (
            -item["priorityScore"],
            -item["riskAssessment"]["score"],
            item["file"],
            item["line"],
        ),
    )


def run_investigation(
    owner: str,
    repo: str,
    token: str,
    issue_report: str,
    github_json: GitHubJson,
    log_text: str = "",
) -> dict:
    """Run the graph for one request; credentials stay in the scan-node closure."""

    def scan_repository_node(state: InvestigationState) -> dict:
        return {
            "scan_result": analyze_repository(owner, repo, token, github_json)
        }

    def rank_evidence_node(state: InvestigationState) -> dict:
        findings = state["scan_result"].get("findings", [])
        hypotheses = _rank_hypotheses(
            state.get("issue_report", ""), findings, state.get("logAnalysis", {})
        )
        overall_risk = max(
            (item["riskAssessment"] for item in hypotheses),
            key=lambda assessment: assessment["score"],
            default=None,
        )
        return {
            "hypotheses": hypotheses,
            "riskAssessment": overall_risk,
        }

    def classify_logs_node(state: InvestigationState) -> dict:
        return {"logAnalysis": classify_log_text(state.get("log_text", ""))}

    def prioritize_tests_node(state: InvestigationState) -> dict:
        scan = state["scan_result"]
        plan = prioritize_tests(
            scan.get("testCandidates", []),
            state.get("hypotheses", []),
        )
        plan["historyNote"] = scan.get("testHistory", {}).get("note", "")
        return {"testPlan": plan}

    def retrieve_context_node(state: InvestigationState) -> dict:
        documents = state["scan_result"].get("_ragDocuments", [])
        hypotheses = state.get("hypotheses", [])
        for index, hypothesis in enumerate(hypotheses):
            hypothesis["ragSources"] = retrieve_for_hypothesis(
                hypothesis, state.get("issue_report", ""), documents
            ) if index < 8 else []
        return {"hypotheses": hypotheses}

    def explain_findings_node(state: InvestigationState) -> dict:
        ai_analysis = explain_findings(
            state.get("issue_report", ""), state.get("hypotheses", [])
        )
        explanations = ai_analysis.get("explanations", {})
        for hypothesis in state.get("hypotheses", []):
            generated = explanations.get(hypothesis.get("id"), {})
            hypothesis["aiExplanation"] = generated.get("explanation", "")
            hypothesis["aiSuggestedFix"] = generated.get("suggestedFix", "")
        return {"hypotheses": state.get("hypotheses", []), "aiAnalysis": ai_analysis}

    def publish_report_node(state: InvestigationState) -> dict:
        findings = state["scan_result"].get("findings", [])
        hypotheses = state.get("hypotheses", [])
        logs = state["logAnalysis"].get("classifications", [])
        tests = state["testPlan"].get("tests", [])
        ai_analysis = state.get("aiAnalysis", {})
        summary = (
            f"Ranked {len(hypotheses)} candidate cause(s) with Bayesian updates and "
            f"Mamdani fuzzy risk scoring; classified {len(logs)} supplied log line(s); "
            f"prioritized {len(tests)} test file(s). MLP scores use synthetic training "
            "examples and are uncalibrated. Repository context was retrieved locally for "
            f"{sum(bool(item.get('ragSources')) for item in hypotheses)} candidate(s). "
            + (f"Optional {ai_analysis.get('provider')} explanations are {ai_analysis.get('status')}. " if ai_analysis else "")
            + "Bayesian estimates use hand-set rule scores and are not validated probabilities."
        ) if findings or logs or tests else (
            "No checked source patterns matched, no logs were supplied, and no test files "
            "were found. This does not prove the reported issue has no cause."
        )
        return {"investigation": {
            "issueReport": state.get("issue_report", ""),
            "summary": summary,
            "engine": "LangGraph",
            "steps": [
                "read_repository", "scan_source", "classify_logs", "bayesian_update",
                "fuzzy_risk_inference", "retrieve_source_context", "generate_optional_explanations",
                "prioritize_tests", "publish_report",
            ],
            "hypotheses": hypotheses,
            "rankingMethod": (
                "The rule confidence is an uncalibrated prior proxy. Issue-term overlap "
                "and raw supplied-log term overlap produce a documented likelihood ratio "
                "for Bayes' odds updating. "
                "Mamdani fuzzy rules combine severity, detector confidence, and posterior "
                "estimate. The MLP uses bundled synthetic examples; the genetic algorithm "
                "orders discovered test files by likely risk-weighted coverage."
            ),
            "rag": {
                "method": "Local BM25 retrieval over short source-code chunks",
                "sourceFiles": len(state["scan_result"].get("_ragDocuments", [])),
                "note": "An enabled provider receives the issue description, finding details, and top retrieved excerpts for up to five findings; the GitHub token is never included.",
            },
            "aiAnalysis": ai_analysis,
            "usesExternalModel": ai_analysis.get("status") == "complete" and ai_analysis.get("provider") == "gemini",
        }}

    graph = StateGraph(InvestigationState)
    graph.add_node("scan_repository", scan_repository_node)
    graph.add_node("classify_logs", classify_logs_node)
    graph.add_node("rank_evidence", rank_evidence_node)
    graph.add_node("prioritize_tests", prioritize_tests_node)
    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_node("explain_findings", explain_findings_node)
    graph.add_node("publish_report", publish_report_node)
    graph.add_edge(START, "scan_repository")
    graph.add_edge("scan_repository", "classify_logs")
    graph.add_edge("classify_logs", "rank_evidence")
    graph.add_edge("rank_evidence", "retrieve_context")
    graph.add_edge("retrieve_context", "explain_findings")
    graph.add_edge("explain_findings", "prioritize_tests")
    graph.add_edge("prioritize_tests", "publish_report")
    graph.add_edge("publish_report", END)
    result = graph.compile().invoke({"issue_report": issue_report, "log_text": log_text})

    scan_result = result["scan_result"]
    scan_result.pop("_ragDocuments", None)
    scan_result["hypotheses"] = result["hypotheses"]
    scan_result["investigation"] = result["investigation"]
    scan_result["riskAssessment"] = result["riskAssessment"]
    scan_result["logAnalysis"] = result["logAnalysis"]
    scan_result["testPlan"] = result["testPlan"]
    return scan_result
