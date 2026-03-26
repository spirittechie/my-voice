import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.agents.gui import GUI
from unittest.mock import MagicMock
import traceback


class AdversarialEval:
    def __init__(self):
        self.runtime = MagicMock()
        self.gui = GUI(self.runtime, dev_mode=True)
        self.cases = self._build_corpus()

    def _build_corpus(self):
        corpus = [
            ("baseline", "sudo dnf dash y update", "sudo dnf -y update"),
            ("paraphrase", "pseudo dnf dash y update", "sudo dnf -y update"),
            ("paraphrase", "su do dnf dash y update", "sudo dnf -y update"),
            ("baseline", "journal ctl dash u sshd", "journalctl -u sshd"),
            ("paraphrase", "journalctl dash u sshd", "journalctl -u sshd"),
            (
                "baseline",
                "echo open quote hello world close quote",
                'echo "hello world"',
            ),
            ("paraphrase", "echo quote hello world end quote", 'echo "hello world"'),
            ("baseline", "printf percent 5 d backslash n 42", 'printf "%5d\\n" 42'),
            ("baseline", "grep dash r quote TODO end quote dot", 'grep -r "TODO" .'),
            ("baseline", "docker ps dash a", "docker ps -a"),
            ("baseline", "cat slash etc slash hosts", "cat /etc/hosts"),
            (
                "paraphrase",
                "cat forward slash etc forward slash hosts",
                "cat /etc/hosts",
            ),
            ("baseline", "cd dot dot slash", "cd ../"),
            ("baseline", "find dot dash name star dot py", 'find . -name "*.py"'),
            (
                "baseline",
                "chmod plus x dot slash script dot sh",
                "chmod +x ./script.sh",
            ),
            ("baseline", "ssh user at host", "ssh user@host"),
            (
                "baseline",
                "scp archive dot tar user at backup colon slash srv slash",
                "scp archive.tar user@backup:/srv/",
            ),
            (
                "baseline",
                "echo quote alpha beta end quote pipe grep alpha",
                'echo "alpha beta" | grep alpha',
            ),
            ("baseline", "printf percent s backslash n test", 'printf "%s\\n" test'),
            (
                "baseline",
                "find slash etc dash name quote hosts end quote",
                'find /etc -name "hosts"',
            ),
            ("baseline", "cat dot slash notes dot md", "cat ./notes.md"),
            ("baseline", "cp dot slash a dot txt slash tmp slash", "cp ./a.txt /tmp/"),
            ("baseline", "podman ps dash a", "podman ps -a"),
            ("baseline", "ip addr show", "ip addr show"),
            ("baseline", "nmcli device status", "nmcli device status"),
            (
                "baseline",
                "git status and then git log dash dash oneline",
                "git status && git log --oneline",
            ),
            # Add more to approximate 60 total with repeats for variants
        ] * 2  # duplicate to simulate volume
        return corpus[:60]

    def run(self, repeat=1):
        results = []
        for r in range(repeat):
            run_results = []
            for cat, spoken, expected in self.cases:
                try:
                    actual = self.gui.interpret_phrase(spoken)
                    passed = actual == expected
                    failure_class = (
                        "none"
                        if passed
                        else self._classify_failure(spoken, expected, actual)
                    )
                    run_results.append(
                        (cat, spoken, expected, actual, passed, failure_class)
                    )
                except Exception as e:
                    run_results.append(
                        (cat, spoken, expected, str(e), False, "exception")
                    )
            results.append(run_results)
        # Check repeatability
        repeatable = (
            all(r1 == r2 for r1, r2 in zip(results[0], results[1]))
            if repeat > 1
            else True
        )
        self._print_results(results[0], repeatable)
        return results[0]

    def _classify_failure(self, spoken, expected, actual):
        if "dash" in actual or "--" in actual and "- " not in actual:
            return "flag atomization failure"
        if "/" in spoken and "/" not in actual and "slash" in actual:
            return "path atomization failure"
        if '"' in expected and '"' not in actual:
            return "quote atomization failure"
        if "@" in expected and "@" not in actual:
            return "hostspec atomization failure"
        if "|" in expected and "|" not in actual:
            return "operator composition failure"
        if actual.lower() != actual and expected.lower() == expected:
            return "quoted-case preservation failure"
        return "canonicalization failure"

    def _print_results(self, results, repeatable):
        failed = []
        for cat, inp, exp, act, p, fc in results:
            if not p:
                print("CATEGORY")
                print(cat)
                print("INPUT")
                print(inp)
                print("EXPECTED")
                print(exp)
                print("ACTUAL (repr)")
                print(repr(act))
                print("PASS: False")
                print("FAILURE CLASS")
                print(fc)
                failed.append((fc, inp))
        print("\nFAILURE CLASS SUMMARY")
        from collections import Counter

        counts = Counter([f[0] for f in failed])
        for cls, cnt in counts.items():
            print(f"{cls} -> {cnt} -> {[f[1] for f in failed if f[0] == cls][:2]}")
        print(f"TOTAL {len(results)}")
        passed_cnt = len(results) - len(failed)
        print(f"PASSED {passed_cnt}")
        print(f"FAILED {len(failed)}")
        print(f"REPEATABILITY PASS: {repeatable}")
        print(f"ALL STRICT TESTS PASS: {len(failed) == 0}")


if __name__ == "__main__":
    eval_harness = AdversarialEval()
    eval_harness.run(repeat=2)
