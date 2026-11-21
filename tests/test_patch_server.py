import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import patch_server as ps  # noqa: E402

SAMPLE = (
    "            val serverUrl = (serverSelectionModule()?.getServerUrl() ?: repository.getServerUrl())\n"
    "            if (serverUrl.isNullOrBlank()) {\n"
    "                _screen.value = AppScreen.ServerSetup()\n"
    "                return@launch\n"
    "            }\n"
)


class ValidateUrl(unittest.TestCase):
    def test_valid(self):
        for u in ["https://book.karbono.es", "http://localhost:8080", "https://a.b/path/x_y-1", "https://h:443/"]:
            self.assertEqual(ps.validate_url(u), u)

    def test_invalid(self):
        for u in ['https://a"b', "https://a\nb", "https://a b", "ftp://x", "https://", "javascript:1",
                  'https://x.es/"; evil()', "https://x.es/$a\\", "https://x.es\n", "", "https://x:99999999/"]:
            with self.assertRaises(ValueError, msg=repr(u)):
                ps.validate_url(u)


class ValidateName(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(ps.validate_name("BookOrbit"), "BookOrbit")
        self.assertEqual(ps.validate_name("Mi $erver"), "Mi $erver")

    def test_invalid(self):
        for n in ["", 'a"b', "a\nb", "a\rb", "x" * 65, "a\x00b"]:
            with self.assertRaises(ValueError, msg=repr(n)):
                ps.validate_name(n)


class Escape(unittest.TestCase):
    def test_escape(self):
        self.assertEqual(ps.kotlin_escape('a\\b"c$d\ne\r'), 'a\\\\b\\"c\\$d\\ne\\r')
        self.assertEqual(ps.kotlin_escape("https://x.es"), "https://x.es")


class Cli(unittest.TestCase):
    def run_script(self, **env):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "A.kt"
            f.write_text(SAMPLE)
            e = {k: v for k, v in os.environ.items() if k not in ("SERVER_URL", "SERVER_NAME")}
            e.update(env)
            r = subprocess.run([sys.executable, str(ROOT / "scripts/patch_server.py"), str(f)],
                               env=e, capture_output=True, text=True)
            return r, f.read_text()

    def test_ok_and_escaped(self):
        r, out = self.run_script(SERVER_URL="https://x.es/a", SERVER_NAME="Mi $erver")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('val defaultUrl = "https://x.es/a"', out)
        self.assertIn('displayName = "Mi \\$erver"', out)

    def test_rejects_injection(self):
        for env in [{"SERVER_URL": 'https://x.es"; evil()//'}, {"SERVER_NAME": 'x"\nevil()'}]:
            r, out = self.run_script(**env)
            self.assertEqual(r.returncode, 1)
            self.assertEqual(out, SAMPLE)


if __name__ == "__main__":
    unittest.main()
