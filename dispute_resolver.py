# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


class DisputeResolver(gl.Contract):
    disputes: TreeMap[str, str]
    dispute_count: bigint

    def __init__(self) -> None:
        self.dispute_count = bigint(0)

    @gl.public.write
    def submit_dispute(
        self,
        title: str,
        party_a_name: str,
        party_a_argument: str,
        party_b_name: str,
        party_b_argument: str,
    ) -> None:
        def resolve() -> str:
            task = (
                "You are an impartial AI judge. Read both sides of the dispute and give a fair ruling.\n\n"
                "DISPUTE: \"" + title + "\"\n\n"
                "PARTY A (" + party_a_name + "):\n" + party_a_argument + "\n\n"
                "PARTY B (" + party_b_name + "):\n" + party_b_argument + "\n\n"
                "Return ONLY a JSON object with this exact structure:\n"
                "{\"winner\": \"PARTY_A\", \"reasoning\": \"one paragraph explanation\", \"confidence\": \"HIGH\"}\n\n"
                "Rules:\n"
                "- winner must be exactly PARTY_A, PARTY_B, or DRAW\n"
                "- Use PARTY_A if their argument is stronger\n"
                "- Use PARTY_B if their argument is stronger\n"
                "- Use DRAW if both sides are equally valid\n"
                "- confidence must be HIGH, MEDIUM, or LOW\n"
                "- reasoning must be 1-2 sentences, strictly neutral and fair\n"
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
            winner = parsed.get("winner", "DRAW")
            if winner not in ("PARTY_A", "PARTY_B", "DRAW"):
                winner = "DRAW"
            confidence = parsed.get("confidence", "MEDIUM")
            if confidence not in ("HIGH", "MEDIUM", "LOW"):
                confidence = "MEDIUM"
            reasoning = str(parsed.get("reasoning", ""))
            return json.dumps({
                "winner": winner,
                "winner_name": party_a_name if winner == "PARTY_A" else (party_b_name if winner == "PARTY_B" else "DRAW"),
                "confidence": confidence,
                "reasoning": reasoning,
            })

        ruling_str = gl.eq_principle.prompt_comparative(
            resolve,
            principle="The winner field must match: both must agree on PARTY_A, PARTY_B, or DRAW."
        )

        dispute_id = str(int(self.dispute_count))
        self.disputes[dispute_id] = json.dumps({
            "id": dispute_id,
            "title": title,
            "party_a": {"name": party_a_name, "argument": party_a_argument},
            "party_b": {"name": party_b_name, "argument": party_b_argument},
            "ruling": json.loads(ruling_str),
        })
        self.dispute_count = bigint(int(self.dispute_count) + 1)

    @gl.public.view
    def get_dispute(self, dispute_id: str) -> str:
        data = self.disputes.get(dispute_id, None)
        if data is None:
            return json.dumps({"error": "Dispute not found"})
        return data

    @gl.public.view
    def get_all_disputes(self) -> str:
        all_disputes = {}
        for i in range(int(self.dispute_count)):
            cid = str(i)
            all_disputes[cid] = json.loads(self.disputes.get(cid, "{}"))
        return json.dumps(all_disputes)

    @gl.public.view
    def get_total_count(self) -> bigint:
        return self.dispute_count
