# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


class FactChecker(gl.Contract):
    claims: TreeMap[str, str]
    claim_count: bigint

    def __init__(self) -> None:
        self.claim_count = bigint(0)

    @gl.public.write
    def check_claim(self, claim: str) -> None:
        def analyze() -> str:
            task = (
                "You are an expert fact-checker with broad knowledge.\n"
                "Evaluate the following claim and return ONLY a JSON object.\n\n"
                "CLAIM: \"" + claim + "\"\n\n"
                "Return exactly this JSON structure:\n"
                "{\"verdict\": \"TRUE\", \"explanation\": \"one sentence reason\"}\n\n"
                "Rules:\n"
                "- verdict must be exactly TRUE, FALSE, or UNCERTAIN\n"
                "- Use TRUE if the claim is clearly correct\n"
                "- Use FALSE if the claim is clearly wrong\n"
                "- Use UNCERTAIN if you cannot be sure\n"
                "- explanation must be one sentence only\n"
                "Return ONLY the JSON, no other text."
            )
            raw = gl.nondet.exec_prompt(task)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                raw = raw[start:end]
            parsed = json.loads(raw)
            verdict = parsed.get("verdict", "UNCERTAIN")
            if verdict not in ("TRUE", "FALSE", "UNCERTAIN"):
                verdict = "UNCERTAIN"
            explanation = str(parsed.get("explanation", ""))
            return json.dumps({"verdict": verdict, "explanation": explanation})

        result_str = gl.eq_principle.prompt_comparative(
            analyze,
            principle="The verdict field must match: both must agree on TRUE, FALSE, or UNCERTAIN."
        )

        claim_id = str(int(self.claim_count))
        self.claims[claim_id] = json.dumps({
            "id": claim_id,
            "claim": claim,
            "result": json.loads(result_str),
        })
        self.claim_count = bigint(int(self.claim_count) + 1)

    @gl.public.view
    def get_result(self, claim_id: str) -> str:
        data = self.claims.get(claim_id, None)
        if data is None:
            return json.dumps({"error": "Claim not found"})
        return data

    @gl.public.view
    def get_all_claims(self) -> str:
        all_claims = {}
        for i in range(int(self.claim_count)):
            cid = str(i)
            all_claims[cid] = json.loads(self.claims.get(cid, "{}"))
        return json.dumps(all_claims)

    @gl.public.view
    def get_total_count(self) -> bigint:
        return self.claim_count
