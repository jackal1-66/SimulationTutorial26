// Decay products of a given particle species found in an o2sim kinematics file,
// and number of such particles per event.
// Usage: root -l -b -q 'kineDaughters.C("o2sim_Kine.root",4122)'
#include <map>
void kineDaughters(const char* fname = "o2sim_Kine.root", int pdg = 4122)
{
  TFile f(fname);
  auto t = (TTree*)f.Get("o2sim");
  if (!t) { printf("no o2sim tree in %s\n", fname); return; }
  std::vector<o2::MCTrack>* tracks = nullptr;
  t->SetBranchAddress("MCTrack", &tracks);
  std::map<int, int> daughters;
  int nmothers = 0;
  for (int ev = 0; ev < t->GetEntries(); ++ev) {
    t->GetEntry(ev);
    int nInEvent = 0;
    for (auto& tr : *tracks) {
      if (tr.GetPdgCode() == pdg) {
        nInEvent++;
      }
      int m = tr.getMotherTrackId();
      if (m >= 0 && m < (int)tracks->size() && (*tracks)[m].GetPdgCode() == pdg) {
        daughters[tr.GetPdgCode()]++;
      }
    }
    nmothers += nInEvent;
    printf("event %d: %d particles with PDG %d (of %zu tracks)\n", ev, nInEvent, pdg, tracks->size());
  }
  printf("\nTotal PDG %d: %d\nDirect decay products:\n", pdg, nmothers);
  std::vector<std::pair<int, int>> v(daughters.begin(), daughters.end());
  std::sort(v.begin(), v.end(), [](auto& a, auto& b) { return a.second > b.second; });
  for (auto& [p, n] : v) {
    auto part = TDatabasePDG::Instance()->GetParticle(p);
    printf("  %8d %-12s %d\n", p, part ? part->GetName() : "?", n);
  }
}
