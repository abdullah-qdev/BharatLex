"""i broke my laptop an they are refuing to give refund
"""

import asyncio

from quad_polar import run_grievance_pipeline, CATEGORY_LAWS

DISCLAIMER = ("This tool gives general guidance, not legal advice. "
              "Any drafted notice is a starting point to review with a lawyer.\n")

MY_CATEGORY  = "consumer"
MY_GRIEVANCE = "An online seller took my payment but never shipped and won't refund."


def pick_category() -> str:
    cats = list(CATEGORY_LAWS.keys())
    print("\nCategories:")
    for i, c in enumerate(cats, 1):
        print(f"  {i}. {c}")
    while True:
        choice = input("Pick a category number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(cats):
            return cats[int(choice) - 1]
        print("  Invalid choice, try again.")


def read_grievance() -> str:
    print("\nDescribe the grievance. Press Enter on an empty line when done:")
    lines = []
    while True:
        line = input()
        if line.strip() == "" and lines:
            break
        if line.strip():
            lines.append(line)
    return " ".join(lines)


def show(verdict: dict):
    print("\n" + "=" * 64)
    print("SUMMARY:", verdict.get("summary", ""))
    if verdict.get("forum"):
        print("\nFORUM:", verdict["forum"])
    if verdict.get("applicable_law"):
        print("\nAPPLICABLE LAW:")
        for a in verdict["applicable_law"]:
            print(f"  - {a.get('law','')} {a.get('section','')}: {a.get('why','')}")
    print("\nTASKS:")
    for i, t in enumerate(verdict.get("tasks", []), 1):
        dl = f"  (by {t['deadline']})" if t.get("deadline") else ""
        print(f"  {i}. {t.get('step','')}{dl}")
        if t.get("detail"):
            print(f"       {t['detail']}")
    if verdict.get("documents"):
        print("\nDOCUMENTS NEEDED:", ", ".join(verdict["documents"]))
    if verdict.get("relief"):
        print("\nRELIEF:", verdict["relief"])
    print("CONFIDENCE:", verdict.get("confidence", ""))
    if verdict.get("notice_draft"):
        print("\n" + "-" * 64 + "\nDRAFT LEGAL NOTICE\n" + "-" * 64)
        print(verdict["notice_draft"])
    print("=" * 64)


async def main():
    print(DISCLAIMER)
    category = pick_category()
    grievance = read_grievance()
    facts = {}

    while True:
        print("\nWorking… (4 agents debating locally, then Gemini judging)\n")
        verdict = await run_grievance_pipeline(grievance, category, facts)

        if verdict.get("status") == "needs_input":
            print("A few details are missing:")
            for q in verdict["questions"]:
                facts[q] = input(f"  {q}\n  > ").strip()
            continue                          # re-run with the answers

        show(verdict)
        break


if __name__ == "__main__":
    asyncio.run(main())
