"""Write precedence-telemetry.json: the run's tokens by model, reasoning effort, phase and agent, and its active time.

Usage:
  python3 -I -X utf8 run_telemetry.py <preprint dir> --skill-commit <commit> [--skill-commit <commit> ...]
      [--session <id> ...] (--no-deviations | --deviations [DEVIATION OPTIONS]) [--dry-run]
  python3 -I -X utf8 run_telemetry.py <preprint dir> --skill-commit <commit> --usage-unavailable "<harness>"
      (--no-deviations | --deviations [DEVIATION OPTIONS]) [--dry-run]

Deviation options, each repeatable, for the tokens the deviations from the procedure added (extra) and saved:
  --extra <agent>[=<share>]     an agent's tokens, or the share (0 to 1) of them that a deviation added
  --saved <agent>[=<factor>]    an agent's tokens times a factor: what a skipped step would have cost
  --extra-tokens / --saved-tokens <kind>=<count>[,<kind>=<count>...]   an estimate made otherwise,
                                for example cache_read=40M,output=0.3M (kinds as in FIELDS)
  --extra unknown / --saved unknown   part of the effect could not be estimated
  <agent> is the number --dry-run lists it under (0 is the coordinator), or its label, with #<n> for the
  n-th agent of that label.

- Reads Claude Code's session transcripts: <config>/projects/*/<session>.jsonl for the coordinator, and
  <config>/projects/*/<session>/subagents/ for its subagents, where <config> is $CLAUDE_CONFIG_DIR or
  ~/.claude. The sessions are those given with --session, or else the current one ($CLAUDE_CODE_SESSION_ID).
  It stops if a session's transcript is missing (Claude Code deletes them after cleanupPeriodDays, 30 by
  default); the telemetry is then left out.
- Each API request counts once, by its message id, so a forked or resumed session's copied history is not
  counted twice. Requests Claude Code makes for itself, such as context compaction, are not in the
  transcripts; compactions are counted, not measured.
- A subagent's phase is the pass its label starts with, as a whole word ("section: §3 ...", "draft: <slug>";
  see PHASES and ALIASES); otherwise "other". An agent launched by a subagent takes its parent's phase, and
  its parent's label with "(helper)". The coordinator is one row.
- Active time is the union of the time each agent was waiting on a model response or running a tool, so
  agents working in parallel count once. Left out: the time after an agent ends its turn, hands back or
  hits a usage limit, until its next message; any gap that ends in a message that isn't a tool result (a
  prompt, a notification, a command) or in a permission answer from the user; questions to the user; and
  any gap over GAP_MINUTES between consecutive entries of one transcript, such as a suspended computer.
  Shorter pauses are counted.
- --usage-unavailable writes null usage and time, for a harness without such transcripts.
- Writes <preprint dir>/precedence-telemetry.json. --dry-run writes nothing, and prints the numbered agents
  with their tokens, and the deviation sums. Agent labels that look like a path, an email address or an ID
  are withheld; other label text is published as written. Model names other than plain Claude model ids
  are reported, to be pointed out to the user.
"""
import argparse
import collections
import datetime
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
FORMAT, VERSION = "math-lineage/precedence-telemetry", 1
GAP_MINUTES = 10
WAIT_TOOLS = {"AskUserQuestion", "ExitPlanMode", "SubagentHandback"}
TIMELINE_TYPES = {"user", "assistant", "attachment", "system"}
FIELDS = ["input_uncached", "cache_write_5m", "cache_write_1h", "cache_read", "output"]
PHASES = ["section", "credit map", "consolidation", "draft", "persona check", "apply", "publish", "other"]
PER_FINDING = {"draft", "persona check", "apply"}
ALIASES = {"author check": "persona check", "author-persona check": "persona check"}
PRIVATE = re.compile(r"[\w.+-]+@[\w-]+\.\w"  # email address
                     r"|[A-Za-z]:[\\/]|\\\\\w|~[\\/]"  # drive, UNC or home path
                     r"|(^|[\s(\"'])/?(Users|home|tmp|mnt|var|root|private|c)/"  # other paths
                     r"|\b[0-9a-f]{8}-[0-9a-f]{4}\b|[0-9a-f]{16,}", re.I)  # UUID, or a long hex id
PLAIN_MODEL = re.compile(r"claude-[a-z0-9.-]+")
DEFINITIONS = {
    "tokens": "Summed over the API requests recorded in the session transcripts of the coordinator and its "
              "subagents; each request counts once. Requests Claude Code makes for itself, such as context "
              "compaction, permission checks and page summaries, are not recorded there and are not included.",
    "input_uncached": "Input tokens neither read from nor written to the prompt cache.",
    "cache_write_5m": "Input tokens written to the prompt cache with a 5-minute lifetime. Cache writes in "
                      "transcripts that don't give the lifetime (older Claude Code versions) are counted here.",
    "cache_write_1h": "Input tokens written to the prompt cache with a 1-hour lifetime.",
    "cache_read": "Input tokens read from the prompt cache.",
    "output": "Output tokens, including reasoning tokens.",
    "active_hours": "Wall-clock hours during which at least one of the agents counted was waiting on a model "
                    "response or running a tool; agents working in parallel count once. Left out: the time "
                    "after an agent ended its turn, handed back or hit a usage limit, until its next message; "
                    "waiting for the user; and any gap over "
                    f"{GAP_MINUTES} minutes between consecutive entries of one agent's transcript, such as a "
                    "suspended computer. Shorter pauses are counted.",
    "phase": "The pass a subagent ran: section (section passes), credit map (companion credit map), "
             "consolidation, draft (drafting and redrafting findings), persona check (author-persona "
             "checks), apply (applying their verdicts), publish (publishing steps such as the JSON), or "
             "other. A helper launched by a subagent counts in its parent's phase. The coordinator's own "
             "requests, across all passes, are the phase coordinator.",
    "by_agent": "One row per subagent, in launch order, labelled by the description it was launched with; a "
                "helper launched by a subagent is labelled after its parent. A resumed subagent's later "
                "work stays in its row. finding is the slug, in precedence-findings.json, of the one finding "
                "the label names, or null.",
    "procedure_deviations": "True when the run departed from the skill's procedure in a way that could "
                            "change its cost or its findings.",
    "deviation_extra_tokens": "The coordinator's estimate, by kind, of the tokens that the deviations added, "
                              "such as work redone, relaunched or run as a test: the agents it names, or the "
                              "share of an agent's work it judged extra, plus any estimate it made otherwise. "
                              "includes_unknown is true when part of the effect could not be estimated and "
                              "is left out.",
    "deviation_saved_tokens": "The coordinator's estimate, by kind, of the tokens that the deviations saved, "
                              "such as steps skipped or shortened, or work taken from an earlier run: "
                              "multiples of comparable agents of this run, plus any estimate it made "
                              "otherwise. includes_unknown as above.",
}


def count(s):
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([kMB]?)", s.strip())
    if not m:
        raise ValueError(f"not a token count: {s!r} (use e.g. 4500000, 4.5M or 450k)")
    return float(m.group(1)) * {"": 1, "k": 1e3, "M": 1e6, "B": 1e9}[m.group(2)]


def kinds(spec):
    """{field: count} from 'cache_read=40M,output=0.3M'."""
    out = dict.fromkeys(FIELDS, 0.0)
    for part in spec.split(","):
        k, _, v = part.partition("=")
        if k.strip() not in FIELDS:
            raise ValueError(f"unknown kind {k.strip()!r} in {spec!r}; the kinds are {', '.join(FIELDS)}")
        out[k.strip()] += count(v)
    return out


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("preprint")
ap.add_argument("--skill-commit", action="append", required=True)
source = ap.add_mutually_exclusive_group()
source.add_argument("--session", action="append", default=[])
source.add_argument("--usage-unavailable", metavar="HARNESS")
ap.add_argument("--deviations", action="store_true")
ap.add_argument("--no-deviations", action="store_true")
for side in ("extra", "saved"):
    ap.add_argument(f"--{side}", action="append", default=[], metavar="AGENT[=N]")
    ap.add_argument(f"--{side}-tokens", action="append", default=[], metavar="KIND=COUNT[,...]")
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
unavailable = a.usage_unavailable is not None

problems = []
if a.deviations == a.no_deviations:
    problems.append("give either --deviations (with the deviation options) or --no-deviations")
if a.no_deviations and (a.extra or a.saved or a.extra_tokens or a.saved_tokens):
    problems.append("the deviation options go with --deviations, not --no-deviations")
for spec in a.extra_tokens + a.saved_tokens:
    try:
        kinds(spec)
    except ValueError as err:
        problems.append(str(err))
if unavailable and any(r.strip().lower() != "unknown" for r in a.extra + a.saved):
    problems.append("with --usage-unavailable there are no agents to name; use --extra-tokens or --saved-tokens")
for c in a.skill_commit:
    if not re.fullmatch(r"[0-9a-f]{7,40}", c):
        problems.append(f"not a commit hash: {c!r}")
if unavailable and (not a.usage_unavailable.strip() or PRIVATE.search(a.usage_unavailable)):
    problems.append("give the harness and its version, with no path, email address or ID")
if not os.path.isdir(a.preprint):
    problems.append(f"no such folder: {a.preprint}")
if problems:
    sys.exit("\n".join(problems))


def ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else 0


def transcripts(sessions):
    """[(path, is_coordinator)] for the given sessions."""
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    out = []
    for sid in sessions:
        if not re.fullmatch(r"[0-9A-Za-z-]{8,}", sid):
            sys.exit(f"not a session id: {sid!r}")
        mains = glob.glob(os.path.join(glob.escape(config), "projects", "*", sid + ".jsonl"))
        if not mains:
            sys.exit(f"session {sid}: no transcript under {config}/projects (Claude Code deletes them after "
                     "cleanupPeriodDays). Leave the telemetry out (publish.md §5).")
        if len(mains) > 1:
            sys.exit(f"session {sid}: found {len(mains)} transcripts under {config}/projects, expected 1")
        out.append((mains[0], True))
        sub = os.path.join(glob.escape(os.path.dirname(mains[0])), sid, "subagents", "**", "*.jsonl")
        out += [(p, False) for p in sorted(glob.glob(sub, recursive=True))]
    return out


def read(path):
    """The transcript's entries, each with its time in "_t" (None if unreadable), and the number of bad ones."""
    entries, bad = [], 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                bad += 1
                continue
            if not isinstance(e, dict):
                bad += 1
                continue
            try:
                e["_t"] = ts(e["timestamp"]) if e.get("timestamp") else None
            except (ValueError, TypeError, AttributeError):
                e["_t"] = None
                bad += 1
            entries.append(e)
    return entries, bad


def describe(path):
    """(phase, label, parent agent id) of a subagent, from the description it was launched with."""
    try:
        with open(path[:-len(".jsonl")] + ".meta.json", encoding="utf-8", errors="replace") as f:
            meta = json.load(f)
        meta = meta if isinstance(meta, dict) else {}
    except (OSError, ValueError):
        meta = {}
    desc, parent = str(meta.get("description") or "").strip(), meta.get("parentAgentId")
    low = desc.lower()
    for name in sorted(PHASES + list(ALIASES), key=len, reverse=True):
        if re.match(re.escape(name) + r"(?![\w-])", low):
            rest = desc[len(name):]
            label = rest.lstrip(" :-").strip() if rest[:1] in ":-" else desc
            return ALIASES.get(name, name), ("(label withheld)" if PRIVATE.search(label) else label or desc), parent
    return "other", "(label withheld)" if PRIVATE.search(desc) else desc or "(no description)", parent


def msg(e):
    m = e.get("message")
    return m if isinstance(m, dict) else {}


def blocks(m):
    c = m.get("content")
    return [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []


def active_intervals(entries):
    """Intervals during which this agent was working (see the module docstring)."""
    line = sorted((e for e in entries if e.get("type") in TIMELINE_TYPES and e["_t"] is not None),
                  key=lambda e: e["_t"])
    out, idle = [], False
    for prev, e in zip(line, line[1:]):
        m = msg(prev)
        if prev.get("type") == "assistant":
            idle = bool(m.get("model") == "<synthetic>" or m.get("stop_reason") == "end_turn"
                        or {b.get("name") for b in blocks(m) if b.get("type") == "tool_use"} & WAIT_TOOLS)
        elif prev.get("type") == "user":
            idle = False
        if e.get("type") == "user":
            decision = e.get("permissionDecision") if isinstance(e.get("permissionDecision"), dict) else {}
            if (not any(b.get("type") == "tool_result" for b in blocks(msg(e)))
                    or str(decision.get("source", "")).startswith("user")):
                continue  # waiting for a prompt, a notification or the user's permission
        if not idle and 0 < e["_t"] - prev["_t"] <= GAP_MINUTES * 60:
            out.append((prev["_t"], e["_t"]))
    return out


def union_hours(intervals):
    total, end = 0.0, None
    for t0, t1 in sorted(intervals):
        if end is None or t0 > end:
            total += t1 - t0
            end = t1
        elif t1 > end:
            total += t1 - end
            end = t1
    return round(total / 3600, 2)


def blank():
    return dict.fromkeys(["requests"] + FIELDS, 0)


def add(row, vals):
    row["requests"] += 1
    for k in FIELDS:
        row[k] += vals[k]


def mostly(counter):
    return counter.most_common(1)[0][0] if counter else None


def finding_slugs(preprint):
    """The finding slugs in <preprint>/precedence-findings.json, or [] without it."""
    try:
        with open(os.path.join(preprint, "precedence-findings.json"), encoding="utf-8") as f:
            return sorted({x["slug"] for x in json.load(f)["findings"] if isinstance(x.get("slug"), str)})
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return []


def finding_of(label, slugs):
    """The one slug that a label names as a whole word, or None."""
    hits = [s for s in slugs if re.search(r"(?<![\w-])" + re.escape(s) + r"(?![\w-])", label or "")]
    return hits[0] if len(hits) == 1 else None


record = {"format": FORMAT, "format_version": VERSION, "definitions": DEFINITIONS,
          "skill_commits": a.skill_commit}
if unavailable:
    record.update({"harness": a.usage_unavailable.strip(), "sessions": None, "subagents": None,
                   "compactions": None, "total": None, "by_model": None, "by_phase": None, "by_agent": None})
else:
    sessions = list(dict.fromkeys(a.session)) or [os.environ.get("CLAUDE_CODE_SESSION_ID", "")]
    if not sessions[0]:
        sys.exit("no session given and $CLAUDE_CODE_SESSION_ID is unset: pass --session, "
                 "or --usage-unavailable outside Claude Code")
    files = transcripts(sessions)
    requests = {}  # message id -> (agent key, model, effort, {field: max})
    agents = {}  # agent key -> {phase, label, parent, start, intervals, models, efforts}
    versions, compactions, skipped = collections.Counter(), set(), 0
    for path, coordinator in files:
        entries, bad = read(path)
        skipped += bad
        key = "coordinator" if coordinator else path
        phase, label, parent = ("coordinator", None, None) if coordinator else describe(path)
        ag = agents.setdefault(key, {"phase": phase, "label": label, "parent": parent,
                                     "start": min((e["_t"] for e in entries if e["_t"] is not None), default=0),
                                     "intervals": [], "models": collections.Counter(),
                                     "efforts": collections.Counter()})
        ag["intervals"] += active_intervals(entries)
        for e in entries:
            if isinstance(e.get("version"), str):
                versions[e["version"]] += 1
            if e.get("type") == "system" and e.get("subtype") == "compact_boundary":
                compactions.add(str(e.get("uuid")))
            m = msg(e)
            u = m.get("usage")
            if e.get("type") != "assistant" or not isinstance(u, dict) or m.get("model") in (None, "<synthetic>"):
                continue
            cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
            w1h = num(cc.get("ephemeral_1h_input_tokens"))
            w5m = num(cc["ephemeral_5m_input_tokens"]) if "ephemeral_5m_input_tokens" in cc \
                else num(u.get("cache_creation_input_tokens")) - w1h
            vals = {"input_uncached": num(u.get("input_tokens")), "cache_write_5m": w5m, "cache_write_1h": w1h,
                    "cache_read": num(u.get("cache_read_input_tokens")), "output": num(u.get("output_tokens"))}
            rid = str(m.get("id") or e.get("requestId") or e.get("uuid"))
            r = requests.setdefault(rid, (key, str(m["model"]), e.get("effort") or e.get("perTurnEffort"),
                                          dict.fromkeys(FIELDS, 0)))
            for k, v in vals.items():
                r[3][k] = max(r[3][k], v)  # streamed entries repeat a request's usage as it grows
    # A helper launched by a subagent takes its parent's phase and label.
    ids = {(os.path.dirname(k), os.path.basename(k)[len("agent-"):-len(".jsonl")]): k
           for k in agents if k != "coordinator"}

    def settle(k, seen=()):
        pk = ids.get((os.path.dirname(k), agents[k]["parent"]))
        if pk is None or pk in seen:
            return
        settle(pk, seen + (k,))
        agents[k].update(phase=agents[pk]["phase"], label=f"{agents[pk]['label']} (helper)", parent=None)

    for k in ids.values():
        settle(k)
    total, by_model, by_phase, by_agent = blank(), collections.defaultdict(blank), collections.defaultdict(blank), {}
    for key, model, effort, vals in requests.values():
        ag = agents[key]
        ag["models"][model] += 1
        ag["efforts"][effort] += 1
        add(total, vals)
        add(by_model[(model, effort)], vals)
        add(by_phase[ag["phase"]], vals)
        add(by_agent.setdefault(key, blank()), vals)
    phase_intervals = collections.defaultdict(list)
    for key, ag in agents.items():
        phase_intervals[ag["phase"]] += ag["intervals"]
    order = ["coordinator"] + PHASES
    subs = sorted((k for k in agents if k != "coordinator"), key=lambda k: agents[k]["start"])
    slugs = finding_slugs(a.preprint)
    if not slugs:
        print("note: no precedence-findings.json with slugs in the preprint folder; findings left null",
              file=sys.stderr)
    unmatched = [agents[k]["label"] for k in subs
                 if agents[k]["phase"] in PER_FINDING and not finding_of(agents[k]["label"], slugs)]
    if slugs and unmatched:
        print("note: these labels name no single finding slug: " + "; ".join(unmatched), file=sys.stderr)
    unusual = sorted({mo for mo, _ in by_model if not PLAIN_MODEL.fullmatch(mo)})
    if unusual:
        print("note: unusual model names; point them out to the user before publishing: " + "; ".join(unusual),
              file=sys.stderr)
    record.update({
        "harness": "Claude Code " + ", ".join(sorted(versions)),
        "sessions": len(sessions),
        "subagents": len(subs),
        "compactions": len(compactions),
        "total": {**total, "active_hours": union_hours([i for ag in agents.values() for i in ag["intervals"]])},
        "by_model": [{"model": mo, "effort": ef, **row}
                     for (mo, ef), row in sorted(by_model.items(), key=lambda kv: [str(x) for x in kv[0]])],
        "by_phase": [{"phase": p, "agents": sum(ag["phase"] == p for ag in agents.values()), **by_phase[p],
                      "active_hours": union_hours(phase_intervals[p])}
                     for p in order if p in phase_intervals],
        "by_agent": [{"phase": agents[k]["phase"], "label": agents[k]["label"],
                      "finding": finding_of(agents[k]["label"], slugs),
                      "model": mostly(agents[k]["models"]), "effort": mostly(agents[k]["efforts"]),
                      **by_agent.get(k, blank()), "active_hours": union_hours(agents[k]["intervals"])}
                     for k in subs],
    })
    if skipped:
        print(f"note: {skipped} unreadable transcript lines or entries skipped", file=sys.stderr)

# Agent 0 is the coordinator; agents 1, 2, ... are the by_agent rows.
numbered = [next((p for p in record["by_phase"] if p["phase"] == "coordinator"), None)] if record["by_phase"] else []
numbered += record["by_agent"] or []


def resolve(ref, extra):
    """(agent row, factor) for '<number or label>[#n][=factor]'."""
    target, factor = ref.strip(), 1.0
    m = re.fullmatch(r"(.*?)\s*=\s*(\d+(?:\.\d+)?)", target)
    if m:
        target, factor = m.group(1), float(m.group(2))
    if factor <= 0 or (extra and factor > 1):
        sys.exit(f"{ref!r}: the {'share must be above 0 and at most 1' if extra else 'factor must be above 0'}")
    if target.isdigit() or target == "coordinator":
        n = 0 if target == "coordinator" else int(target)
        if n >= len(numbered) or numbered[n] is None:
            sys.exit(f"{ref!r}: no agent {n}; --dry-run lists them")
        return numbered[n], factor
    m = re.fullmatch(r"(.*?)#(\d+)", target)
    label, nth = (m.group(1).strip(), int(m.group(2))) if m else (target, None)
    hits = [r for r in numbered[1:] if r["label"] == label]
    if not hits:
        sys.exit(f"{ref!r}: no agent with that label; --dry-run lists them")
    if nth is None and len(hits) > 1:
        sys.exit(f"{ref!r}: {len(hits)} agents have that label; add #<n> or use its number")
    if nth is not None and not 1 <= nth <= len(hits):
        sys.exit(f"{ref!r}: there are {len(hits)} agents with that label")
    return hits[(nth or 1) - 1], factor


def side(refs, specs, extra):
    total, unknown = dict.fromkeys(FIELDS, 0.0), False
    for ref in refs:
        if ref.strip().lower() == "unknown":
            unknown = True
            continue
        row, factor = resolve(ref, extra)
        for k in FIELDS:
            total[k] += row[k] * factor
    for spec in specs:
        for k, v in kinds(spec).items():
            total[k] += v
    return {**{k: round(v) for k, v in total.items()}, "includes_unknown": unknown}


record.update({"procedure_deviations": a.deviations,
               "deviation_extra_tokens": side(a.extra, a.extra_tokens, True),
               "deviation_saved_tokens": side(a.saved, a.saved_tokens, False)})

text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
if a.dry_run:
    for n, r in enumerate(numbered):
        if r is not None:
            print(f"{n:4d}  {r['phase']:<13} {sum(r[k] for k in FIELDS) / 1e6:9.1f}M  "
                  f"{r.get('label') or 'coordinator'}")
    for key in ("deviation_extra_tokens", "deviation_saved_tokens"):
        d = record[key]
        print(f"{key}: {sum(d[k] for k in FIELDS) / 1e6:.1f}M"
              + "".join(f", {k} {d[k]:,}" for k in FIELDS) + (" (includes unknown)" if d["includes_unknown"] else ""))
    sys.exit(0)
out = os.path.join(a.preprint, "precedence-telemetry.json")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
t = record["total"]
print(f"wrote {out}" + (f": {t['requests']} requests, {sum(t[k] for k in FIELDS):,} tokens "
                        f"({t['cache_read']:,} cache reads), {t['active_hours']} active hours" if t else ""))
