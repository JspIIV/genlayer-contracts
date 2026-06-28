# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


class RWADueDiligence(gl.Contract):
    assets: TreeMap[str, str]
    asset_count: bigint

    def __init__(self) -> None:
        self.asset_count = bigint(0)

    @gl.public.write
    def analyze_asset(
        self,
        asset_type: str,
        asset_name: str,
        location: str,
        claimed_value_usd: str,
        description: str,
        documentation_summary: str,
    ) -> None:
        def evaluate() -> str:
            task = (
                "You are a senior RWA (Real World Asset) due diligence analyst with expertise in asset tokenization.\n"
                "Analyze the following asset and provide a comprehensive evaluation for blockchain tokenization.\n\n"
                "ASSET TYPE: " + asset_type + "\n"
                "ASSET NAME: " + asset_name + "\n"
                "LOCATION: " + location + "\n"
                "CLAIMED VALUE (USD): " + claimed_value_usd + "\n"
                "DESCRIPTION: " + description + "\n"
                "DOCUMENTATION SUMMARY: " + documentation_summary + "\n\n"
                "Return ONLY a JSON object with this exact structure:\n"
                "{\n"
                "  \"tokenization_verdict\": \"ELIGIBLE\",\n"
                "  \"risk_rating\": \"LOW\",\n"
                "  \"valuation_assessment\": \"FAIR\",\n"
                "  \"red_flags\": [\"flag1\", \"flag2\"],\n"
                "  \"strengths\": [\"strength1\", \"strength2\"],\n"
                "  \"reasoning\": \"two sentence summary\"\n"
                "}\n\n"
                "Rules:\n"
                "- tokenization_verdict must be exactly ELIGIBLE, CONDITIONAL, or NOT_ELIGIBLE\n"
                "- ELIGIBLE: asset is suitable for tokenization as described\n"
                "- CONDITIONAL: asset needs additional verification or conditions before tokenization\n"
                "- NOT_ELIGIBLE: asset has critical issues preventing tokenization\n"
                "- risk_rating must be exactly LOW, MEDIUM, or HIGH\n"
                "- valuation_assessment must be exactly UNDERVALUED, FAIR, or OVERVALUED\n"
                "- red_flags: list of 0-3 concerns, empty array if none\n"
                "- strengths: list of 1-3 positive aspects\n"
                "- reasoning: exactly two sentences explaining the verdict\n"
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

            verdict = parsed.get("tokenization_verdict", "CONDITIONAL")
            if verdict not in ("ELIGIBLE", "CONDITIONAL", "NOT_ELIGIBLE"):
                verdict = "CONDITIONAL"

            risk = parsed.get("risk_rating", "MEDIUM")
            if risk not in ("LOW", "MEDIUM", "HIGH"):
                risk = "MEDIUM"

            valuation = parsed.get("valuation_assessment", "FAIR")
            if valuation not in ("UNDERVALUED", "FAIR", "OVERVALUED"):
                valuation = "FAIR"

            red_flags = parsed.get("red_flags", [])
            if not isinstance(red_flags, list):
                red_flags = []

            strengths = parsed.get("strengths", [])
            if not isinstance(strengths, list):
                strengths = []

            reasoning = str(parsed.get("reasoning", ""))

            return json.dumps({
                "tokenization_verdict": verdict,
                "risk_rating": risk,
                "valuation_assessment": valuation,
                "red_flags": red_flags,
                "strengths": strengths,
                "reasoning": reasoning,
            })

        analysis_str = gl.eq_principle.prompt_comparative(
            evaluate,
            principle="The tokenization_verdict and risk_rating fields must match between validators."
        )

        asset_id = str(int(self.asset_count))
        self.assets[asset_id] = json.dumps({
            "id": asset_id,
            "asset_type": asset_type,
            "asset_name": asset_name,
            "location": location,
            "claimed_value_usd": claimed_value_usd,
            "description": description,
            "documentation_summary": documentation_summary,
            "analysis": json.loads(analysis_str),
        })
        self.asset_count = bigint(int(self.asset_count) + 1)

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
