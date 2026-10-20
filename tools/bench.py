#!/usr/bin/env python3
"""Measure this engine on the four axes that matter, in a throwaway vault.

    python3 tools/bench.py              # markdown table, ~40 s, offline
    python3 tools/bench.py --json
    python3 tools/bench.py --notes 500  # bigger vault

Why these axes and not a published score: LoCoMo and LongMemEval were built for 32k context
windows, a plain "dump everything into the prompt" baseline now scores competitively on them,
their headline numbers are mostly vendor-reported, and an independent audit found answer-key
errors — so a number from them would say little about this engine and nothing anyone could
reproduce. Hindsight's benchmark manifesto argues for accuracy *with* speed, cost, usability
and reproducibility together; the cost-aware evaluation in arXiv:2609.05441 adds that the
interesting question is utility per dollar against full replay. That is what this measures,
offline, on your machine, with no API key and no judge model:

  accuracy  — retrieval hit@1 / hit@3 over a seeded vault of near-duplicate notes
  cost      — characters and estimated tokens a session start injects, vs. replaying everything
  speed     — wall-clock latency of the hooks that run on every session and every prompt
  usability — dependencies, infrastructure and the number of commands to install

Sources: https://hindsight.vectorize.io/blog/2026/03/23/agent-memory-benchmark ·
https://arxiv.org/abs/2609.05441 · https://arxiv.org/abs/2501.13956
"""
import argparse
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENGINE = REPO / "engine" / "humona.py"
CHARS_PER_TOKEN = 4  # rough, and the same divisor is applied to every number below

SERVICES = ["billing", "ingest", "gateway", "scheduler", "notifier", "search", "ledger", "render",
            "auth", "export", "importer", "webhook", "digest", "replay", "archive"]
STORES = ["Postgres 16", "SQLite WAL", "Redis streams", "S3 + manifest", "DynamoDB", "ClickHouse"]
REGIONS = ["eu-central-1", "eu-west-3", "us-east-1", "ap-south-1"]
TOPICS = ["retry policy", "rate limit", "cache ttl", "migration order", "backfill window"]

# The same task in scripts that are written without spaces, where the index falls back to
# character bigrams. Worth measuring rather than asserting: "it returns something" and "it returns
# the right note out of forty near-identical ones" are different claims.      # i18n-data
LANGS = {
    "japanese": (["請求", "配送", "在庫", "認証", "通知", "検索", "台帳", "描画"],
                 ["再試行方針", "レート制限", "キャッシュ期限", "移行順序", "補充期間"],
                 "%sサービスの%sはプラットフォームチームと合意した。変更には移行メモが必要である。",
                 "%sサービスの%sはどこで決まったか"),
    "chinese": (["计费", "接入", "网关", "调度", "通知", "搜索", "账本", "渲染"],
                ["重试策略", "速率限制", "缓存时效", "迁移顺序", "回填窗口"],
                "%s服务的%s由平台团队共同商定，未经迁移说明不得更改。",
                "%s服务的%s是怎么定的"),
    "korean": (["결제", "수집", "게이트웨이", "스케줄러", "알림", "검색", "원장", "렌더"],
               ["재시도 정책", "속도 제한", "캐시 만료", "마이그레이션 순서", "백필 기간"],
               "%s 서비스의 %s은 플랫폼 팀과 합의되었으며 마이그레이션 노트 없이 변경할 수 없다.",
               "%s 서비스의 %s은 어디서 정해졌나"),
    "russian": (["биллинг", "приём", "шлюз", "планировщик", "уведомления", "поиск", "реестр", "рендер"],
                ["политика повторов", "ограничение скорости", "время жизни кэша",
                 "порядок миграции", "окно дозаполнения"],
                "%s: %s согласована с платформенной командой и не меняется без заметки о миграции.",
                "где согласована %s для сервиса %s"),
}


BODY = ("The %s service stores its state in %s and runs in %s. Its %s was agreed with the platform "
        "team and must not be changed without a migration note. Every service in this fleet keeps "
        "the same shape of record, so the only thing that tells them apart is the service name and "
        "the decision itself.")


def write(d, name, title, body):
    (d / (name + ".md")).write_text(
        "---\ntitle: \"%s\"\ntype: semantic\nproject: global\ncreated: 2026-01-01\n"
        "recall_count: 0\ntags: [semantic]\n---\n# %s\n\n%s\n" % (title, title, body), encoding="utf-8")


def seed(vault, n, rng):
    """Notes that share every word except the fact itself — discrimination among near-duplicates,
    which is what separates a memory from a grep.

    Each (service, topic) pair is written exactly once, so every query has exactly one correct
    answer; a vault larger than the number of pairs is filled with distractors that use the same
    boilerplate and a disjoint vocabulary, so they can crowd the ranking without ever being a
    legitimate answer. Scoring a question that several notes answer equally well would make hit@1
    look bad for being right, which is how a benchmark ends up lying in your favour or against you.
    """
    d = vault / "memory" / "3-LongTerm" / "Semantic"
    d.mkdir(parents=True, exist_ok=True)
    pairs = [(s, t) for s in SERVICES for t in TOPICS]
    rng.shuffle(pairs)
    truth = []
    for svc, topic in pairs[:n]:
        store, region = rng.choice(STORES), rng.choice(REGIONS)
        name = "service-%s-%s" % (svc, topic.replace(" ", "-"))
        write(d, name, "%s %s" % (svc, topic), BODY % (svc, store, region, topic))
        truth.append({"note": name, "svc": svc, "store": store, "region": region, "topic": topic})
    for i in range(max(0, n - len(pairs))):   # distractors: same shape, no overlap with any answer
        write(d, "fleet-decision-%d" % i, "fleet decision %d" % i,
              BODY % ("worker-%d" % i, rng.choice(STORES), rng.choice(REGIONS),
                      "shutdown order %d" % i))
    return truth


def language_accuracy(lang, env, cwd, rng, queries, vault):
    """hit@k for one language, one correct answer per question by construction."""
    svcs, topics, body_t, q_t = LANGS[lang]
    d = vault / "memory" / "3-LongTerm" / "Semantic"
    for p in d.glob("*.md"):
        p.unlink()
    pairs = [(s, t) for s in svcs for t in topics]
    for i, (s, t) in enumerate(pairs):
        body = body_t % ((t, s) if lang == "russian" else (s, t))
        write(d, "lang-%d" % i, "%s %s" % (s, t), body)
    run(["reindex"], env, cwd)
    sample = rng.sample(list(enumerate(pairs)), min(queries, len(pairs)))
    h1 = h3 = 0
    for i, (s, t) in sample:
        q = q_t % ((t, s) if lang == "russian" else (s, t))
        r = run(["search", q, "-k", 3, "--json", "--keyword"], env, cwd)
        try:
            got = [h.get("path", "") for h in json.loads(r.stdout).get("results", [])]
        except ValueError:
            got = []
        want = "lang-%d.md" % i
        h1 += 1 if got and want in got[0] else 0
        h3 += 1 if any(want in g for g in got) else 0
    return {"notes": len(pairs), "queries": len(sample),
            "hit@1": round(h1 / len(sample), 3), "hit@3": round(h3 / len(sample), 3)}


def run(args, env, cwd, stdin=""):
    return subprocess.run([sys.executable, str(ENGINE)] + [str(a) for a in args], input=stdin,
                          capture_output=True, text=True, env=env, cwd=str(cwd), timeout=120)


def timed(fn, repeat):
    ts = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t0) * 1000)
    return {"p50_ms": round(statistics.median(ts), 1),
            "p95_ms": round(sorted(ts)[max(0, int(len(ts) * 0.95) - 1)], 1)}


def grep_baseline(vault, q, k=3):
    """What a naive 'grep the notes and count the words' retrieval returns, so the engine's hit
    rate can be read against something. This is the honest floor: no idf, no field weighting,
    no recency — the thing people reach for before they build a memory."""
    words = [w for w in re.findall(r"[a-z0-9]+", q.lower()) if len(w) > 2]
    scored = []
    for p in (vault / "memory").rglob("*.md"):
        t = p.read_text(encoding="utf-8").lower()
        scored.append((sum(t.count(w) for w in words), p.name))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [n for s, n in scored[:k] if s]


def accuracy(truth, vault, env, cwd, rng, queries, keyword_only=True):
    """hit@k on two query styles, reported separately because they fail differently:
    named   — the question mentions the thing by name, which is how an agent usually asks
    blind   — the question describes it without the name, where keyword search has nothing to grip

    Search runs with --keyword so the result does not depend on the optional embedding venv; with
    it installed the blind row is the one that moves.
    """
    out = {}
    for style in ("named", "blind"):
        hits = {"engine": [0, 0], "grep": [0, 0]}
        sample = rng.sample(truth, min(queries, len(truth)))
        for t in sample:
            q = ("where does the %s service keep its %s" % (t["svc"], t["topic"]) if style == "named"
                 else "which service agreed its %s with the platform team in %s" % (t["topic"], t["region"]))
            args = ["search", q, "-k", 3, "--json"] + (["--keyword"] if keyword_only else [])
            r = run(args, env, cwd)
            try:
                got = [h.get("path", "") for h in json.loads(r.stdout).get("results", [])]
            except ValueError:
                got = []
            for name, ranked in (("engine", got), ("grep", grep_baseline(vault, q))):
                hits[name][0] += 1 if ranked and t["note"] in ranked[0] else 0
                hits[name][1] += 1 if any(t["note"] in g for g in ranked) else 0
        out[style] = {"queries": len(sample)}
        for name, (h1, h3) in hits.items():
            out[style][name] = {"hit@1": round(h1 / len(sample), 3), "hit@3": round(h3 / len(sample), 3)}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--notes", type=int, default=300)
    ap.add_argument("--queries", type=int, default=40)
    ap.add_argument("--repeat", type=int, default=15)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--languages", action="store_true",
                    help="also measure retrieval in Japanese, Chinese, Korean and Russian")
    ap.add_argument("--semantic", action="store_true",
                    help="also measure with the optional embedding layer (needs `humona semantic install`)")
    a = ap.parse_args()

    rng = random.Random(a.seed)
    tmp = Path(tempfile.mkdtemp(prefix="brain-bench-"))
    vault, state = tmp / "vault", tmp / "state"
    env = dict(os.environ, HUMONA_VAULT=str(vault), HUMONA_STATE=str(state),
               BRAIN_CC_PROJECTS=str(tmp / "cc"), BRAIN_NO_SYNC="1")
    env.pop("VIRTUAL_ENV", None)
    try:
        run(["init"], env, tmp)
        truth = seed(vault, a.notes, rng)
        run(["reindex"], env, tmp)
        run(["index"], env, tmp)

        ctx = run(["context"], env, tmp, stdin="{}").stdout
        full = sum(len(p.read_text(encoding="utf-8")) for p in (vault / "memory").rglob("*.md"))
        res = {
            "notes": a.notes,
            "cost": {
                "session_start_chars": len(ctx),
                "session_start_tokens_est": round(len(ctx) / CHARS_PER_TOKEN),
                "full_replay_chars": full,
                "full_replay_tokens_est": round(full / CHARS_PER_TOKEN),
                "ratio": round(full / max(len(ctx), 1), 1),
            },
            "speed": {
                "session_start_hook": timed(lambda: run(["context"], env, tmp, stdin="{}"), a.repeat),
                "per_prompt_hook": timed(
                    lambda: run(["hint"], env, tmp, stdin=json.dumps({"prompt": "where does billing keep state"})),
                    a.repeat),
                "search": timed(lambda: run(["search", "retry policy", "--keyword"], env, tmp), a.repeat),
            },
            "accuracy": accuracy(truth, vault, env, tmp, rng, a.queries),
            "accuracy_semantic": (accuracy(truth, vault, env, tmp, random.Random(a.seed), a.queries,
                                           keyword_only=False) if a.semantic else None),
            "usability": {
                "runtime_dependencies": 0,
                "python": ">=3.8 (standard library only)",
                "services_required": "none (no database, no vector store, no API key)",
                "install_commands": 2,
                "offline": True,
            },
            "reproduce": "python3 tools/bench.py --notes %d --queries %d --seed %d%s"
                         % (a.notes, a.queries, a.seed,
                            ("" if not a.semantic else " --semantic") + ("" if not a.languages else " --languages")),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if a.languages:
        res["languages"] = {}
        tmp2 = Path(tempfile.mkdtemp(prefix="brain-bench-lang-"))
        try:
            v2, s2 = tmp2 / "vault", tmp2 / "state"
            env2 = dict(env, HUMONA_VAULT=str(v2), HUMONA_STATE=str(s2))
            run(["init"], env2, tmp2)
            (v2 / "memory" / "3-LongTerm" / "Semantic").mkdir(parents=True, exist_ok=True)
            for lang in LANGS:
                res["languages"][lang] = language_accuracy(lang, env2, tmp2, random.Random(a.seed),
                                                           a.queries, v2)
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    c, s, acc = res["cost"], res["speed"], res["accuracy"]
    print("# brain bench — %d notes, seed %d, offline\n" % (a.notes, a.seed))
    print("| axis | measure | value |")
    print("|---|---|---|")
    print("| cost | session start injects | %s chars ≈ %s tokens |"
          % (c["session_start_chars"], c["session_start_tokens_est"]))
    print("| cost | replaying every note would cost | %s chars ≈ %s tokens (%.0f×) |"
          % (c["full_replay_chars"], c["full_replay_tokens_est"], c["ratio"]))
    print("| speed | session-start hook | %.0f ms p50 · %.0f ms p95 |"
          % (s["session_start_hook"]["p50_ms"], s["session_start_hook"]["p95_ms"]))
    print("| speed | per-prompt hook | %.0f ms p50 · %.0f ms p95 |"
          % (s["per_prompt_hook"]["p50_ms"], s["per_prompt_hook"]["p95_ms"]))
    print("| speed | search | %.0f ms p50 · %.0f ms p95 |"
          % (s["search"]["p50_ms"], s["search"]["p95_ms"]))
    for style, label in (("named", "question names the thing"), ("blind", "question only describes it")):
        e, g = acc[style]["engine"], acc[style]["grep"]
        print("| accuracy | hit@1 / hit@3 — %s | **%.2f / %.2f**  (naive grep: %.2f / %.2f, n=%d) |"
              % (label, e["hit@1"], e["hit@3"], g["hit@1"], g["hit@3"], acc[style]["queries"]))
    if res.get("accuracy_semantic"):
        for style, label in (("named", "question names the thing"), ("blind", "question only describes it")):
            e = res["accuracy_semantic"][style]["engine"]
            print("| accuracy | hit@1 / hit@3 — %s, **embeddings on** | **%.2f / %.2f** (n=%d) |"
                  % (label, e["hit@1"], e["hit@3"], res["accuracy_semantic"][style]["queries"]))
    for lang, r in (res.get("languages") or {}).items():
        print("| accuracy | hit@1 / hit@3 — **%s**, %d near-identical notes | **%.2f / %.2f** (n=%d) |"
              % (lang, r["notes"], r["hit@1"], r["hit@3"], r["queries"]))
    print("| usability | runtime dependencies · services | 0 · none |")
    print("\nReproduce: `%s`" % res["reproduce"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
