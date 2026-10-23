import io, numpy as np, pandas as pd
D = "/home/claude/gm/data/"
FILES = {"Burnt": "Greenmount_Burnt.sim", "Incorporated": "Greenmount_Incorporated.sim",
         "Mulch": "Greenmount_mulch.sim", "Zero till": "Greenmount_Zero_till.sim"}

def load(name):
    L = [l for l in open(D + FILES[name], errors="replace") if not l.startswith("//")]
    i = next(k for k, l in enumerate(L) if l.startswith("Date"))
    d = pd.read_csv(io.StringIO("".join(L[i:])), on_bad_lines="skip", dtype=str)
    d["Date"] = pd.to_datetime(d["Date"], dayfirst=True, errors="coerce")
    d = d.dropna(subset=["Date"]).set_index("Date").apply(pd.to_numeric, errors="coerce")
    col = lambda *keys: next((c for c in d.columns if all(k.lower() in c.lower() for k in keys)), None)
    return pd.DataFrame({"cover": d[col("cov")], "paw": d[col("paw")],
                         "rough": d[col("rough")] if col("rough") else np.nan,
                         "runoff": d[col("runoff")], "erosion": d[col("erosion")],
                         "suspended": d[col("susp")]})
