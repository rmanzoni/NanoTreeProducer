import sys
import ROOT
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from TreeProducerEleTau import *
from CorrectionTools.ElectronSFs import *
from CorrectionTools.PileupWeightTool import *
from CorrectionTools.LeptonTauFakeSFs import *
from CorrectionTools.RecoilCorrectionTool import *
from CorrectionTools.BTaggingTool import BTagWeightTool, BTagWPs


class EleTauProducer(Module):
    
    def __init__(self, name, dataType, **kwargs):
        
        self.name           = name
        self.out            = TreeProducerEleTau(name)
        self.isData         = dataType=='data'
        self.year           = kwargs.get('year',     2017 )
        self.tes            = kwargs.get('tes',      1.0  )
        self.ltf            = kwargs.get('ltf',      1.0  )
        self.jtf            = kwargs.get('jtf',      1.0  )
        self.doZpt          = kwargs.get('doZpt',    'DY' in name )
        self.doRecoil       = kwargs.get('doRecoil', ('DY' in name or re.search(r"W\d?Jets",name)) and self.year>2016)
        self.doTTpt         = kwargs.get('doTTpt',   'TT' in name )
        self.doTight        = kwargs.get('doTight',  self.tes!=1 or self.ltf!=1 )
        self.channel        = 'eletau'
        year, channel       = self.year, self.channel
        
        self.vlooseIso      = getVLooseTauIso(year)
        if year==2016:
          self.trigger      = lambda e: e.HLT_Ele25_eta2p1_WPTight_Gsf or e.HLT_Ele27_WPTight_Gsf #or e.HLT_Ele45_WPLoose_Gsf_L1JetTauSeeded #or e.HLT_Ele24_eta2p1_WPLoose_Gsf_LooseIsoPFTau20_SingleL1 or e.HLT_Ele24_eta2p1_WPLoose_Gsf_LooseIsoPFTau20 or e.HLT_Ele24_eta2p1_WPLoose_Gsf_LooseIsoPFTau30
          self.eleCutPt     = 26
        elif year==2017:
          self.trigger      = lambda e: e.HLT_Ele35_WPTight_Gsf or e.HLT_Ele32_WPTight_Gsf_L1DoubleEG or e.HLT_Ele32_WPTight_Gsf
          self.eleCutPt     = 36
        else:
          self.trigger      = lambda e: e.HLT_Ele32_WPTight_Gsf or e.HLT_Ele35_WPTight_Gsf
          self.eleCutPt     = 33
        self.tauCutPt       = 20
        
        if not self.isData:
          self.eleSFs       = ElectronSFs(year=year)
          self.puTool       = PileupWeightTool(year=year)
          self.ltfSFs       = LeptonTauFakeSFs('loose','tight',year=year)
          self.btagTool     = BTagWeightTool('DeepCSV','medium',channel='mutau',year=year)
          if self.doZpt: 
            self.zptTool    = ZptCorrectionTool(year=year)
          if self.doRecoil:
            self.recoilTool = RecoilCorrectionTool(year=year)
        self.deepcsv_wp     = BTagWPs('DeepCSV',year=year)
        
        self.Nocut = 0
        self.Trigger = 1
        self.GoodElectrons = 2
        self.GoodTaus = 3
        self.GoodDiLepton = 4
        self.TotalWeighted = 15
        self.TotalWeighted_no0PU = 16
        
        self.out.cutflow.GetXaxis().SetBinLabel(1+self.Nocut,               "no cut"                 )
        self.out.cutflow.GetXaxis().SetBinLabel(1+self.Trigger,             "trigger"                )
        self.out.cutflow.GetXaxis().SetBinLabel(1+self.GoodElectrons,       "electron object"        )
        self.out.cutflow.GetXaxis().SetBinLabel(1+self.GoodTaus,            "tau object"             )
        self.out.cutflow.GetXaxis().SetBinLabel(1+self.GoodDiLepton,        "eletau pair"            )
        self.out.cutflow.GetXaxis().SetBinLabel(1+self.TotalWeighted,       "no cut, weighted"       )
        self.out.cutflow.GetXaxis().SetBinLabel(1+self.TotalWeighted_no0PU, "no cut, weighted, PU>0" )
        self.out.cutflow.GetXaxis().SetLabelSize(0.041)
        
    def beginJob(self):
        pass
        
    def endJob(self):
        if not self.isData:
          self.btagTool.setDirectory(self.out.outputfile,'btag')
        self.out.endJob()
        
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        sys.stdout.flush()
        checkBranches(inputTree)
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):        
        pass
        
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        sys.stdout.flush()
        
        #####################################
        self.out.cutflow.Fill(self.Nocut)
        if self.isData:
          self.out.cutflow.Fill(self.TotalWeighted, 1.)
          if event.PV_npvs>0:
            self.out.cutflow.Fill(self.TotalWeighted_no0PU, 1.)
          else:
            return False
        else:
          self.out.cutflow.Fill(self.TotalWeighted, event.genWeight)
          if event.Pileup_nTrueInt>0:
            self.out.cutflow.Fill(self.TotalWeighted_no0PU, event.genWeight)
          else:
            return False
        #####################################
        
        
        if not self.trigger(event):
            return False
        
        #####################################
        self.out.cutflow.Fill(self.Trigger)
        #####################################
        
        
        idx_goodelectrons = [ ]
        for ielectron in range(event.nElectron):
            if event.Electron_pt[ielectron] < self.eleCutPt: continue
            if abs(event.Electron_eta[ielectron]) > 2.1: continue
            if abs(event.Electron_dz[ielectron]) > 0.2: continue
            if abs(event.Electron_dxy[ielectron]) > 0.045: continue
            if event.Electron_convVeto[ielectron] !=1: continue
            if ord(event.Electron_lostHits[ielectron]) > 1: continue
            if event.Electron_mvaFall17V2Iso_WP80[ielectron] < 0.5: continue
            idx_goodelectrons.append(ielectron)
        
        if len(idx_goodelectrons)==0:
            return False
        
        #####################################
        self.out.cutflow.Fill(self.GoodElectrons)
        #####################################
        
        
        Tau_genmatch = { } # bug in Tau_genPartFlav
        idx_goodtaus = [ ]
        for itau in range(event.nTau):
            if not self.vlooseIso(event,itau): continue
            if abs(event.Tau_eta[itau]) > 2.3: continue
            if abs(event.Tau_dz[itau]) > 0.2: continue
            if event.Tau_decayMode[itau] not in [0,1,10]: continue
            if abs(event.Tau_charge[itau])!=1: continue
            if not self.isData:
              Tau_genmatch[itau] = genmatch(event,itau)
              #if self.tes!=1.0 and Tau_genmatch[itau]==5:
              #  event.Tau_pt[itau]   *= self.tes
              #  event.Tau_mass[itau] *= self.tes
              #elif self.ltf!=1.0 and 0<Tau_genmatch[itau]<5:
              #  event.Tau_pt[itau]   *= self.ltf
              #  event.Tau_mass[itau] *= self.ltf
              #elif self.jtf!=1.0 and Tau_genmatch[itau]==0:
              #  event.Tau_pt[itau]   *= self.jtf
              #  event.Tau_mass[itau] *= self.jtf
            if event.Tau_pt[itau] < self.tauCutPt: continue
            ###if ord(event.Tau_idAntiEle[itau])<1: continue
            ###if ord(event.Tau_idAntiMu[itau])<1: continue
            idx_goodtaus.append(itau)
        
        if len(idx_goodtaus)==0:
            return False
        
        #####################################
        self.out.cutflow.Fill(self.GoodTaus)
        #####################################
        
        
        electrons = Collection(event, 'Electron')
        taus  = Collection(event, 'Tau')
        ltaus = [ ]
        for idx1 in idx_goodelectrons:
            for idx2 in idx_goodtaus:
                dR = taus[idx2].p4().DeltaR(electrons[idx1].p4())
                if dR < 0.5: continue
                ltau = LeptonTauPair(idx1, event.Electron_pt[idx1], event.Electron_pfRelIso03_all[idx1],
                                     idx2, event.Tau_pt[idx2],      event.Tau_rawMVAoldDM2017v2[idx2])
                ltaus.append(ltau)
        
        if len(ltaus)==0:
            return False
        
        ltau     = bestDiLepton(ltaus)
        electron = electrons[ltau.id1].p4()
        tau      = taus[ltau.id2].p4()
        #print 'chosen tau1 (idx, pt) = ', ltau.id1, ltau.tau1_pt, 'check', electron.p4().Pt()
        #print 'chosen tau2 (idx, pt) = ', ltau.id2, ltau.tau2_pt, 'check', tau.p4().Pt()
        
        #####################################
        self.out.cutflow.Fill(self.GoodDiLepton)
        #####################################
        
        
        # VETOS
        self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = extraLeptonVetos(event, [-1], [ltau.id1], self.channel)
        self.out.lepton_vetos[0] = self.out.extramuon_veto[0] or self.out.extraelec_veto[0] or self.out.dilepton_veto[0]
        ###if self.doTight and (self.out.lepton_vetos[0] or event.Electron_pfRelIso03_all[ltau.id1]>0.10 or\
        ###                     ord(event.Tau_idAntiMu[ltau.id2]<1 or ord(event.Tau_idAntiEle[ltau.id2]<8):
        ###  return False
        
        
        # JETS
        jetIds  = [ ]
        bjetIds = [ ]
        jets    = Collection(event, 'Jet')
        nfjets  = 0
        ncjets  = 0
        nbtag   = 0
        for ijet in range(event.nJet):
            if event.Jet_pt[ijet] < 30: continue
            if abs(event.Jet_eta[ijet]) > 4.7: continue
            if electron.DeltaR(jets[ijet].p4()) < 0.5: continue
            if tau.DeltaR(jets[ijet].p4()) < 0.5: continue
            jetIds.append(ijet)
            
            if abs(event.Jet_eta[ijet]) > 2.4:
              nfjets += 1
            else:
              ncjets += 1
            
            if event.Jet_btagDeepB[ijet] > self.deepcsv_wp.medium:
              nbtag += 1
              bjetIds.append(ijet)
        
        if not self.isData and self.vlooseIso(event,ltau.id2) and event.Electron_pfRelIso03_all[ltau.id1]<0.50:
          self.btagTool.fillEfficiencies(event,jetIds)
        
        
        # EVENT
        self.out.isData[0]                     = self.isData
        self.out.run[0]                        = event.run
        self.out.lumi[0]                       = event.luminosityBlock
        self.out.event[0]                      = event.event & 0xffffffffffffffff
        ###self.out.puppimet[0]                  = event.PuppiMET_pt
        ###self.out.puppimetphi[0]               = event.PuppiMET_phi
        ###self.out.metsignificance[0]           = event.MET_significance
        ###self.out.metcovXX[0]                  = event.MET_covXX
        ###self.out.metcovXY[0]                  = event.MET_covXY
        ###self.out.metcovYY[0]                  = event.MET_covYY
        self.out.npvs[0]                       = event.PV_npvs
        self.out.npvsGood[0]                   = event.PV_npvsGood
        
        if not self.isData:
          self.out.genmet[0]                   = event.GenMET_pt
          self.out.genmetphi[0]                = event.GenMET_phi
          self.out.nPU[0]                      = event.Pileup_nPU
          self.out.nTrueInt[0]                 = event.Pileup_nTrueInt
          try:
            self.out.LHE_Njets[0]              = event.LHE_Njets
          except RuntimeError:
            self.out.LHE_Njets[0]              = -1
        
        
        # ELECTRON
        self.out.pt_1[0]                       = event.Electron_pt[ltau.id1]
        self.out.eta_1[0]                      = event.Electron_eta[ltau.id1]
        self.out.phi_1[0]                      = event.Electron_phi[ltau.id1]
        self.out.m_1[0]                        = event.Electron_mass[ltau.id1]
        self.out.dxy_1[0]                      = event.Electron_dxy[ltau.id1]
        self.out.dz_1[0]                       = event.Electron_dz[ltau.id1]         
        self.out.q_1[0]                        = event.Electron_charge[ltau.id1]
        self.out.pfRelIso03_all_1[0]           = event.Electron_pfRelIso03_all[ltau.id1]
        self.out.cutBased_1[0]                 = event.Electron_cutBased[ltau.id1]
        self.out.mvaFall17Iso_1[0]             = event.Electron_mvaFall17V2Iso[ltau.id1]
        self.out.mvaFall17Iso_WPL_1[0]         = event.Electron_mvaFall17V2Iso_WPL[ltau.id1]
        self.out.mvaFall17Iso_WP80_1[0]        = event.Electron_mvaFall17V2Iso_WP80[ltau.id1]
        self.out.mvaFall17Iso_WP90_1[0]        = event.Electron_mvaFall17V2Iso_WP90[ltau.id1]
        
        
        # TAU
        self.out.pt_2[0]                       = event.Tau_pt[ltau.id2]
        self.out.eta_2[0]                      = event.Tau_eta[ltau.id2]
        self.out.phi_2[0]                      = event.Tau_phi[ltau.id2]
        self.out.m_2[0]                        = event.Tau_mass[ltau.id2]
        self.out.dxy_2[0]                      = event.Tau_dxy[ltau.id2]
        self.out.dz_2[0]                       = event.Tau_dz[ltau.id2]         
        self.out.leadTkPtOverTauPt_2[0]        = event.Tau_leadTkPtOverTauPt[ltau.id2]
        self.out.chargedIso_2[0]               = event.Tau_chargedIso[ltau.id2]
        self.out.neutralIso_2[0]               = event.Tau_neutralIso[ltau.id2]
        self.out.photonsOutsideSignalCone_2[0] = event.Tau_photonsOutsideSignalCone[ltau.id2]
        self.out.puCorr_2[0]                   = event.Tau_puCorr[ltau.id2]
        self.out.rawAntiEle_2[0]               = event.Tau_rawAntiEle[ltau.id2]
        self.out.rawIso_2[0]                   = event.Tau_rawIso[ltau.id2]
        self.out.q_2[0]                        = event.Tau_charge[ltau.id2]
        self.out.decayMode_2[0]                = event.Tau_decayMode[ltau.id2]
        ###self.out.rawAntiEleCat_2[0]            = event.Tau_rawAntiEleCat[ltau.id2]
        self.out.idAntiEle_2[0]                = ord(event.Tau_idAntiEle[ltau.id2])
        self.out.idAntiMu_2[0]                 = ord(event.Tau_idAntiMu[ltau.id2])
        self.out.idDecayMode_2[0]              = event.Tau_idDecayMode[ltau.id2]
        self.out.idDecayModeNewDMs_2[0]        = event.Tau_idDecayModeNewDMs[ltau.id2]
        self.out.rawMVAoldDM_2[0]              = event.Tau_rawMVAoldDM[ltau.id2]
        self.out.rawMVAnewDM2017v2_2[0]        = event.Tau_rawMVAnewDM2017v2[ltau.id2]
        self.out.rawMVAoldDM2017v1_2[0]        = event.Tau_rawMVAoldDM2017v1[ltau.id2]
        self.out.rawMVAoldDM2017v2_2[0]        = event.Tau_rawMVAoldDM2017v2[ltau.id2]
        self.out.idMVAoldDM_2[0]               = ord(event.Tau_idMVAoldDM[ltau.id2])
        self.out.idMVAoldDM2017v1_2[0]         = ord(event.Tau_idMVAoldDM2017v1[ltau.id2])
        self.out.idMVAoldDM2017v2_2[0]         = ord(event.Tau_idMVAoldDM2017v2[ltau.id2])
        self.out.idMVAnewDM2017v2_2[0]         = ord(event.Tau_idMVAnewDM2017v2[ltau.id2])
        
        
        # GENERATOR      
        if not self.isData:
          self.out.genPartFlav_1[0]     = ord(event.Electron_genPartFlav[ltau.id1])
          self.out.genPartFlav_2[0]     = Tau_genmatch[ltau.id2] # ord(event.Tau_genPartFlav[ltau.id2])
          
          genvistau = Collection(event, 'GenVisTau')
          dRmax  = 1000
          gendm  = -1
          genpt  = -1
          geneta = -1
          genphi = -1
          for igvt in range(event.nGenVisTau):
            dR = genvistau[igvt].p4().DeltaR(tau)
            if dR < 0.5 and dR < dRmax:
              dRmax  = dR
              gendm  = event.GenVisTau_status[igvt]
              genpt  = event.GenVisTau_pt[igvt]
              geneta = event.GenVisTau_eta[igvt]
              genphi = event.GenVisTau_phi[igvt]
          
          self.out.gendecayMode_2[0] = gendm
          self.out.genvistaupt_2[0]  = genpt
          self.out.genvistaueta_2[0] = geneta
          self.out.genvistauphi_2[0] = genphi
        
        
        # WEIGHTS
        met = TLorentzVector()
        met.SetPxPyPzE(event.MET_pt*cos(event.MET_phi),event.MET_pt*sin(event.MET_phi),0,event.MET_pt)
        if not self.isData:
          if self.doRecoil:
            boson, boson_vis         = getBoson(event)
            self.recoilTool.CorrectPFMETByMeanResolution(met,boson,boson_vis,len(jetIds))
            event.MET_pt             = met.Pt()
            event.MET_phi            = met.Phi()
            self.out.m_genboson[0]   = boson.M()
            self.out.pt_genboson[0]  = boson.Pt()
            if self.doZpt:
              self.out.zptweight[0]  = self.zptTool.getZptWeight(boson.Pt(),boson.M())
          elif self.doZpt:
            zboson = getZBoson(event)
            self.out.m_genboson[0]   = zboson.M()
            self.out.pt_genboson[0]  = zboson.Pt()
            self.out.zptweight[0]    = self.zptTool.getZptWeight(zboson.Pt(),zboson.M())
          elif self.doTTpt:
            toppt1, toppt2           = getTTPt(event)
            self.out.ttptweight[0]   = getTTptWeight(toppt1,toppt2)
          self.out.genweight[0]      = event.genWeight
          self.out.puweight[0]       = self.puTool.getWeight(event.Pileup_nTrueInt)
          self.out.trigweight[0]     = self.eleSFs.getTriggerSF(self.out.pt_1[0], self.out.eta_1[0])
          self.out.idisoweight_1[0]  = self.eleSFs.getIdIsoSF(self.out.pt_1[0],self.out.eta_1[0])
          self.out.idisoweight_2[0]  = self.ltfSFs.getSF(self.out.genPartFlav_2[0],self.out.eta_2[0])
          self.out.btagweight[0]     = self.btagTool.getWeight(event,jetIds)
          self.out.weight[0]         = self.out.genweight[0]*self.out.puweight[0]*self.out.trigweight[0]*self.out.idisoweight_1[0]*self.out.idisoweight_2[0]
        
        
        # JETS
        self.out.njets[0]            = len(jetIds)
        self.out.njets50[0]          = len([j for j in jetIds if event.Jet_pt[j]>50])
        self.out.nfjets[0]           = nfjets
        self.out.ncjets[0]           = ncjets
        self.out.nbtag[0]            = nbtag
        
        if len(jetIds)>0:
          self.out.jpt_1[0]          = event.Jet_pt[jetIds[0]]
          self.out.jeta_1[0]         = event.Jet_eta[jetIds[0]]
          self.out.jphi_1[0]         = event.Jet_phi[jetIds[0]]
          self.out.jdeepb_1[0]       = event.Jet_btagDeepB[jetIds[0]]
        else:
          self.out.jpt_1[0]          = -9.
          self.out.jeta_1[0]         = -9.
          self.out.jphi_1[0]         = -9.
          self.out.jdeepb_1[0]       = -9.
        
        if len(jetIds)>1:
          self.out.jpt_2[0]          = event.Jet_pt[jetIds[1]]
          self.out.jeta_2[0]         = event.Jet_eta[jetIds[1]]
          self.out.jphi_2[0]         = event.Jet_phi[jetIds[1]]
          self.out.jdeepb_2[0]       = event.Jet_btagDeepB[jetIds[1]]
        else:
          self.out.jpt_2[0]          = -9.
          self.out.jeta_2[0]         = -9.
          self.out.jphi_2[0]         = -9.
          self.out.jdeepb_2[0]       = -9.
        
        if len(bjetIds)>0:
          self.out.bpt_1[0]          = event.Jet_pt[bjetIds[0]]
          self.out.beta_1[0]         = event.Jet_eta[bjetIds[0]]
        else:
          self.out.bpt_1[0]          = -9.
          self.out.beta_1[0]         = -9.
        
        if len(bjetIds)>1:
          self.out.bpt_2[0]          = event.Jet_pt[bjetIds[1]]
          self.out.beta_2[0]         = event.Jet_eta[bjetIds[1]]
        else:
          self.out.bpt_2[0]          = -9.
          self.out.beta_2[0]         = -9.
        
        self.out.met[0]              = event.MET_pt
        self.out.metphi[0]           = event.MET_phi
        self.out.pfmt_1[0]           = sqrt( 2 * self.out.pt_1[0] * self.out.met[0] * ( 1 - cos(deltaPhi(self.out.phi_1[0], self.out.metphi[0])) ) );
        self.out.pfmt_2[0]           = sqrt( 2 * self.out.pt_2[0] * self.out.met[0] * ( 1 - cos(deltaPhi(self.out.phi_2[0], self.out.metphi[0])) ) );
        
        self.out.m_vis[0]            = (electron + tau).M()
        self.out.pt_ll[0]            = (electron + tau).Pt()
        self.out.dR_ll[0]            = electron.DeltaR(tau)
        self.out.dphi_ll[0]          = deltaPhi(self.out.phi_1[0], self.out.phi_2[0])
        self.out.deta_ll[0]          = abs(self.out.eta_1[0] - self.out.eta_2[0])
        
        
        # PZETA
        leg1                         = TVector3(electron.Px(), electron.Py(), 0.)
        leg2                         = TVector3(tau.Px(), tau.Py(), 0.)
        zetaAxis                     = TVector3(leg1.Unit() + leg2.Unit()).Unit()
        pzeta_vis                    = leg1*zetaAxis + leg2*zetaAxis
        pzeta_miss                   = met.Vect()*zetaAxis
        self.out.pzetamiss[0]        = pzeta_miss
        self.out.pzetavis[0]         = pzeta_vis
        self.out.dzeta[0]            = pzeta_miss - 0.85*pzeta_vis
        
        
        self.out.tree.Fill()
        return True
        
