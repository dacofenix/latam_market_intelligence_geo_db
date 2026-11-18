#!/usr/bin/env python3
"""Layer B (Stack Overflow Developer Survey 2025) for a focus country.

Re-implements the indicator set and rules of the Peru/Mexico layer B engine
(layer_b_engine.py, as published in the Mexico package) so that it can be run
with Argentina as focus country. Validation: run with --focus MX and compare
with the Mexico package outputs (all rows must match).

Usage: build-argentina-b-survey.py <raw_dir_with_results.csv> <out_dir> [--focus AR] [--mexico-dir DIR]
"""
import argparse, csv, json, math, os, hashlib
import pandas as pd

SURVEY = "stack_overflow_developer_survey"
YEAR = "2025"
SRC = "SRC_SO_2025"
Z = 1.959963984540054

LATAM = ["Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Costa Rica", "Cuba",
         "Dominican Republic", "Ecuador", "El Salvador", "Guatemala", "Honduras", "Mexico",
         "Nicaragua", "Panama", "Paraguay", "Peru", "Uruguay", "Venezuela, Bolivarian Republic of..."]
ISO = {"AR": "Argentina", "BR": "Brazil", "MX": "Mexico", "CO": "Colombia", "CL": "Chile", "PE": "Peru"}
PRO = "I am a developer by profession"

# Item lists exactly as in the Mexico/Peru engine outputs (fixed order).
B4A = ["Visual Studio Code", "Visual Studio", "Notepad++", "IntelliJ IDEA", "Vim", "Cursor", "PyCharm",
       "Android Studio", "Jupyter Notebook/JupyterLab", "Neovim", "Nano", "Sublime Text", "Xcode", "Claude Code",
       "WebStorm", "Zed", "Rider", "Eclipse", "VSCodium", "PhpStorm", "Windsurf", "RustRover", "Lovable.dev",
       "Bolt", "Cline and/or Roo", "Aider", "Trae"]
AI_NATIVE = ["Cursor", "Windsurf", "Claude Code", "Cline and/or Roo", "Aider", "Trae", "Bolt", "Lovable.dev", "Zed"]
B4B = ["openAI GPT (chatbot models)", "Anthropic: Claude Sonnet", "Gemini (Flash general purpose models)",
       "openAI Reasoning models", "openAI Image generating models", "Gemini (Pro Reasoning models)",
       "DeepSeek (R- Reasoning models)", "Meta Llama (all models)", "DeepSeek (V- General purpose models)",
       "X Grok models", "Mistral AI models", "Perplexity Sonar models", "Alibaba Cloud Qwen models",
       "Microsoft Phi-4 models", "Amazon Titan models", "Cohere: Command A", "Reka (Flash 3 or other Reka models)"]
B4C = ["ChatGPT", "GitHub Copilot", "Google Gemini", "Claude Code", "Microsoft Copilot", "Perplexity", "v0.dev",
       "Bolt.new", "Lovable.dev", "AgentGPT", "Tabnine", "Replit", "Auto-GPT", "Amazon Codewhisperer",
       "Blackbox AI", "Roo code (Roo-Cline)", "Cody", "Devin AI", "Glean (Enterprise Agents)",
       "OpenHands (formerly OpenDevin)"]
BX3 = ["Visual Studio Code", "IntelliJ IDEA", "Visual Studio", "Vim", "Notepad++", "Cursor", "Neovim", "Claude Code",
       "PyCharm", "Jupyter Notebook/JupyterLab", "Android Studio", "Zed", "Nano", "Xcode", "Sublime Text",
       "WebStorm", "Rider", "VSCodium", "Windsurf", "PhpStorm", "RustRover", "Eclipse", "Lovable.dev",
       "Cline and/or Roo", "Aider", "Bolt", "Trae"]
TASKS = ["Committing and reviewing code", "Creating or maintaining documentation", "Debugging or fixing code",
         "Deployment and monitoring", "Documenting code", "Generating content or synthetic data",
         "Learning about a codebase", "Learning new concepts or technologies", "Predictive analytics",
         "Project planning", "Search for answers", "Testing code", "Writing code"]
TOOLCOLS = {"current": ["AIToolCurrently partially AI", "AIToolCurrently mostly AI"],
            "planned": ["AIToolPlan to partially use AI", "AIToolPlan to mostly use AI"],
            "not_planned": ["AIToolDon't plan to use AI for this task"]}
BX9 = ["AI solutions that are almost right, but not quite", "Debugging AI-generated code is more time-consuming",
       "I don\u2019t use AI tools regularly",
       "I\u2019ve become less confident in my own problem-solving", "It\u2019s hard to understand how or why the code works",
       "Other (write in):", "I haven\u2019t encountered any problems"]
DIST = [("BX5", "AISent"), ("BX7", "AIComplex"), ("BX6", "AIAcc"), ("BX8", "AIAgentChange"),
        ("BX10", "PurchaseInfluence"), ("BX12", "LearnCodeAI"), ("BX11", "AIThreat")]


def wilson(k, n):
    if n == 0:
        return None, None
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def base_flag(n):
    if n < 30:
        return "suppressed"
    if n < 50:
        return "indicative"
    return "ok"


def multi(series):
    """Series of ';'-joined answers -> list of sets (None when missing)."""
    return [None if (isinstance(v, float) and math.isnan(v)) else set(str(v).split(";")) for v in series]


def build(df, focus):
    fname = ISO[focus]
    latam_ex = [c for c in LATAM if c != fname]
    comp = [c for c in ["BR", "AR", "MX", "CO", "CL"] if c != focus][:4] if focus != "MX" else ["BR", "AR", "CO", "CL"]
    groups = [
        ("country", focus, "all_respondents", f'Respondents with Country = "{fname}"', fname, "",
         df[df.Country == fname]),
        ("country", focus, "professional_developers",
         f'Respondents with Country = "{fname}" and MainBranch = "{PRO}"', f"{fname} - professional developers", "",
         df[(df.Country == fname) & (df.MainBranch == PRO)]),
        ("region", f"LATAM_EX_{focus}", "all_respondents",
         f"Respondents in 18 Latin American countries, {fname} EXCLUDED", f"LATAM excl. {fname} (18 countries)",
         ";".join(latam_ex), df[df.Country.isin(latam_ex)]),
        ("global", "GLOBAL", "all_respondents",
         f"All {len(df):,} respondents in the public CSV, including {df.Country.isna().sum():,} with no country",
         "Global", "", df),
    ]
    for c in comp:
        groups.append(("country", c, "all_respondents", f'Country = "{ISO[c]}"', ISO[c], "", df[df.Country == ISO[c]]))

    ind_rows, dist_rows, grp_rows = [], [], []
    for gtype, gcode, seg, gdef, glabel, incl, g in groups:
        n_resp = len(g)
        grp_rows.append(dict(focus_country_code=focus, group_type=gtype, group_code=gcode, survey_segment=seg,
                             group_definition=gdef, group_label=glabel, countries_included=incl,
                             respondents=n_resp, template_confidence="LOW (<300)" if n_resp < 300 else ">=300",
                             source_id=SRC))
        out = []

        def add(iid, block, var, qid, item, k, n, task="", stance="", derived=False):
            out.append(dict(indicator_id=iid, indicator_block=block, variable=var, qid=qid, item=item, task=task,
                            task_stance=stance, numerator=k, valid_n=n, is_derived=derived))

        sel = g.AISelect.dropna()
        yes = sel.str.startswith("Yes")
        add("B1", "adoption", "AISelect", "QID78", "Uses AI tools (daily, weekly or monthly/infrequently)", int(yes.sum()), len(sel))
        add("B2", "adoption", "AISelect", "QID78", "Uses AI tools daily", int((sel == "Yes, I use AI tools daily").sum()), len(sel))
        ag = g.AIAgents.dropna()
        add("B3", "adoption", "AIAgents", "QID85", "Uses AI agents at work (daily, weekly or monthly/infrequently)",
            int(ag.str.startswith("Yes").sum()), len(ag))
        dev = [s for s in multi(g.DevEnvsHaveWorkedWith) if s is not None]
        for it in B4A:
            add("B4a", "tool_use", "DevEnvsHaveWorkedWith", "QID38", it, sum(it in s for s in dev), len(dev))
        mods = [s for s in multi(g.AIModelsHaveWorkedWith) if s is not None]
        for it in B4B:
            add("B4b", "tool_use", "AIModelsHaveWorkedWith", "QID43", it, sum(it in s for s in mods), len(mods))
        ext = [s for s in multi(g.AIAgentExternal) if s is not None]
        for it in B4C:
            add("B4c", "tool_use", "AIAgentExternal", "QID92", it, sum(it in s for s in ext), len(ext))
        add("B5", "sample", "Country", "QID20", "Respondents (rows with group definition)", n_resp, n_resp)
        add("B4a", "tool_use", "DevEnvsHaveWorkedWith", "QID38",
            "ANY AI-native editor (Cursor, Windsurf, Claude Code, Cline and/or Roo, Aider, Trae, Bolt, Lovable.dev, Zed)",
            sum(bool(s & set(AI_NATIVE)) for s in dev), len(dev), derived=True)
        plan = int((sel == "No, but I plan to soon").sum())
        nonu = int(sel.str.startswith("No").sum())
        add("BX1", "intention", "AISelect", "QID78", "Does not use AI tools but plans to soon", plan, len(sel))
        add("BX1", "intention", "AISelect", "QID78", "Plans to soon, as share of NON-users", plan, nonu)
        add("BX2", "intention", "AIAgents", "QID85", "Does not use AI agents but plans to", int((ag == "No, but I plan to").sum()), len(ag))
        add("BX2", "intention", "AIAgents", "QID85", "Uses AI only in copilot/autocomplete mode (not agents)",
            int((ag == "No, I use AI exclusively in copilot/autocomplete mode").sum()), len(ag))
        add("BX2", "intention", "AIAgents", "QID85", "Does not use AI agents and does not plan to",
            int((ag == "No, and I don't plan to").sum()), len(ag))
        want = [s for s in multi(g.DevEnvsWantToWorkWith) if s is not None]
        for it in BX3:
            add("BX3", "intention", "DevEnvsWantToWorkWith", "QID38", it, sum(it in s for s in want), len(want))
        tc = {k: [multi(g[c]) for c in cols] for k, cols in TOOLCOLS.items()}
        allcols = [multi(g[c]) for cols in TOOLCOLS.values() for c in cols]
        for t in TASKS:
            answered = [any(col[i] is not None and t in col[i] for col in allcols) for i in range(n_resp)]
            nv = sum(answered)
            labels = {"current": "currently uses AI (mostly or partially)", "planned": "plans to use AI (mostly or partially)",
                      "not_planned": "does not plan to use AI"}
            for st in ["current", "planned", "not_planned"]:
                k = sum(any(col[i] is not None and t in col[i] for col in tc[st]) for i in range(n_resp))
                add("BX4", "intention", "AITool* (5 matrix columns)", "QID82", f"{t} | {labels[st]}", k, nv, task=t, stance=st)
        se = g.AISent.dropna()
        add("BX5", "sentiment", "AISent", "QID79", "Favorable or very favorable towards AI tools",
            int(se.isin(["Favorable", "Very favorable"]).sum()), len(se))
        ac = g.AIAcc.dropna()
        add("BX6", "trust", "AIAcc", "QID80", "Trusts accuracy of AI output (highly or somewhat)",
            int(ac.isin(["Highly trust", "Somewhat trust"]).sum()), len(ac))
        add("BX6", "trust", "AIAcc", "QID80", "Distrusts accuracy of AI output (highly or somewhat)",
            int(ac.isin(["Highly distrust", "Somewhat distrust"]).sum()), len(ac))
        cx = g.AIComplex.dropna()
        add("BX7", "trust", "AIComplex", "QID81", "AI handles complex tasks very well or good",
            int(cx.isin(["Very well at handling complex tasks", "Good, but not great at handling complex tasks"]).sum()), len(cx))
        add("BX7", "trust", "AIComplex", "QID81", "Does not use AI for complex tasks / doesn't know",
            int((cx == "I don't use AI tools for complex tasks / I don't know").sum()), len(cx))
        ch = g.AIAgentChange.dropna()
        add("BX8", "behaviour", "AIAgentChange", "QID83", "AI tools or agents changed how development work is done",
            int(ch.isin(["Yes, somewhat", "Yes, to a great extent"]).sum()), len(ch))
        fr = [s for s in multi(g.AIFrustration) if s is not None]
        for it in BX9:
            add("BX9", "behaviour", "AIFrustration", "QID99", it, sum(it in s for s in fr), len(fr))
        pi = g.PurchaseInfluence.dropna()
        add("BX10", "behaviour", "PurchaseInfluence", "QID17",
            "Influenced or endorsed a technology purchase/tool in the past year", int(pi.str.startswith("Yes").sum()), len(pi))
        add("BX10", "behaviour", "PurchaseInfluence", "QID17",
            "Influenced a paid purchase (substantial addition or tool used by >5 colleagues)",
            int(pi.str.startswith("Yes, I influenced the purchase").sum()), len(pi))
        th = g.AIThreat.dropna()
        add("BX11", "sentiment", "AIThreat", "QID28", "Believes AI is a threat to current job", int((th == "Yes").sum()), len(th))
        lc = g.LearnCodeAI.dropna()
        add("BX12", "behaviour", "LearnCodeAI", "QID12", "Learned AI-enabled tools in the past year",
            int(lc.str.startswith("Yes").sum()), len(lc))
        add("BX12", "behaviour", "LearnCodeAI", "QID12", "Learned AI-enabled tools for job or career",
            int((lc == "Yes, I learned how to use AI-enabled tools required for my job or to benefit my career").sum()), len(lc))

        for r in out:
            k, n = r["numerator"], r["valid_n"]
            if r["indicator_id"] == "B5":
                p = lo = hi = None
                bf = "not_applicable"
            else:
                bf = base_flag(n)
                if bf == "suppressed" or n == 0:
                    p = lo = hi = None
                else:
                    p = k / n
                    lo, hi = wilson(k, n)
            # Engine rules (reproduced from the Mexico package): suppressed cells (valid_n < 30) hide the
            # numerator; the small-numerator flag (< 10) is raised for country and global groups, not regions.
            r.update(survey=SURVEY, survey_year=YEAR, focus_country_code=focus, group_type=gtype, group_code=gcode,
                     survey_segment=seg, group_definition=gdef, proportion=p, ci_low=lo, ci_high=hi, base_flag=bf,
                     small_numerator_flag=(k < 10 and gtype != "region" and bf != "suppressed"), source_id=SRC)
            if bf == "suppressed":
                r["numerator"] = None
            ind_rows.append(r)

        for iid, var in DIST:
            s = g[var].dropna()
            n = len(s)
            vc = s.value_counts()
            for cat in sorted(df[var].dropna().unique()):
                k = int(vc.get(cat, 0))
                bf = base_flag(n)
                dist_rows.append(dict(focus_country_code=focus, group_type=gtype, group_code=gcode, survey_segment=seg,
                                      group_definition=gdef, survey_year=YEAR, indicator_id=iid, variable=var,
                                      category=cat, numerator=int(k), valid_n=n,
                                      proportion=None if bf == "suppressed" else k / n, base_flag=bf,
                                      small_numerator_flag=k < 10, source_id=SRC))

    # exploratory comparisons for the focus country (all respondents) against LATAM ex-focus and global
    key = lambda r: (r["indicator_id"], r["item"])
    by = {}
    for r in ind_rows:
        by[(r["group_code"], r["survey_segment"], key(r))] = r
    for r in ind_rows:
        for col, ref in [(f"vs_latam_ex_{focus.lower()}", f"LATAM_EX_{focus}"), ("vs_global", "GLOBAL")]:
            r.setdefault(col, "")
        if r["group_code"] != focus or r["survey_segment"] != "all_respondents":
            continue
        for col, ref in [(f"vs_latam_ex_{focus.lower()}", f"LATAM_EX_{focus}"), ("vs_global", "GLOBAL")]:
            o = by[(ref, "all_respondents", key(r))]
            if r["proportion"] is None or o["proportion"] is None:
                r[col] = "not_assessed"
            elif r["ci_low"] > o["ci_high"]:
                r[col] = "higher_exploratory"
            elif r["ci_high"] < o["ci_low"]:
                r[col] = "lower_exploratory"
            else:
                r[col] = "no_clear_difference_exploratory"
    return ind_rows, dist_rows, grp_rows


IND_COLS = ["survey", "survey_year", "indicator_id", "indicator_block", "variable", "qid", "item", "task", "task_stance",
            "focus_country_code", "group_type", "group_code", "survey_segment", "group_definition", "numerator",
            "valid_n", "proportion", "ci_low", "ci_high", "base_flag", "small_numerator_flag", "VS_LATAM", "vs_global",
            "is_derived", "source_id"]
DIST_COLS = ["focus_country_code", "group_type", "group_code", "survey_segment", "group_definition", "survey_year",
             "indicator_id", "variable", "category", "numerator", "valid_n", "proportion", "base_flag",
             "small_numerator_flag", "source_id"]
GRP_COLS = ["focus_country_code", "group_type", "group_code", "survey_segment", "group_definition", "group_label",
            "countries_included", "respondents", "template_confidence", "source_id"]


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    return repr(v) if isinstance(v, float) else str(v)


def write(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([fmt(r.get(c)) for c in cols])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("out")
    ap.add_argument("--focus", default="AR")
    a = ap.parse_args()
    f = os.path.join(a.raw, "results.csv")
    df = pd.read_csv(f, low_memory=False)
    ind, dist, grp = build(df, a.focus)
    fl = a.focus.lower()
    cols = [c if c != "VS_LATAM" else f"vs_latam_ex_{fl}" for c in IND_COLS]
    os.makedirs(a.out, exist_ok=True)
    write(os.path.join(a.out, f"b_survey_indicators_{fl}.csv"), cols, ind)
    write(os.path.join(a.out, f"b_survey_distributions_{fl}.csv"), DIST_COLS, dist)
    write(os.path.join(a.out, f"b_comparison_groups_{fl}.csv"), GRP_COLS, grp)
    print(len(ind), len(dist), len(grp))


if __name__ == "__main__":
    main()
