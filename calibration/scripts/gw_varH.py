import json
import gw_variants as V
if __name__ == "__main__":
    G_ = json.load(open("/home/claude/gw/fit_noseason.json"))["params"]
    H = V.sed_fit(dict(G_, sed_winter_frac=0.05), ["K", "sed_cover_coef", "sed_winter_frac"], [(0.05, 5), (0.0, 0.2), (0.0, 0.5)])
    row, e = V.summ("H linear CN + ZT offset, exponential sediment + sediment season only", H)
    var = json.load(open("/home/claude/gw/variants.json")); var["H"] = row
    json.dump(var, open("/home/claude/gw/variants.json", "w"), default=float, indent=1)
    json.dump({"params": H}, open("/home/claude/gw/fit_H.json", "w"), default=float, indent=1)
