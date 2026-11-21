"""Genera entrega_logix.md/.docx insertando la evidencia MEDIDA (docs/evidencia_consola.txt) en la plantilla.
Uso (desde la carpeta logix/):  python main.py --all-quick > docs/evidencia_consola.txt  &&  python docs/generar_entrega.py
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ev = open(os.path.join(HERE, "evidencia_consola.txt"), encoding="utf-8").read()
blocks: dict[str, list[str]] = {}
parts = re.split(r"\n=+\n  (P\d\d) - ([^\n]*)\n=+\n", "\n" + ev)
for i in range(1, len(parts), 3):
    blocks.setdefault(parts[i], []).append(f"[{parts[i]}] {parts[i + 1]}\n{parts[i + 2].strip()}")


def block(kind: str, q: str) -> str:
    items = blocks.get(q, [])
    sel = items[:1] if kind == "DEMO" else items[1:]
    return "\n\n".join(f"```text\n{b}\n```" for b in sel)


tpl = open(os.path.join(HERE, "plantilla_entrega.md"), encoding="utf-8").read()
out = re.sub(r"\{\{(DEMO|BENCH):(P\d\d)\}\}", lambda m: block(m.group(1), m.group(2)), tpl)
md = os.path.join(HERE, "entrega_logix.md")
open(md, "w", encoding="utf-8").write(out)
try:
    subprocess.run(["pandoc", md, "-o", os.path.join(HERE, "entrega_logix.docx")], check=True)
    print("Generados entrega_logix.md y entrega_logix.docx")
except (FileNotFoundError, subprocess.CalledProcessError):
    print("Generado entrega_logix.md (pandoc no disponible: convierta a Word manualmente)")
