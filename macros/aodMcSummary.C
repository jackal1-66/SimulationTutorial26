// Summary of the MC content of an AO2D file:
//  - number of MC collisions per sub-generator ID (e.g. gap-triggered or hybrid generators)
//  - number of MC particles with a given |PDG| code, per sub-generator ID
// Usage: root -l -b -q 'aodMcSummary.C("AO2D.root",4122)'
#include <map>

// sub-generator ID: bits 11-15 of fGeneratorsID, stored with an offset of +1
// (see o2::mcgenid in SimulationDataFormat/MCGenProperties.h)
int subGeneratorId(short generatorsID)
{
  return static_cast<int>((static_cast<unsigned short>(generatorsID) >> 11) & 0x1F) - 1;
}

void aodMcSummary(const char* fname = "AO2D.root", int pdg = 4122)
{
  TFile f(fname);
  if (f.IsZombie()) {
    return;
  }
  std::map<int, long> nCollPerSubGen, nSelPerSubGen;
  long nColl = 0, nPart = 0, nSel = 0;
  for (auto k : *f.GetListOfKeys()) {
    TString dname = k->GetName();
    if (!dname.BeginsWith("DF_")) {
      continue;
    }
    auto dir = (TDirectory*)f.Get(dname);
    TTree *tColl = nullptr, *tPart = nullptr;
    for (auto kk : *dir->GetListOfKeys()) {
      TString tname = kk->GetName();
      // exact table names, with an optional version suffix (O2mccollision_001); not O2mccollisionlabel
      if (tname == "O2mccollision" || tname.BeginsWith("O2mccollision_")) {
        tColl = (TTree*)dir->Get(tname);
      } else if (tname == "O2mcparticle" || tname.BeginsWith("O2mcparticle_")) {
        tPart = (TTree*)dir->Get(tname);
      }
    }
    if (!tColl) {
      continue;
    }
    // sub-generator ID of every MC collision in this data frame
    std::vector<int> subGen;
    TTreeReader rc(tColl);
    TTreeReaderValue<short> genId(rc, "fGeneratorsID");
    while (rc.Next()) {
      subGen.push_back(subGeneratorId(*genId));
      nCollPerSubGen[subGen.back()]++;
    }
    nColl += subGen.size();
    if (!tPart) {
      continue;
    }
    // particles: count the requested species, attributed to the sub-generator of their collision
    TTreeReader rp(tPart);
    TTreeReaderValue<int> pdgCode(rp, "fPdgCode");
    TTreeReaderValue<int> collIdx(rp, "fIndexMcCollisions");
    while (rp.Next()) {
      nPart++;
      if (std::abs(*pdgCode) == pdg) {
        nSel++;
        int idx = *collIdx;
        int sg = (idx >= 0 && idx < (int)subGen.size()) ? subGen[idx] : -99;
        nSelPerSubGen[sg]++;
      }
    }
  }
  printf("MC collisions          : %ld\n", nColl);
  printf("MC particles (stored)  : %ld\n", nPart);
  printf("|PDG| == %d          : %ld  (%.3f per MC collision)\n\n", pdg, nSel, nColl ? double(nSel) / nColl : 0.);
  printf("%16s %14s %14s %14s\n", "subGeneratorId", "collisions", Form("|PDG|=%d", pdg), "per collision");
  for (auto& [sg, n] : nCollPerSubGen) {
    long ns = nSelPerSubGen.count(sg) ? nSelPerSubGen[sg] : 0;
    printf("%16d %14ld %14ld %14.3f\n", sg, n, ns, n ? double(ns) / n : 0.);
  }
}
