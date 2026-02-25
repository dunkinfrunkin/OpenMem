"""LLM-based answer evaluation.

Uses OpenAI to judge whether the agent's answer is correct,
complete, and free of hallucinations.
"""
from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class JudgeResult:
    correctness: float  # 0-1: does it contain the right info?
    completeness: float  # 0-1: does it cover all key facts?
    no_hallucination: float  # 0-1: does it avoid stating wrong info?
    key_facts_found: list[str]
    key_facts_missing: list[str]
    overall: float  # weighted average
    reasoning: str = ""


JUDGE_PROMPT = """\
You are an expert evaluator. Judge whether the ACTUAL ANSWER correctly answers the QUESTION based on the EXPECTED ANSWER and KEY FACTS.

QUESTION:
{question}

EXPECTED ANSWER:
{expected_answer}

KEY FACTS (these should appear in a correct answer):
{key_facts}

ACTUAL ANSWER:
{actual_answer}

Evaluate the actual answer on three dimensions:
1. **correctness** (0.0-1.0): Does the answer contain accurate information that aligns with the expected answer? 1.0 = fully correct, 0.0 = completely wrong.
2. **completeness** (0.0-1.0): Does the answer cover all the key facts listed? 1.0 = all facts present, 0.0 = none present.
3. **no_hallucination** (0.0-1.0): Does the answer avoid stating incorrect information not supported by the expected answer? 1.0 = no hallucinations, 0.0 = significant false claims.

Also list which key facts were found and which were missing.

Respond with ONLY valid JSON in this exact format:
{{"correctness": 0.0, "completeness": 0.0, "no_hallucination": 0.0, "key_facts_found": [], "key_facts_missing": [], "reasoning": "brief explanation"}}
"""


def judge_answer(
    question: str,
    expected_answer: str,
    key_facts: list[str],
    actual_answer: str,
    model: str = "gpt-4o-mini",
) -> JudgeResult:
    from openai import OpenAI

    client = OpenAI()

    prompt = JUDGE_PROMPT.format(
        question=question,
        expected_answer=expected_answer,
        key_facts="\n".join(f"- {f}" for f in key_facts),
        actual_answer=actual_answer,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return JudgeResult(
            correctness=0.0,
            completeness=0.0,
            no_hallucination=0.0,
            key_facts_found=[],
            key_facts_missing=key_facts,
            overall=0.0,
            reasoning=f"Failed to parse judge response: {content[:200]}",
        )

    correctness = float(data.get("correctness", 0.0))
    completeness = float(data.get("completeness", 0.0))
    no_hallucination = float(data.get("no_hallucination", 0.0))
    found = data.get("key_facts_found", [])
    missing = data.get("key_facts_missing", [])
    reasoning = data.get("reasoning", "")

    # Weighted average: correctness matters most
    overall = 0.5 * correctness + 0.3 * completeness + 0.2 * no_hallucination

    return JudgeResult(
        correctness=correctness,
        completeness=completeness,
        no_hallucination=no_hallucination,
        key_facts_found=found,
        key_facts_missing=missing,
        overall=overall,
        reasoning=reasoning,
    )
