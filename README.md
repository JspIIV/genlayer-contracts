# GenLayer Intelligent Contracts

A collection of intelligent contracts built on [GenLayer](https://genlayer.com) testnet — combining on-chain state with decentralized AI consensus.

## Contracts

### 1. On-Chain Fact Checker
Evaluates any claim using a decentralized network of AI validators and returns a tamper-proof verdict.

**Verdicts:** `TRUE` · `FALSE` · `UNCERTAIN`

```python
check_claim("The Earth is the third planet from the Sun")
# → { "verdict": "TRUE", "explanation": "Earth orbits at the third position..." }
```

### 2. AI Dispute Resolver
Submit both sides of any dispute. Independent AI validators read the arguments and reach consensus on a ruling — stored permanently on-chain.

**Rulings:** `PARTY_A` · `PARTY_B` · `DRAW`

```python
submit_dispute(
    title="Freelancer Payment Dispute",
    party_a_name="Client",
    party_a_argument="Delivered 5 weeks late with buggy code...",
    party_b_name="Freelancer",
    party_b_argument="Client kept changing requirements..."
)
# → { "winner": "DRAW", "confidence": "MEDIUM", "reasoning": "..." }
```

## Why GenLayer?

Traditional smart contracts can only work with deterministic data. GenLayer's intelligent contracts unlock **subjective reasoning** — multiple validator nodes run the same AI prompt independently, and only reach finality when they agree. This makes it possible to build:

- Fact-checking systems that can't be manipulated
- Dispute resolution without centralized arbitrators
- Any use case where AI judgment needs to be trustless

## Stack

- **Language:** Python (GenLayer SDK)
- **Runtime:** GenVM (`py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`)
- **Consensus:** `gl.eq_principle.prompt_comparative`
- **Storage:** `TreeMap`, `bigint`
- **Network:** GenLayer testnet
