from __future__ import annotations
from pathlib import Path


def _escape_pdf(text: str) -> str:
    return str(text).replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


class MotorsportReport:
    """Small dependency-free PDF writer used by the event export."""
    def __init__(self, path, logo_path=None, hero_path=None):
        self.path = Path(path)
        self.logo_path = logo_path
        self.hero_path = hero_path

    def build_event_report(self, bundle) -> None:
        lines = ["SORG RENNSPORT - GT Data Analyzer", ""]
        event = bundle.get("event") if isinstance(bundle, dict) else None
        if event:
            def v(k, default=""):
                try: return event[k] if event[k] is not None else default
                except Exception: return default
            lines += [f"Event: {v('name')}", f"Strecke: {v('track_name')}",
                      f"Datum: {v('start_date')} - {v('end_date')}", ""]
        sessions = bundle.get("sessions", []) if isinstance(bundle, dict) else []
        for item in sessions:
            s = item.get("session", item) if isinstance(item, dict) else item
            try:
                lines.append(f"Session: {s['session_date']} | {s['session_type']} | {s['manufacturer']} {s['model']}")
            except Exception:
                lines.append("Session")
            if isinstance(item, dict):
                lines.append(f"  Reifensaetze: {len(item.get('tyres', []))} | Setup: {len(item.get('setup', []))} | Aenderungen: {len(item.get('changes', []))}")
        self._write_pdf(lines)

    def _write_pdf(self, lines):
        pages=[]
        for i in range(0, max(1,len(lines)), 44):
            pages.append(lines[i:i+44] or ["SORG GT Data Analyzer"])
        objects=[]
        # 1 catalog, 2 pages tree, 3 font; page/content pairs start at 4
        kids=[]
        for idx,page_lines in enumerate(pages):
            page_obj=4+idx*2; content_obj=page_obj+1; kids.append(f"{page_obj} 0 R")
            stream=["BT", "/F1 11 Tf", "48 790 Td", "14 TL"]
            for j,line in enumerate(page_lines):
                if j: stream.append("T*")
                stream.append(f"({_escape_pdf(line)[:160]}) Tj")
            stream.append("ET")
            data="\n".join(stream).encode('latin-1','replace')
            objects.append((page_obj, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_obj} 0 R >>".encode()))
            objects.append((content_obj, b"<< /Length "+str(len(data)).encode()+b" >>\nstream\n"+data+b"\nendstream"))
        base=[(1,b"<< /Type /Catalog /Pages 2 0 R >>"),
              (2,f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>".encode()),
              (3,b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")]
        all_objs=sorted(base+objects)
        pdf=bytearray(b"%PDF-1.4\n")
        offsets={}
        for num,data in all_objs:
            offsets[num]=len(pdf); pdf += f"{num} 0 obj\n".encode()+data+b"\nendobj\n"
        xref=len(pdf); maxobj=max(offsets)
        pdf += f"xref\n0 {maxobj+1}\n".encode()+b"0000000000 65535 f \n"
        for n in range(1,maxobj+1): pdf += f"{offsets[n]:010d} 00000 n \n".encode()
        pdf += f"trailer\n<< /Size {maxobj+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
        self.path.write_bytes(pdf)
