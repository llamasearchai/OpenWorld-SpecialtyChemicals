from openworld_specialty_chemicals.provenance import ProvenanceStore
from openworld_specialty_chemicals.lineage import LineageStore

def test_provenance_and_lineage(tmp_path):
    prov_path = tmp_path / "prov/ledger.jsonl"
    lin_path = tmp_path / "lin/samples.jsonl"
    ps = ProvenanceStore(str(prov_path))
    ps.log("step", {"a":1}, ["in"], ["out"])
    assert prov_path.exists() and prov_path.read_text().strip() != ""
    ls = LineageStore(str(lin_path))
    ls.log_sample("S1","lab_csv","SO4","ICP-MS",{"Kd":0.1},"file.csv")
    assert lin_path.exists() and lin_path.read_text().strip() != ""


