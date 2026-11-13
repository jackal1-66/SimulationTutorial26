// Overview of an o2sim kinematics file: PDG codes and production vertices.
// Usage: root -l -b -q 'kineOverview.C("o2sim_Kine.root","kine.svg")'
// (SVG: does not need the ASImage/libjpeg libraries that PNG output requires)
void kineOverview(const char* fname = "o2sim_Kine.root", const char* out = "kine.svg")
{
  TFile f(fname);
  auto t = (TTree*)f.Get("o2sim");
  if (!t) { printf("no o2sim tree in %s\n", fname); return; }
  printf("%s: %lld events\n", fname, t->GetEntries());
  gStyle->SetOptStat(1110);
  TCanvas c("c", "c", 1200, 500);
  c.Divide(2, 1);
  c.cd(1); gPad->SetLogy();
  t->Draw("MCTrack.mPdgCode>>hpdg(200,-3500,3500)", "", "");
  ((TH1*)gDirectory->Get("hpdg"))->SetTitle("PDG code of all MC tracks;PDG;entries");
  c.cd(2); gPad->SetLogy();
  t->Draw("MCTrack.mStartVertexCoordinatesY>>hvy(200,-300,300)", "", "");
  ((TH1*)gDirectory->Get("hvy"))->SetTitle("Production vertex y (primary+secondary);y (cm);entries");
  c.SaveAs(out);
}
