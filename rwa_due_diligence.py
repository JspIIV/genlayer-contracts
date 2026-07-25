# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json

ERROR_EXPECTED = "[EXPECTED]"
ERROR_EXTERNAL = "[EXTERNAL]"
ERROR_TRANSIENT = "[TRANSIENT]"
ERROR_LLM = "[LLM_ERROR]"


class RWADueDiligence(gl.Contract):
    assets: TreeMap[str, str]
    asset_count: bigint

    def __init__(self) -> None:
        self.asset_count = bigint(0)

    @gl.public.write
    def submit_asset(
        self,
        asset_type: str,
        asset_name: str,
        location: str,
        claimed_value_usd: str,
        description: str,
        evidence_url: str,
    ) -> None:
        asset_id = str(int(self.asset_count))
        self.assets[asset_id] = json.dumps({
            "id": asset_id,
            "asset_type": asset_type,
            "asset_name": asset_name,
            "location": location,
            "claimed_value_usd": claimed_value_usd,
            "description": description,
            "evidence_url": evidence_url,
            "status": "PENDING_VERIFICATION",
            "analysis": None,
        })
        self.asset_count = bigint(int(self.asset_count) + 1)

    @gl.public.write
    def verify_asset(self, asset_id: str) -> None:
        raw = self.assets.get(asset_id, None)
        if raw is None:
            raise gl.vm.UserError(ERROR_EXPECTED + " Asset not found")
        asset = json.loads(raw)
        if asset["status"] != "PENDING_VERIFICATION":
            raise gl.vm.UserError(ERROR_EXPECTED + " Asset is not pending verification")

        asset_type = asset["asset_type"]
        asset_name = asset["asset_name"]
        location = asset["location"]
        claimed_value_usd = asset["claimed_value_usd"]
        description = asset["description"]
        evidence_url = asset["evidence_url"]

        def evaluate() -> str:
            # Contract-side acquisition of authoritative evidence: every validator
            # independently fetches the submitter-provided evidence document
            # (registry page, proof-of-reserve, appraisal, price feed, etc.)
            # rather than trusting the submitter's free-text description alone.
            resp = gl.nondet.web.get(evidence_url)
            if resp.status >= 500:
                raise gl.vm.UserError(ERROR_TRANSIENT + " Evidence source temporarily unavailable")
            if resp.status >= 400:
                raise gl.vm.UserError(ERROR_EXTERNAL + " Evidence source returned status " + str(resp.status))
            evidence_content = resp.body.decode("utf-8", errors="replace")[:6000]

            task = (
                "You are a senior RWA (Real World Asset) due diligence analyst with expertise in\n"
                "asset tokenization. You must ground your assessment in the FETCHED EVIDENCE below,\n"
                "not in the submitter's own description, which may be inaccurate or self-serving.\n\n"
                "ASSET TYPE: " + asset_type + "\n"
                "ASSET NAME: " + asset_name + "\n"
                "LOCATION: " + location + "\n"
                "CLAIMED VALUE (USD): " + claimed_value_usd + "\n"
                "SUBMITTER DESCRIPTION (unverified, treat with skepticism): " + description + "\n\n"
                "FETCHED EVIDENCE (from " + evidence_url + "):\n" + evidence_content + "\n\n"
                "Cross-check the submitter's claims against the fetched evidence. If the evidence does\n"
                "not support the claimed value, ownership, or existence of the asset, this must be\n"
                "reflected as a red flag, a lower valuation, and a stricter verdict.\n\n"
                "Return ONLY a JSON object with this exact structure:\n"
                "{\n"
                "  \"tokenization_verdict\": \"ELIGIBLE\",\n"
                "  \"risk_rating\": \"LOW\",\n"
                "  \"valuation_assessment\": \"FAIR\",\n"
                "  \"red_flags\": [\"flag1\", \"flag2\"],\n"
                "  \"strengths\": [\"strength1\", \"strength2\"],\n"
                "  \"reasoning\": \"two sentence summary citing the fetched evidence\"\n"
                "}\n\n"
                "Rules:\n"
                "- tokenization_verdict must be exactly ELIGIBLE, CONDITIONAL, or NOT_ELIGIBLE\n"
                "- NOT_ELIGIBLE if the fetched evidence contradicts or fails to support the claimed asset/value\n"
                "- risk_rating must be exactly LOW, MEDIUM, or HIGH\n"
                "- valuation_assessment must be exactly UNDERVALUED, FAIR, or OVERVALUED, based on the\n"
                "  fetched evidence, not the submitter's claimed value alone\n"
                "- red_flags: list of 0-5 concerns; must include any mismatch between the submitter's\n"
                "  description and the fetched evidence\n"
                "- strengths: list of 0-3 positive aspects that are actually supported by the evidence\n"
                "- reasoning: exactly two sentences, must reference what the fetched evidence showed\n"
                "Return ONLY the JSON, no other text."
            )
            raw_resp = gl.nondet.exec_prompt(task)
            raw_resp = raw_resp.strip()
            if raw_resp.startswith("```"):
                raw_resp = raw_resp.split("```")[1]
                if raw_resp.startswith("json"):
                    raw_resp = raw_resp[4:]
            raw_resp = raw_resp.strip()
            start = raw_resp.find("{")
            end = raw_resp.rfind("}") + 1
            if start >= 0 and end > start:
                raw_resp = raw_resp[start:end]

            try:
                parsed = json.loads(raw_resp)
            except (ValueError, TypeError):
                raise gl.vm.UserError(ERROR_LLM + " Non-JSON response from model")

            verdict = parsed.get("tokenization_verdict", None)
            if verdict not in ("ELIGIBLE", "CONDITIONAL", "NOT_ELIGIBLE"):
                raise gl.vm.UserError(ERROR_LLM + " Invalid tokenization_verdict: " + str(verdict))

            risk = parsed.get("risk_rating", None)
            if risk not in ("LOW", "MEDIUM", "HIGH"):
                raise gl.vm.UserError(ERROR_LLM + " Invalid risk_rating: " + str(risk))

            valuation = parsed.get("valuation_assessment", None)
            if valuation not in ("UNDERVALUED", "FAIR", "OVERVALUED"):
                raise gl.vm.UserError(ERROR_LLM + " Invalid valuation_assessment: " + str(valuation))

            red_flags = parsed.get("red_flags", [])
            if not isinstance(red_flags, list):
                red_flags = []
            red_flags = [str(f) for f in red_flags][:5]

            strengths = parsed.get("strengths", [])
            if not isinstance(strengths, list):
                strengths = []
            strengths = [str(s) for s in strengths][:3]

            reasoning = str(parsed.get("reasoning", ""))

            return json.dumps({
                "tokenization_verdict": verdict,
                "risk_rating": risk,
                "valuation_assessment": valuation,
                "red_flags": red_flags,
                "strengths": strengths,
                "reasoning": reasoning,
                "evidence_url": evidence_url,
            })

        analysis_str = gl.eq_principle.prompt_comparative(
            evaluate,
            principle=(
                "tokenization_verdict, risk_rating, and valuation_assessment must all match exactly "
                "between validators, since these are the consequential outputs that determine whether "
                "the asset can be tokenized. Wording of red_flags/strengths/reasoning may differ, but "
                "the underlying substance must not contradict between validators."
            ),
        )

        asset["status"] = "VERIFIED"
        asset["analysis"] = json.loads(analysis_str)
        self.assets[asset_id] = json.dumps(asset)

    @gl.public.view
    def get_asset(self, asset_id: str) -> str:
        data = self.assets.get(asset_id, None)
        if data is None:
            return json.dumps({"error": "Asset not found"})
        return data

    @gl.public.view
    def get_all_assets(self) -> str:
        all_assets = {}
        for i in range(int(self.asset_count)):
            aid = str(i)
            all_assets[aid] = json.loads(self.assets.get(aid, "{}"))
        return json.dumps(all_assets)

    @gl.public.view
    def get_total_count(self) -> bigint:
        return self.asset_count
